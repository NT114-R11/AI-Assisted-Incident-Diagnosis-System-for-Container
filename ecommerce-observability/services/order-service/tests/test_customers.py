import uuid

import pytest

from app.models.customer import Customer


class FakeResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data


class FakeAsyncClient:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url):
        return self.response


def test_create_customer(client, monkeypatch):
    fake_response = FakeResponse(
        200,
        {"email": "customer@example.com"},
    )

    monkeypatch.setattr(
        "app.routers.customer.httpx.AsyncClient",
        lambda: FakeAsyncClient(fake_response),
    )

    response = client.post(
        "/customers/",
        json={
            "name": "John Doe",
            "email": "customer@example.com",
            "phone": "0123456789",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "John Doe"
    assert data["email"] == "customer@example.com"
    assert data["phone"] == "0123456789"
    assert "customer_id" in data


def test_create_customer_user_not_found(client, monkeypatch):
    fake_response = FakeResponse(404)

    monkeypatch.setattr(
        "app.routers.customer.httpx.AsyncClient",
        lambda: FakeAsyncClient(fake_response),
    )

    response = client.post(
        "/customers/",
        json={
            "name": "John Doe",
            "email": "missing@example.com",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == \
        "User email does not exist in user-service"


def test_create_customer_user_service_error(client, monkeypatch):
    fake_response = FakeResponse(500)

    monkeypatch.setattr(
        "app.routers.customer.httpx.AsyncClient",
        lambda: FakeAsyncClient(fake_response),
    )

    response = client.post(
        "/customers/",
        json={
            "name": "John Doe",
            "email": "customer@example.com",
        },
    )

    assert response.status_code == 503


def test_create_customer_duplicate(client, monkeypatch, db):
    fake_response = FakeResponse(200)

    monkeypatch.setattr(
        "app.routers.customer.httpx.AsyncClient",
        lambda: FakeAsyncClient(fake_response),
    )

    existing = Customer(
        name="Existing",
        email="customer@example.com",
    )

    db.add(existing)
    db.commit()

    response = client.post(
        "/customers/",
        json={
            "name": "John Doe",
            "email": "customer@example.com",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Email is already exists"


def test_get_customers(client, db):
    customer1 = Customer(
        name="John",
        email="john@example.com",
    )

    customer2 = Customer(
        name="Jane",
        email="jane@example.com",
    )

    db.add_all([customer1, customer2])
    db.commit()

    response = client.get("/customers/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


def test_get_customer(client, db):
    customer = Customer(
        name="John",
        email="john@example.com",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    response = client.get(
        f"/customers/{customer.customer_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == str(customer.customer_id)
    assert data["name"] == "John"


def test_get_customer_not_found(client):
    customer_id = uuid.uuid4()

    response = client.get(
        f"/customers/{customer_id}"
    )

    assert response.status_code == 404


def test_update_customer(client, db):
    customer = Customer(
        name="John",
        email="john@example.com",
        phone="111",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    response = client.put(
        f"/customers/{customer.customer_id}",
        json={
            "name": "John Updated",
            "phone": "999",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "John Updated"
    assert data["phone"] == "999"


def test_update_customer_duplicate_email(client, db):
    customer1 = Customer(
        name="John",
        email="john@example.com",
    )

    customer2 = Customer(
        name="Jane",
        email="jane@example.com",
    )

    db.add_all([customer1, customer2])
    db.commit()
    db.refresh(customer1)

    response = client.put(
        f"/customers/{customer1.customer_id}",
        json={
            "email": "jane@example.com",
        },
    )

    assert response.status_code == 409


def test_update_customer_not_found(client):
    response = client.put(
        f"/customers/{uuid.uuid4()}",
        json={"name": "Updated"},
    )

    assert response.status_code == 404


def test_delete_customer(client, db):
    customer = Customer(
        name="John",
        email="john@example.com",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    customer_id = customer.customer_id

    response = client.delete(
        f"/customers/{customer_id}"
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Customer deleted successfully"
    }

    assert db.get(Customer, customer_id) is None


def test_delete_customer_not_found(client):
    response = client.delete(
        f"/customers/{uuid.uuid4()}"
    )

    assert response.status_code == 404