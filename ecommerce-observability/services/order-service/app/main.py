from fastapi import FastAPI
from app.database.database import Base, engine

from app.models.customer import Customer
from app.models.order import Order
from app.models.shipping_address import ShippingAddress
from app.models.billing_address import BillingAddress

#ROUTER
from app.routers.customer import router as customer_router
from app.routers.shipping_address import router as shipping_address_router
from app.routers.billing_address import router as billing_address_router
from app.routers.order import router as order_router


Base.metadata.create_all(bind=engine)
TITLE = "Order Service"
VERSION = "1.0.0"

app = FastAPI(title=TITLE,version=VERSION)


app.include_router(customer_router)
app.include_router(shipping_address_router)
app.include_router(billing_address_router)
app.include_router(order_router)

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