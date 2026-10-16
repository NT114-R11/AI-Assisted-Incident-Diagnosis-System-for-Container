import uuid
from app.models.product import Product
from app.models.seller import Seller


"""
Part 1: Test Get Product
"""
def test_get_products_empty(client):
    response = client.get("/products/")

    assert response.status_code == 200
    assert response.json() == []


def test_get_products(client,db):
    seller = Seller(shop_name = "Test shop", user_email = "seller@test.com")

    db.add(seller)
    db.commit()
    db.refresh(seller)

    product = Product(
        product_name = "Test product",
        quantity = 10,
        description = "Test description",
        manufacturer = "Test manufacturer",
        categories = "Test category",
        price =100.00,
        seller_id =seller.id
    )

    db.add(product)
    db.commit()
    response = client.get("/products/")
    assert response.status_code == 200
    data = response.json()

    assert len(data) == 1
    assert data[0]["product_name"] == "Test product"
    assert data[0]["quantity"] == 10
    assert data[0]["seller_id"] == str(seller.id)

def test_get_product(client,db):
    seller = Seller(shop_name="Test shop", user_email="seller@test.com")
    db.add(seller)
    db.commit()
    db.refresh(seller)

    product = Product(
        product_name = "Test Product",
        quantity =10,
        description = "Test description",
        manufacturer = "Test manufacturer",
        categories = "Test category",
        price =100.00,
        seller_id =seller.id
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    response = client.get(f"/products/{product.product_id}")

    assert response.status_code == 200
    data = response.json()

    assert data["product_id"] == str(product.product_id)
    assert data["product_name"] == "Test Product"
    assert data["quantity"] == 10
    assert data["price"] == 100.0
    assert data["seller_id"] == str(seller.id)

def test_get_product_notfound(client):
    product_id = uuid.uuid4()

    response = client.get(f"/products/{product_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found!"


"""
Part 2 Test Create product
"""

def test_create_product(client, db):
    
    seller = Seller(
        shop_name = "Test shop",
        user_email = "create@test.com"
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    payload = {
        "product_name": "IPhone 18 pro max",
        "quantity": 10,
        "description": "New model profeshional",
        "manufacturer": "Apple Inc",
        "categories": "Smart phone",
        "price": 2300.00,
        "seller_id": str(seller.id)
    }

    request = client.post("/products/", json=payload)
    assert request.status_code == 201
    data = request.json()

    assert data["product_name"] == "IPhone 18 pro max"
    assert data["quantity"] == 10
    assert data["price"] == 2300.00
    assert data["seller_id"] == str(seller.id)

def test_create_product_with_seller_notfound(client):
    payload = {
        "product_name": "Product name",
        "quantity": 10,
        "description": "Test",
        "manufacturer": "Test",
        "categories": "Test",
        "price": 100.00,
        "seller_id": str(uuid.uuid4())
    }
    request = client.post("/products/", json=payload)

    assert request.status_code == 404
    assert "does not exists" in request.json()["detail"]

"""
Part 3 Update information
"""

def test_update_product(client, db):
    seller = Seller(
        shop_name = "Test shop",
        user_email = "update@test.com"
    )
    db.add(seller)
    db.commit()
    db.refresh(seller)


    product = Product(
        product_name = "Old Product",
        quantity = 10,
        price = 100.00,
        seller_id = seller.id
    )
    db.add(product)
    db.commit()
    db.refresh(product)

    payload = {
        "product_name": "Updated Product",
        "quantity": 14,
        "price": 110.00
    }

    request = client.put(f"/products/{product.product_id}", json=payload)

    assert request.status_code == 200

    data = request.json()
    assert data["product_name"] == "Updated Product"
    assert data["quantity"] == 14
    assert data["price"] == 110.00


def test_update_product_partial(client,db):
    seller = Seller(
        shop_name = "Partial Update Shop",
        user_email = "Partial@test.com"
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    product = Product(
        product_name = "Original name product",
        quantity = 10,
        price = 100.00,
        description = "Original description",
        seller_id = seller.id
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    payload = {
        "price": 99.13
    }

    request = client.put(f"/products/{product.product_id}", json=payload)

    assert request.status_code == 200

    data = request.json()

    assert data["product_name"] == "Original name product"
    assert data["quantity"] == 10
    assert data["price"] == 99.13
    assert data["description"] == "Original description"


def test_update_product_not_found(client):
    product_id = uuid.uuid4()

    response = client.put(
        f"/products/{product_id}",
        json={
            "product_name": "Updated Product",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found!"


def test_update_product_invalid_seller(client, db):
    seller = Seller(
        shop_name="Update Seller",
        user_email="updateseller@test.com",
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    product = Product(
        product_name="Product",
        quantity=10,
        price=100.00,
        seller_id=seller.id,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    payload = {
        "seller_id": str(uuid.uuid4()),
    }

    response = client.put(
        f"/products/{product.product_id}",
        json=payload,
    )

    assert response.status_code == 404
    assert "does not exist" in response.json()["detail"]


"""
Part 4 Delete and check Inventory
"""

def test_delete_product(client, db):
    seller = Seller(
        shop_name="Delete Shop",
        user_email="delete@test.com",
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    product = Product(
        product_name="Delete Product",
        quantity=10,
        price=100.00,
        seller_id=seller.id,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    product_id = product.product_id

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == 204

    deleted_product = db.get(Product, product_id)

    assert deleted_product is None


def test_delete_product_not_found(client):
    product_id = uuid.uuid4()

    response = client.delete(f"/products/{product_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found!"



def test_deduct_stock(client, db):
    seller = Seller(
        shop_name="Stock Shop",
        user_email="stock@test.com",
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    product = Product(
        product_name="Stock Product",
        quantity=100,
        price=50.00,
        seller_id=seller.id,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    response = client.patch(
        f"/products/{product.product_id}/deduct-stock",
        json={"quantity": 30},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Stock deducted successfully"
    assert data["remaining_quantity"] == 70
    assert data["price"] == 50.0


def test_deduct_stock_insufficient(client, db):
    seller = Seller(
        shop_name="Insufficient Shop",
        user_email="insufficient@test.com",
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    product = Product(
        product_name="Limited Product",
        quantity=10,
        price=50.00,
        seller_id=seller.id,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    response = client.patch(
        f"/products/{product.product_id}/deduct-stock",
        json={"quantity": 20},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Insufficient stock"


def test_deduct_stock_product_not_found(client):
    product_id = uuid.uuid4()

    response = client.patch(
        f"/products/{product_id}/deduct-stock",
        json={"quantity": 10},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"



def test_restore_stock(client, db):
    seller = Seller(
        shop_name="Restore Shop",
        user_email="restore@test.com",
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    product = Product(
        product_name="Restore Product",
        quantity=50,
        price=50.00,
        seller_id=seller.id,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    response = client.patch(
        f"/products/{product.product_id}/restore-stock",
        json={"quantity": 25},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Stock restored successfully"
    assert data["current_quantity"] == 75


def test_restore_stock_product_not_found(client):
    product_id = uuid.uuid4()

    response = client.patch(
        f"/products/{product_id}/restore-stock",
        json={"quantity": 10},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Product not found"