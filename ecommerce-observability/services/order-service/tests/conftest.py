import pytest

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.main import app
from app.database.database import SessionLocal, get_db

from app.models.customer import Customer
from app.models.shipping_address import ShippingAddress
from app.models.billing_address import BillingAddress
from app.models.order import Order
from app.models.order_item import OrderItem


@pytest.fixture
def db():
    db = SessionLocal()

    # Cleanup in dependency order
    db.execute(delete(OrderItem))
    db.execute(delete(Order))
    db.execute(delete(ShippingAddress))
    db.execute(delete(BillingAddress))
    db.execute(delete(Customer))
    db.commit()

    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client(db):
    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()