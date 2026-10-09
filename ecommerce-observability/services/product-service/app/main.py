import logging
import os
import re
import time
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from sqlalchemy import text

from app.database.database import Base, engine
from app.models.product import Product
from app.routers.products import router as product_router
from app.routers.seller import router as seller_router

logger = logging.getLogger("product-service")
request_count = Counter(
    "http_requests_total",
    "HTTP requests processed by the service.",
    ("service", "method", "handler", "status_code"),
)
request_duration = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds.",
    ("service", "method", "handler"),
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
probe_paths = {"/health", "/ready", "/metrics", "/openapi.json", "/docs", "/redoc"}
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
    title="Product Service",
    version=os.getenv("APP_VERSION", "1.0.0"),
    lifespan=lifespan,
)

@app.middleware("http")
async def observe_request(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", "")
    if not request_id_pattern.fullmatch(request_id):
        request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    started_at = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        response = JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "request_id": request_id},
        )

    response.headers["X-Request-ID"] = request_id
    if request.url.path not in probe_paths:
        route = request.scope.get("route")
        handler = getattr(route, "path", "unmatched")
        request_count.labels(
            "product-service", request.method, handler, str(response.status_code)
        ).inc()
        request_duration.labels("product-service", request.method, handler).observe(
            time.perf_counter() - started_at
        )
    return response


@app.get("/metrics", include_in_schema=False)
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

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