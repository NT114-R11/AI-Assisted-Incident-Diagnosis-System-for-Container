import os
import logging
import re
import time
import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import select, text

from app.database.database import Base, SessionLocal, engine
from app.models import User, Authority
from app.routers import auth, authority, user
from app.security import hash_password
from prometheus_fastapi_instrumentator import Instrumentator
TITLE = "User Service"
VERSION = os.getenv("APP_VERSION", "1.0.0")
request_id_pattern = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format=(
        '{"time":"%(asctime)s","level":"%(levelname)s",'
        '"service":"user-service","message":"%(message)s"}'
    ),
)
logger = logging.getLogger("user-service")


def create_bootstrap_admin():
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_pw = os.getenv("ADMIN_PASSWORD")

    if not admin_email or not admin_pw:
        logger.warning("Bootstrap admin skipped: ADMIN_EMAIL or ADMIN_PASSWORD is missing")
        return

    db = SessionLocal()
    try:
        user = db.get(User, admin_email)
        if not user:
            user = User(
                email=admin_email,
                password=hash_password(admin_pw),
                enable=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        admin_authority = db.scalars(
            select(Authority).where(
                Authority.email == admin_email,
                Authority.authority == "ADMIN"
            )
        ).first()

        if not admin_authority:
            db.add(Authority(
                email=admin_email,
                authority="ADMIN"
            ))
            db.commit()
    except Exception:
        db.rollback()
        logger.exception("Bootstrap admin failed")
    finally:
        db.close()


def init_db(max_retries: int = 10, delay: float = 3.0) -> None:
    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized")
            return
        except Exception:
            logger.exception("DB init failed (%s/%s)", attempt, max_retries)
            if attempt == max_retries:
                raise
            time.sleep(delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    create_bootstrap_admin()
    yield
    engine.dispose()


app = FastAPI(
    title=TITLE,
    version=VERSION,
    lifespan=lifespan
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", "")
    if not request_id_pattern.fullmatch(request_id):
        request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_id=%s %s %s failed",
            request_id,
            request.method,
            request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )

    response.headers["X-Request-ID"] = request_id
    if request.url.path not in ("/health", "/ready", "/metrics"):
        logger.info(
            "request_id=%s %s %s status=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
        )
    return response


Instrumentator().instrument(app).expose(app, include_in_schema=False)

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(authority.router)


@app.get("/")
def root():
    return {
        "service": "User service", 
        "status": "running"}

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "user-service"
    }

@app.get("/ready")
def ready():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("Database readiness check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": "user-service",
                "database": "down",
            },
        )
    return {
        "status": "ready",
        "service": "user-service",
        "database": "up",
    }