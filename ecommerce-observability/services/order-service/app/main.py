from fastapi import FastAPI
from app.database.database import Base, engine

from app.models.customer import Customer
from app.models.order import Order
from app.models.shipping_address import ShippingAddress
from app.models.billing_address import BillingAddress

Base.metadata.create_all(bind=engine)
TITLE = "Order Service"
VERSION = "1.0.0"

app = FastAPI(title=TITLE,version=VERSION)


@app.get("/")
def root():
    return {
        "service": "order-service",
        "status": "running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }