import logging
import os
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.database.database import Base, engine

from app.models.customer import Customer  # noqa: F401
from app.models.order import Order  # noqa: F401
from app.models.shipping_address import ShippingAddress  # noqa: F401
from app.models.billing_address import BillingAddress  # noqa: F401

from app.routers.customer import router as customer_router
from app.routers.shipping_address import router as shipping_address_router
from app.routers.billing_address import router as billing_address_router
from app.routers.order import router as order_router


SERVICE_NAME = "order-service"
TITLE = "Order Service"
VERSION = os.getenv("APP_VERSION", "1.0.0")

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format=(
        '{"time":"%(asctime)s","level":"%(levelname)s",'
        '"service":"' + SERVICE_NAME + '","message":"%(message)s"}'
    ),
)
logger = logging.getLogger(SERVICE_NAME)


def init_db(max_retries: int = 10, delay: float = 3.0) -> None:
    for attempt in range(1, max_retries + 1):
        try:
            Base.metadata.create_all(bind=engine)
            logger.info("Database initialized")
            return
        except Exception as exc:
            logger.warning("DB init failed (%s/%s): %s", attempt, max_retries, exc)
            if attempt == max_retries:
                raise
            time.sleep(delay)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting %s v%s", SERVICE_NAME, VERSION)
    init_db()
    yield
    logger.info("Shutting down %s", SERVICE_NAME)
    engine.dispose()


app = FastAPI(title=TITLE, version=VERSION, lifespan=lifespan)
Instrumentator().instrument(app).expose(app, include_in_schema=False)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception(
            "request_id=%s %s %s failed",
            request_id, request.method, request.url.path,
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )

    duration_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id

    if request.url.path not in ("/health", "/metrics"):
        logger.info(
            "request_id=%s %s %s status=%s duration_ms=%.1f",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )

    return response


app.include_router(customer_router)
app.include_router(shipping_address_router)
app.include_router(billing_address_router)
app.include_router(order_router)


@app.get("/")
def root():
    return {
        "service": SERVICE_NAME,
        "version": VERSION,
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": SERVICE_NAME
    }


@app.get("/ready")
def ready():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        logger.error("Readiness check failed: %s", exc)
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "service": SERVICE_NAME,
                "database": "down"
            },
        )

    return {
        "status": "ready",
        "service": SERVICE_NAME,
        "database": "up"
    }