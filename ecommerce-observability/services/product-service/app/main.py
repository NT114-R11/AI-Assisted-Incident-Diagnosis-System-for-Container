import logging
import os
import re
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.database.database import Base, engine
from app.models.product import Product
from app.routers.products import router as product_router
from app.routers.seller import router as seller_router

TITLE = "Product Service"
VERSION = os.getenv("APP_VERSION", "1.0.0")
logger = logging.getLogger("product-service")
request_id_pattern = re.compile(r"[A-Za-z0-9._:-]{1,128}\Z")


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
    yield
    engine.dispose()


app = FastAPI(
    title=TITLE,
    version=VERSION,
    lifespan=lifespan,
)


@app.middleware("http")
async def observe_request(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", "")
    if not request_id_pattern.fullmatch(request_id):
        request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    try:
        response = await call_next(request)
    except Exception:
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )

    response.headers["X-Request-ID"] = request_id
    return response


Instrumentator().instrument(app).expose(app, include_in_schema=False)

app.include_router(product_router)
app.include_router(seller_router)

@app.get("/")
def root():
    return {
        "service" : "product-service",
        "status" : "running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service" : "product-service", 
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
                "service": "product-service",
                "database": "down",
            },
        )
    return {
        "status": "ready",
        "service": "product-service",
        "database": "up",
    }