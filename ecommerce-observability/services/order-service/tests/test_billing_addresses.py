import uuid

import pytest

from app.models.customer import Customer
from app.models.billing_address import BillingAddress


@pytest.fixture
def customer(db):
    customer = Customer(
        name="John Doe",
        email="john@example.com",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def test_create_billing_address(client, customer):
    response = client.post(
        f"/billing-addresses/customers/{customer.customer_id}",
        json={
            "address": "456 Le Loi",
            "city": "Ho Chi Minh City",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == str(customer.customer_id)
    assert data["address"] == "456 Le Loi"
    assert data["city"] == "Ho Chi Minh City"


def test_create_billing_address_customer_not_found(client):
    response = client.post(
        f"/billing-addresses/customers/{uuid.uuid4()}",
        json={
            "address": "456 Le Loi",
            "city": "Ho Chi Minh City",
        },
    )

    assert response.status_code == 404


def test_get_customer_billing_addresses(client, customer, db):
    db.add_all([
        BillingAddress(
            customer_id=customer.customer_id,
            address="Address 1",
            city="HCM",
        ),
        BillingAddress(
            customer_id=customer.customer_id,
            address="Address 2",
            city="Hanoi",
        ),
    ])

    db.commit()

    response = client.get(
        f"/billing-addresses/customers/{customer.customer_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


def test_get_customer_billing_addresses_not_found(client):
    response = client.get(
        f"/billing-addresses/customers/{uuid.uuid4()}"
    )

    assert response.status_code == 404


def test_get_billing_address(client, customer, db):
    address = BillingAddress(
        customer_id=customer.customer_id,
        address="456 Le Loi",
        city="HCM",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    response = client.get(
        f"/billing-addresses/{address.id}"
    )

    assert response.status_code == 200

    assert response.json()["address"] == "456 Le Loi"


def test_get_billing_address_not_found(client):
    response = client.get(
        f"/billing-addresses/{uuid.uuid4()}"
    )

    assert response.status_code == 404


def test_update_billing_address(client, customer, db):
    address = BillingAddress(
        customer_id=customer.customer_id,
        address="Old Address",
        city="HCM",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    response = client.put(
        f"/billing-addresses/{address.id}",
        json={
            "address": "New Address",
            "city": "Hanoi",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["address"] == "New Address"
    assert data["city"] == "Hanoi"


def test_update_billing_address_not_found(client):
    response = client.put(
        f"/billing-addresses/{uuid.uuid4()}",
        json={
            "address": "New Address",
        },
    )

    assert response.status_code == 404


def test_delete_billing_address(client, customer, db):
    address = BillingAddress(
        customer_id=customer.customer_id,
        address="456 Le Loi",
        city="HCM",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    address_id = address.id

    response = client.delete(
        f"/billing-addresses/{address_id}"
    )

    assert response.status_code == 200

    assert db.get(BillingAddress, address_id) is None


def test_delete_billing_address_not_found(client):
    response = client.delete(
        f"/billing-addresses/{uuid.uuid4()}"
    )

    assert response.status_code == 404