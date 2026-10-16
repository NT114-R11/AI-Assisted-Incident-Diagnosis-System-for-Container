import uuid
import pytest

from app.models.customer import Customer
from app.models.shipping_address import ShippingAddress


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


def test_create_shipping_address(client, customer):
    response = client.post(
        f"/shipping-addresses/customers/{customer.customer_id}",
        json={
            "address": "123 Nguyen Hue",
            "city": "Ho Chi Minh City",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["customer_id"] == str(customer.customer_id)
    assert data["address"] == "123 Nguyen Hue"
    assert data["city"] == "Ho Chi Minh City"


def test_create_shipping_address_customer_not_found(client):
    response = client.post(
        f"/shipping-addresses/customers/{uuid.uuid4()}",
        json={
            "address": "123 Nguyen Hue",
            "city": "Ho Chi Minh City",
        },
    )

    assert response.status_code == 404


def test_get_customer_shipping_addresses(client, customer, db):
    db.add_all([
        ShippingAddress(
            customer_id=customer.customer_id,
            address="Address 1",
            city="HCM",
        ),
        ShippingAddress(
            customer_id=customer.customer_id,
            address="Address 2",
            city="Hanoi",
        ),
    ])

    db.commit()

    response = client.get(
        f"/shipping-addresses/customers/{customer.customer_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 2


def test_get_customer_shipping_addresses_not_found(client):
    response = client.get(
        f"/shipping-addresses/customers/{uuid.uuid4()}"
    )

    assert response.status_code == 404


def test_get_shipping_address(client, customer, db):
    address = ShippingAddress(
        customer_id=customer.customer_id,
        address="123 Nguyen Hue",
        city="HCM",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    response = client.get(
        f"/shipping-addresses/{address.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["address"] == "123 Nguyen Hue"


def test_get_shipping_address_not_found(client):
    response = client.get(
        f"/shipping-addresses/{uuid.uuid4()}"
    )

    assert response.status_code == 404


def test_update_shipping_address(client, customer, db):
    address = ShippingAddress(
        customer_id=customer.customer_id,
        address="Old Address",
        city="HCM",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    response = client.put(
        f"/shipping-addresses/{address.id}",
        json={
            "address": "New Address",
            "city": "Hanoi",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["address"] == "New Address"
    assert data["city"] == "Hanoi"


def test_update_shipping_address_not_found(client):
    response = client.put(
        f"/shipping-addresses/{uuid.uuid4()}",
        json={
            "address": "New Address",
        },
    )

    assert response.status_code == 404


def test_delete_shipping_address(client, customer, db):
    address = ShippingAddress(
        customer_id=customer.customer_id,
        address="123 Nguyen Hue",
        city="HCM",
    )

    db.add(address)
    db.commit()
    db.refresh(address)

    address_id = address.id

    response = client.delete(
        f"/shipping-addresses/{address_id}"
    )

    assert response.status_code == 200

    assert db.get(ShippingAddress, address_id) is None


def test_delete_shipping_address_not_found(client):
    response = client.delete(
        f"/shipping-addresses/{uuid.uuid4()}"
    )

    assert response.status_code == 404