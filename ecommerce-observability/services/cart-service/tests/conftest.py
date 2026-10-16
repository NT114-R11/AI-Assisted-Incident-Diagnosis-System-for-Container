import pytest

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.main import app
from app.database.database import SessionLocal, get_db
from app.models.cart import Cart
from app.models.cart_item import CartItem


@pytest.fixture
def db():
    db = SessionLocal()

    db.execute(delete(CartItem))
    db.execute(delete(Cart))
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
