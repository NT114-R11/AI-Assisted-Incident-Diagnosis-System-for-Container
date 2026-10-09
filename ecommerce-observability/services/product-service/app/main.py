from fastapi import FastAPI

from app.database.database import Base, engine
from app.models.product import Product
from app.routers.products import router as product_router
from app.routers.seller import router as seller_router
from prometheus_fastapi_instrumentator import Instrumentator
Base.metadata.create_all(bind=engine)

TITLE = "Product Service"
VERSION = "1.0.0"

app = FastAPI(title=TITLE,version=VERSION)

Instrumentator().instrument(app=app).expose(app)
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