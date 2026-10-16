import uuid
from decimal import Decimal

from app.models.customer import Customer
from app.models.shipping_address import ShippingAddress
from app.models.billing_address import BillingAddress
from app.models.order import Order
from app.models.order_item import OrderItem


class FakeResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data


class FakeAsyncClient:
    def __init__(
        self,
        cart_response=None,
        stock_responses=None,
        delete_response=None,
    ):
        self.cart_response = cart_response
        self.stock_responses = stock_responses or {}
        self.delete_response = delete_response or FakeResponse(200)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        pass

    async def get(self, url):
        if "/carts/" in url:
            return self.cart_response

        return FakeResponse(200)

    async def patch(self, url, json=None):
        product_id = url.split("/products/")[1].split("/")[0]

        return self.stock_responses.get(
            product_id,
            FakeResponse(
                200,
                {
                    "product_id": product_id,
                    "price": "50.00",
                    "remaining_quantity": 10,
                },
            ),
        )

    async def delete(self, url):
        return self.delete_response


def create_customer(db):
    customer = Customer(
        name="John Doe",
        email="john@example.com",
        phone="0123456789",
    )

    db.add(customer)
    db.commit()
    db.refresh(customer)

    return customer


def create_addresses(db, customer):
    shipping = ShippingAddress(
        customer_id=customer.customer_id,
        address="123 Nguyen Hue",
        city="HCM",
    )

    billing = BillingAddress(
        customer_id=customer.customer_id,
        address="456 Le Loi",
        city="HCM",
    )

    db.add_all([shipping, billing])
    db.commit()

    db.refresh(shipping)
    db.refresh(billing)

    return shipping, billing


def test_create_order(client, db, monkeypatch):
    customer = create_customer(db)
    shipping, billing = create_addresses(db, customer)

    product_id = str(uuid.uuid4())
    cart_id = uuid.uuid4()

    cart_response = FakeResponse(
        200,
        {
            "cart_id": str(cart_id),
            "customer_id": str(customer.customer_id),
            "total_price": "100.00",
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                    "price": "50.00",
                }
            ],
        },
    )

    stock_response = FakeResponse(
        200,
        {
            "product_id": product_id,
            "price": "50.00",
            "remaining_quantity": 8,
        },
    )

    fake_client = FakeAsyncClient(
        cart_response=cart_response,
        stock_responses={
            product_id: stock_response,
        },
    )

    monkeypatch.setattr(
        "app.routers.order.httpx.AsyncClient",
        lambda timeout=5.0: fake_client,
    )

    response = client.post(
        "/orders/",
        json={
            "customer_id": str(customer.customer_id),
            "cart_id": str(cart_id),
            "shipping_address_id": str(shipping.id),
            "billing_address_id": str(billing.id),
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == str(customer.customer_id)
    assert data["cart_id"] == str(cart_id)
    assert data["status"] == "PENDING"

    assert Decimal(data["total_price"]) == Decimal("100.00")

    assert len(data["items"]) == 1

    item = data["items"][0]

    assert item["product_id"] == product_id
    assert item["quantity"] == 2
    assert Decimal(item["price"]) == Decimal("50.00")


def test_create_order_customer_not_found(client, db):
    shipping_id = uuid.uuid4()
    billing_id = uuid.uuid4()

    response = client.post(
        "/orders/",
        json={
            "customer_id": str(uuid.uuid4()),
            "cart_id": str(uuid.uuid4()),
            "shipping_address_id": str(shipping_id),
            "billing_address_id": str(billing_id),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found!"


def test_create_order_invalid_shipping_address(client, db):
    customer = create_customer(db)

    billing = BillingAddress(
        customer_id=customer.customer_id,
        address="456 Le Loi",
        city="HCM",
    )

    db.add(billing)
    db.commit()
    db.refresh(billing)

    response = client.post(
        "/orders/",
        json={
            "customer_id": str(customer.customer_id),
            "cart_id": str(uuid.uuid4()),
            "shipping_address_id": str(uuid.uuid4()),
            "billing_address_id": str(billing.id),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid shipping address"


def test_create_order_shipping_address_belongs_to_other_customer(client, db):
    customer1 = create_customer(db)

    customer2 = Customer(
        name="Jane",
        email="jane@example.com",
    )

    db.add(customer2)
    db.commit()
    db.refresh(customer2)

    shipping, billing = create_addresses(db, customer2)

    response = client.post(
        "/orders/",
        json={
            "customer_id": str(customer1.customer_id),
            "cart_id": str(uuid.uuid4()),
            "shipping_address_id": str(shipping.id),
            "billing_address_id": str(billing.id),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid shipping address"


def test_create_order_invalid_billing_address(client, db):
    customer = create_customer(db)

    shipping = ShippingAddress(
        customer_id=customer.customer_id,
        address="123 Nguyen Hue",
        city="HCM",
    )

    db.add(shipping)
    db.commit()
    db.refresh(shipping)

    response = client.post(
        "/orders/",
        json={
            "customer_id": str(customer.customer_id),
            "cart_id": str(uuid.uuid4()),
            "shipping_address_id": str(shipping.id),
            "billing_address_id": str(uuid.uuid4()),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid billing address"


def test_create_order_cart_not_found(client, db, monkeypatch):
    customer = create_customer(db)
    shipping, billing = create_addresses(db, customer)

    fake_client = FakeAsyncClient(
        cart_response=FakeResponse(404)
    )

    monkeypatch.setattr(
        "app.routers.order.httpx.AsyncClient",
        lambda timeout=5.0: fake_client,
    )

    response = client.post(
        "/orders/",
        json={
            "customer_id": str(customer.customer_id),
            "cart_id": str(uuid.uuid4()),
            "shipping_address_id": str(shipping.id),
            "billing_address_id": str(billing.id),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart not found"


def test_create_order_cart_service_error(client, db, monkeypatch):
    customer = create_customer(db)
    shipping, billing = create_addresses(db, customer)

    fake_client = FakeAsyncClient(
        cart_response=FakeResponse(500)
    )

    monkeypatch.setattr(
        "app.routers.order.httpx.AsyncClient",
        lambda timeout=5.0: fake_client,
    )

    response = client.post(
        "/orders/",
        json={
            "customer_id": str(customer.customer_id),
            "cart_id": str(uuid.uuid4()),
            "shipping_address_id": str(shipping.id),
            "billing_address_id": str(billing.id),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Cart-Service error"


def test_create_order_empty_cart(client, db, monkeypatch):
    customer = create_customer(db)
    shipping, billing = create_addresses(db, customer)

    fake_client = FakeAsyncClient(
        cart_response=FakeResponse(
            200,
            {
                "items": [],
            },
        )
    )

    monkeypatch.setattr(
        "app.routers.order.httpx.AsyncClient",
        lambda timeout=5.0: fake_client,
    )

    response = client.post(
        "/orders/",
        json={
            "customer_id": str(customer.customer_id),
            "cart_id": str(uuid.uuid4()),
            "shipping_address_id": str(shipping.id),
            "billing_address_id": str(billing.id),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == \
        "Cart is empty. Cannot place order."


def test_create_order_product_service_error(
    client,
    db,
    monkeypatch,
):
    customer = create_customer(db)
    shipping, billing = create_addresses(db, customer)

    product_id = str(uuid.uuid4())

    cart_response = FakeResponse(
        200,
        {
            "items": [
                {
                    "product_id": product_id,
                    "quantity": 2,
                    "price": "50.00",
                }
            ]
        },
    )

    stock_response = FakeResponse(
        400,
        {
            "detail": "Not enough product quantity"
        },
    )

    fake_client = FakeAsyncClient(
        cart_response=cart_response,
        stock_responses={
            product_id: stock_response
        },
    )

    monkeypatch.setattr(
        "app.routers.order.httpx.AsyncClient",
        lambda timeout=5.0: fake_client,
    )

    response = client.post(
        "/orders/",
        json={
            "customer_id": str(customer.customer_id),
            "cart_id": str(uuid.uuid4()),
            "shipping_address_id": str(shipping.id),
            "billing_address_id": str(billing.id),
        },
    )

    assert response.status_code == 400
    assert "Failed to deduct stock" in response.json()["detail"]


def test_get_orders(client, db):
    customer = create_customer(db)
    shipping, billing = create_addresses(db, customer)

    order = Order(
        customer_id=customer.customer_id,
        cart_id=uuid.uuid4(),
        shipping_address_id=shipping.id,
        billing_address_id=billing.id,
        total_price=Decimal("100.00"),
        status="PENDING",
    )

    order.items.append(
        OrderItem(
            product_id=uuid.uuid4(),
            quantity=2,
            price=Decimal("50.00"),
        )
    )

    db.add(order)
    db.commit()

    response = client.get("/orders/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert len(data[0]["items"]) == 1


def test_get_order(client, db):
    customer = create_customer(db)
    shipping, billing = create_addresses(db, customer)

    order = Order(
        customer_id=customer.customer_id,
        cart_id=uuid.uuid4(),
        shipping_address_id=shipping.id,
        billing_address_id=billing.id,
        total_price=Decimal("50.00"),
        status="PENDING",
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    response = client.get(
        f"/orders/{order.order_number}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["order_number"] == str(order.order_number)
    assert data["status"] == "PENDING"


def test_get_order_not_found(client):
    response = client.get(
        f"/orders/{uuid.uuid4()}"
    )

    assert response.status_code == 404


def test_update_order(client, db):
    customer = create_customer(db)
    shipping, billing = create_addresses(db, customer)

    order = Order(
        customer_id=customer.customer_id,
        cart_id=uuid.uuid4(),
        shipping_address_id=shipping.id,
        billing_address_id=billing.id,
        total_price=Decimal("100.00"),
        status="PENDING",
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    response = client.put(
        f"/orders/{order.order_number}",
        json={
            "status": "PROCESSING",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "PROCESSING"


def test_update_order_not_found(client):
    response = client.put(
        f"/orders/{uuid.uuid4()}",
        json={
            "status": "PROCESSING",
        },
    )

    assert response.status_code == 404


def test_cancel_order(client, db, monkeypatch):
    customer = create_customer(db)
    shipping, billing = create_addresses(db, customer)

    product_id = uuid.uuid4()

    order = Order(
        customer_id=customer.customer_id,
        cart_id=uuid.uuid4(),
        shipping_address_id=shipping.id,
        billing_address_id=billing.id,
        total_price=Decimal("100.00"),
        status="PENDING",
    )

    order.items.append(
        OrderItem(
            product_id=product_id,
            quantity=2,
            price=Decimal("50.00"),
        )
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    fake_client = FakeAsyncClient()

    monkeypatch.setattr(
        "app.routers.order.httpx.AsyncClient",
        lambda timeout=5.0: fake_client,
    )

    response = client.put(
        f"/orders/{order.order_number}/cancel"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "CANCELLED"


def test_cancel_order_not_found(client):
    response = client.put(
        f"/orders/{uuid.uuid4()}/cancel"
    )

    assert response.status_code == 404


def test_cancel_order_already_cancelled(client, db):
    customer = create_customer(db)
    shipping, billing = create_addresses(db, customer)

    order = Order(
        customer_id=customer.customer_id,
        cart_id=uuid.uuid4(),
        shipping_address_id=shipping.id,
        billing_address_id=billing.id,
        total_price=Decimal("50.00"),
        status="CANCELLED",
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    response = client.put(
        f"/orders/{order.order_number}/cancel"
    )

    assert response.status_code == 400

    assert response.json()["detail"] == \
        "Order is already cancelled"


def test_delete_order(client, db):
    customer = create_customer(db)
    shipping, billing = create_addresses(db, customer)

    order = Order(
        customer_id=customer.customer_id,
        cart_id=uuid.uuid4(),
        shipping_address_id=shipping.id,
        billing_address_id=billing.id,
        total_price=Decimal("50.00"),
        status="PENDING",
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    order_number = order.order_number

    response = client.delete(
        f"/orders/{order_number}"
    )

    assert response.status_code == 200

    assert response.json() == {
        "message": "Order was deleted successfully"
    }

    assert db.get(Order, order_number) is None


def test_delete_order_cascade_items(client, db):
    customer = create_customer(db)
    shipping, billing = create_addresses(db, customer)

    order = Order(
        customer_id=customer.customer_id,
        cart_id=uuid.uuid4(),
        shipping_address_id=shipping.id,
        billing_address_id=billing.id,
        total_price=Decimal("100.00"),
        status="PENDING",
    )

    item = OrderItem(
        product_id=uuid.uuid4(),
        quantity=2,
        price=Decimal("50.00"),
    )

    order.items.append(item)

    db.add(order)
    db.commit()

    item_id = item.id
    order_number = order.order_number

    response = client.delete(
        f"/orders/{order_number}"
    )

    assert response.status_code == 200

    assert db.get(Order, order_number) is None
    assert db.get(OrderItem, item_id) is None