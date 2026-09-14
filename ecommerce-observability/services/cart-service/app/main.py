from fastapi import FastAPI
from app.database.database import Base,engine
from app.models import Cart, CartItem
from app.routers.cart import router as cart_router

Base.metadata.create_all(bind=engine)

TITLE = "Cart Service"
VERSION = "1.0.0"

app = FastAPI(title=TITLE, version=VERSION)

app.include_router(cart_router)

@app.get("/")
def root():
    return {
        "service": "cart-service",
        "status": "running"
    }
@app.get("/health")
def health():
    return {
        "status": "healthy"
    }