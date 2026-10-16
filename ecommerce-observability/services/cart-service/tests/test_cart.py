import uuid
from decimal import Decimal

import httpx

from app.models.cart import Cart
from app.models.cart_item import CartItem



class FakeResponse:
    def __init__(self, status_code, data=None):
        self.status_code = status_code
        self._data = data or {}

    def json(self):
        return self._data


class FakeAsyncClient:
    def __init__(self, status_code=200):
        self.status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def get(self, *args, **kwargs):
        return FakeResponse(self.status_code)


def fake_product_response(
    quantity=100,
    price=50.00,
):
    return FakeResponse(
        status_code=200,
        data={
            "product_id": str(uuid.uuid4()),
            "product_name": "Test Product",
            "quantity": quantity,
            "description": "Test product",
            "manufacturer": "Test Manufacturer",
            "categories": "Test",
            "price": price,
            "seller_id": str(uuid.uuid4()),
        },
    )



def test_create_cart(client, db, monkeypatch):
    customer_id = uuid.uuid4()

    monkeypatch.setattr(
        "app.routers.cart.httpx.AsyncClient",
        lambda: FakeAsyncClient(status_code=200),
    )

    response = client.post(
        "/carts/",
        json={
            "customer_id": str(customer_id),
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["customer_id"] == str(customer_id)
    assert data["total_price"] == "0.00"
    assert data["items"] == []
    assert "cart_id" in data


def test_create_cart_customer_not_found(client, monkeypatch):
    customer_id = uuid.uuid4()

    monkeypatch.setattr(
        "app.routers.cart.httpx.AsyncClient",
        lambda: FakeAsyncClient(status_code=404),
    )

    response = client.post(
        "/carts/",
        json={
            "customer_id": str(customer_id),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Customer not found"


def test_create_cart_order_service_error(client, monkeypatch):
    customer_id = uuid.uuid4()

    monkeypatch.setattr(
        "app.routers.cart.httpx.AsyncClient",
        lambda: FakeAsyncClient(status_code=500),
    )

    response = client.post(
        "/carts/",
        json={
            "customer_id": str(customer_id),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Order-Service error"


def test_create_cart_order_service_unavailable(client, monkeypatch):
    customer_id = uuid.uuid4()

    class FailingAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            pass

        async def get(self, *args, **kwargs):
            raise httpx.RequestError("Connection failed")

    monkeypatch.setattr(
        "app.routers.cart.httpx.AsyncClient",
        lambda: FailingAsyncClient(),
    )

    response = client.post(
        "/carts/",
        json={
            "customer_id": str(customer_id),
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "Order Service unavailable"


def test_create_cart_duplicate_customer(client, db, monkeypatch):
    customer_id = uuid.uuid4()

    existing_cart = Cart(
        customer_id=customer_id,
        total_price=Decimal("0.00"),
    )

    db.add(existing_cart)
    db.commit()

    monkeypatch.setattr(
        "app.routers.cart.httpx.AsyncClient",
        lambda: FakeAsyncClient(status_code=200),
    )

    response = client.post(
        "/carts/",
        json={
            "customer_id": str(customer_id),
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Customer already has a cart"



def test_get_cart_by_customer(client, db):
    customer_id = uuid.uuid4()

    cart = Cart(
        customer_id=customer_id,
        total_price=Decimal("0.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    response = client.get(
        f"/carts/customer/{customer_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["cart_id"] == str(cart.cart_id)
    assert data["customer_id"] == str(customer_id)
    assert data["total_price"] == "0.00"
    assert data["items"] == []


def test_get_cart_by_customer_not_found(client):
    customer_id = uuid.uuid4()

    response = client.get(
        f"/carts/customer/{customer_id}"
    )

    assert response.status_code == 404
    assert (
        response.json()["detail"]
        == f"Cart not found for customer_id {customer_id}"
    )



def test_get_cart(client, db):
    customer_id = uuid.uuid4()

    cart = Cart(
        customer_id=customer_id,
        total_price=Decimal("0.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    response = client.get(
        f"/carts/{cart.cart_id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["cart_id"] == str(cart.cart_id)
    assert data["customer_id"] == str(customer_id)


def test_get_cart_not_found(client):
    cart_id = uuid.uuid4()

    response = client.get(
        f"/carts/{cart_id}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart not found"




def test_add_cart_item(client, db, monkeypatch):
    customer_id = uuid.uuid4()

    cart = Cart(
        customer_id=customer_id,
        total_price=Decimal("0.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    product_id = uuid.uuid4()

    monkeypatch.setattr(
        "app.routers.cart.httpx.get",
        lambda *args, **kwargs: fake_product_response(
            quantity=100,
            price=50.00,
        ),
    )

    response = client.post(
        f"/carts/{cart.cart_id}/items",
        json={
            "product_id": str(product_id),
            "quantity": 2,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["product_id"] == str(product_id)
    assert data["quantity"] == 2
    assert data["price"] == "50.0"


def test_add_cart_item_updates_existing_item(
    client,
    db,
    monkeypatch,
):
    customer_id = uuid.uuid4()
    product_id = uuid.uuid4()

    cart = Cart(
        customer_id=customer_id,
        total_price=Decimal("50.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    item = CartItem(
        cart_id=cart.cart_id,
        product_id=product_id,
        quantity=1,
        price=Decimal("50.00"),
    )

    db.add(item)
    db.commit()

    monkeypatch.setattr(
        "app.routers.cart.httpx.get",
        lambda *args, **kwargs: fake_product_response(
            quantity=100,
            price=50.00,
        ),
    )

    response = client.post(
        f"/carts/{cart.cart_id}/items",
        json={
            "product_id": str(product_id),
            "quantity": 2,
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["quantity"] == 3
    assert data["price"] == "50.00"


def test_add_cart_item_cart_not_found(client, monkeypatch):
    cart_id = uuid.uuid4()

    response = client.post(
        f"/carts/{cart_id}/items",
        json={
            "product_id": str(uuid.uuid4()),
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart not found!"


def test_add_cart_item_product_not_found(
    client,
    db,
    monkeypatch,
):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("0.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    monkeypatch.setattr(
        "app.routers.cart.httpx.get",
        lambda *args, **kwargs: FakeResponse(
            status_code=404
        ),
    )

    response = client.post(
        f"/carts/{cart.cart_id}/items",
        json={
            "product_id": str(uuid.uuid4()),
            "quantity": 1,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found!"


def test_add_cart_item_product_service_error(
    client,
    db,
    monkeypatch,
):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("0.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    monkeypatch.setattr(
        "app.routers.cart.httpx.get",
        lambda *args, **kwargs: FakeResponse(
            status_code=500
        ),
    )

    response = client.post(
        f"/carts/{cart.cart_id}/items",
        json={
            "product_id": str(uuid.uuid4()),
            "quantity": 1,
        },
    )

    assert response.status_code == 502
    assert response.json()["detail"] == (
        "Failed to get product information"
    )


def test_add_cart_item_product_service_unavailable(
    client,
    db,
    monkeypatch,
):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("0.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    def failing_get(*args, **kwargs):
        raise httpx.RequestError("Connection failed")

    monkeypatch.setattr(
        "app.routers.cart.httpx.get",
        failing_get,
    )

    response = client.post(
        f"/carts/{cart.cart_id}/items",
        json={
            "product_id": str(uuid.uuid4()),
            "quantity": 1,
        },
    )

    assert response.status_code == 503
    assert response.json()["detail"] == "product-service gone wrong"


def test_add_cart_item_insufficient_stock(
    client,
    db,
    monkeypatch,
):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("0.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    monkeypatch.setattr(
        "app.routers.cart.httpx.get",
        lambda *args, **kwargs: fake_product_response(
            quantity=2,
            price=50.00,
        ),
    )

    response = client.post(
        f"/carts/{cart.cart_id}/items",
        json={
            "product_id": str(uuid.uuid4()),
            "quantity": 5,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough product quality"


def test_add_cart_item_invalid_quantity(client, db):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("0.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    response = client.post(
        f"/carts/{cart.cart_id}/items",
        json={
            "product_id": str(uuid.uuid4()),
            "quantity": 0,
        },
    )

    assert response.status_code == 422





def test_update_cart_item(client, db, monkeypatch):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("100.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    product_id = uuid.uuid4()

    item = CartItem(
        cart_id=cart.cart_id,
        product_id=product_id,
        quantity=2,
        price=Decimal("50.00"),
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    monkeypatch.setattr(
        "app.routers.cart.httpx.get",
        lambda *args, **kwargs: fake_product_response(
            quantity=100,
            price=60.00,
        ),
    )

    response = client.put(
        f"/carts/{cart.cart_id}/items/{item.item_id}",
        json={
            "quantity": 5,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["quantity"] == 5
    assert data["price"] == "60.0"


def test_update_cart_item_cart_not_found(client):
    response = client.put(
        f"/carts/{uuid.uuid4()}/items/{uuid.uuid4()}",
        json={
            "quantity": 2,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart not found!"


def test_update_cart_item_not_found(client, db):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("0.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    response = client.put(
        f"/carts/{cart.cart_id}/items/{uuid.uuid4()}",
        json={
            "quantity": 2,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart item not found"


def test_update_cart_item_wrong_cart(client, db):
    cart1 = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("0.00"),
    )

    cart2 = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("0.00"),
    )

    db.add_all([cart1, cart2])
    db.commit()
    db.refresh(cart1)
    db.refresh(cart2)

    item = CartItem(
        cart_id=cart1.cart_id,
        product_id=uuid.uuid4(),
        quantity=1,
        price=Decimal("50.00"),
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    response = client.put(
        f"/carts/{cart2.cart_id}/items/{item.item_id}",
        json={
            "quantity": 2,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart item not found"


def test_update_cart_item_insufficient_stock(
    client,
    db,
    monkeypatch,
):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("50.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    item = CartItem(
        cart_id=cart.cart_id,
        product_id=uuid.uuid4(),
        quantity=1,
        price=Decimal("50.00"),
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    monkeypatch.setattr(
        "app.routers.cart.httpx.get",
        lambda *args, **kwargs: fake_product_response(
            quantity=2,
            price=50.00,
        ),
    )

    response = client.put(
        f"/carts/{cart.cart_id}/items/{item.item_id}",
        json={
            "quantity": 5,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Not enough product quantity"


def test_update_cart_item_product_not_found(
    client,
    db,
    monkeypatch,
):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("50.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    item = CartItem(
        cart_id=cart.cart_id,
        product_id=uuid.uuid4(),
        quantity=1,
        price=Decimal("50.00"),
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    monkeypatch.setattr(
        "app.routers.cart.httpx.get",
        lambda *args, **kwargs: FakeResponse(
            status_code=404
        ),
    )

    response = client.put(
        f"/carts/{cart.cart_id}/items/{item.item_id}",
        json={
            "quantity": 2,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found!"




def test_delete_cart_item(client, db):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("100.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    item = CartItem(
        cart_id=cart.cart_id,
        product_id=uuid.uuid4(),
        quantity=2,
        price=Decimal("50.00"),
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    item_id = item.item_id

    response = client.delete(
        f"/carts/{cart.cart_id}/items/{item_id}"
    )

    assert response.status_code == 200

    assert response.json()["message"] == (
        "Item was deleted successfully"
    )

    deleted_item = db.get(CartItem, item_id)

    assert deleted_item is None


def test_delete_cart_item_cart_not_found(client):
    response = client.delete(
        f"/carts/{uuid.uuid4()}/items/{uuid.uuid4()}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart is not found!"


def test_delete_cart_item_not_found(client, db):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("0.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    response = client.delete(
        f"/carts/{cart.cart_id}/items/{uuid.uuid4()}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Item is not found in your cart"
    )




def test_delete_cart(client, db):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("0.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    cart_id = cart.cart_id

    response = client.delete(
        f"/carts/{cart_id}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Cart was deleted successfully"
    )

    deleted_cart = db.get(Cart, cart_id)

    assert deleted_cart is None


def test_delete_cart_with_items(client, db):
    cart = Cart(
        customer_id=uuid.uuid4(),
        total_price=Decimal("100.00"),
    )

    db.add(cart)
    db.commit()
    db.refresh(cart)

    item = CartItem(
        cart_id=cart.cart_id,
        product_id=uuid.uuid4(),
        quantity=2,
        price=Decimal("50.00"),
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    item_id = item.item_id
    cart_id = cart.cart_id

    response = client.delete(
        f"/carts/{cart_id}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == (
        "Cart was deleted successfully"
    )

    assert db.get(Cart, cart_id) is None
    assert db.get(CartItem, item_id) is None


def test_delete_cart_not_found(client):
    response = client.delete(
        f"/carts/{uuid.uuid4()}"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Cart not found!"
