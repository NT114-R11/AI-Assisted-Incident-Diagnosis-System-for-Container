from fastapi import FastAPI

from app.database.database import Base, engine
from app.models.product import Product
from app.routers.products import router as product_router
from app.routers.seller import router as seller_router

Base.metadata.create_all(bind=engine)


app = FastAPI(
    title="Product Service",
    version="1.0.0"
)

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
    return {"status": "healthy" }