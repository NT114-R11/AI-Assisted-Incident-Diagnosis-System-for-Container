import uuid

from app.models.seller import Seller



class FakeResponse:
    def __init__(self, status_code):
        self.status_code = status_code


class FakeAsyncClient:
    def __init__(self, status_code=200):
        self.status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        pass

    async def get(self, *args, **kwargs):
        return FakeResponse(self.status_code)




def test_create_seller(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.seller.httpx.AsyncClient",
        lambda: FakeAsyncClient(status_code=200),
    )

    payload = {
        "user_email": "new-seller@test.com",
        "shop_name": "New Shop",
        "description": "New seller",
        "phone": "0123456789",
    }

    response = client.post("/sellers/", json=payload)

    assert response.status_code == 200

    data = response.json()

    assert data["user_email"] == "new-seller@test.com"
    assert data["shop_name"] == "New Shop"
    assert data["description"] == "New seller"
    assert data["phone"] == "0123456789"
    assert "id" in data


def test_create_seller_user_not_found(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.seller.httpx.AsyncClient",
        lambda: FakeAsyncClient(status_code=404),
    )

    payload = {
        "user_email": "missing@test.com",
        "shop_name": "Missing Shop",
    }

    response = client.post("/sellers/", json=payload)

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "User email does not exist in user-service"
    )


def test_create_seller_user_service_error(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.seller.httpx.AsyncClient",
        lambda: FakeAsyncClient(status_code=500),
    )

    payload = {
        "user_email": "error@test.com",
        "shop_name": "Error Shop",
    }

    response = client.post("/sellers/", json=payload)

    assert response.status_code == 503
    assert response.json()["detail"] == (
        "user-service error to during verfication"
    )


def test_create_seller_duplicate_email(client, db, monkeypatch):
    monkeypatch.setattr(
        "app.routers.seller.httpx.AsyncClient",
        lambda: FakeAsyncClient(status_code=200),
    )

    seller = Seller(
        user_email="duplicate@test.com",
        shop_name="Existing Shop",
    )

    db.add(seller)
    db.commit()

    payload = {
        "user_email": "duplicate@test.com",
        "shop_name": "Another Shop",
    }

    response = client.post("/sellers/", json=payload)

    assert response.status_code == 400
    assert response.json()["detail"] == (
        "Seller with this email already exists."
    )




def test_get_sellers_empty(client):
    response = client.get("/sellers/")

    assert response.status_code == 200
    assert response.json() == []


def test_get_sellers(client, db):
    seller = Seller(
        user_email="seller@test.com",
        shop_name="Test Shop",
        description="Test description",
        phone="0123456789",
    )

    db.add(seller)
    db.commit()

    response = client.get("/sellers/")

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["user_email"] == "seller@test.com"
    assert data[0]["shop_name"] == "Test Shop"




def test_get_seller(client, db):
    seller = Seller(
        user_email="getseller@test.com",
        shop_name="Get Seller Shop",
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    response = client.get(f"/sellers/{seller.id}")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == str(seller.id)
    assert data["user_email"] == "getseller@test.com"
    assert data["shop_name"] == "Get Seller Shop"


def test_get_seller_not_found(client):
    seller_id = uuid.uuid4()

    response = client.get(f"/sellers/{seller_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Seller not found!"



def test_update_seller(client, db):
    seller = Seller(
        user_email="updateseller@test.com",
        shop_name="Old Shop",
        description="Old description",
        phone="0123456789",
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    payload = {
        "shop_name": "Updated Shop",
        "description": "Updated description",
        "phone": "0987654321",
    }

    response = client.put(
        f"/sellers/{seller.id}",
        json=payload,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["shop_name"] == "Updated Shop"
    assert data["description"] == "Updated description"
    assert data["phone"] == "0987654321"


def test_update_seller_partial(client, db):
    seller = Seller(
        user_email="partial-seller@test.com",
        shop_name="Original Shop",
        description="Original description",
        phone="0123456789",
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    response = client.put(
        f"/sellers/{seller.id}",
        json={
            "shop_name": "Only Name Changed",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["shop_name"] == "Only Name Changed"
    assert data["description"] == "Original description"
    assert data["phone"] == "0123456789"


def test_update_seller_not_found(client):
    seller_id = uuid.uuid4()

    response = client.put(
        f"/sellers/{seller_id}",
        json={
            "shop_name": "Updated Shop",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Seller not found!"


def test_delete_seller(client, db):
    seller = Seller(
        user_email="deleteseller@test.com",
        shop_name="Delete Shop",
    )

    db.add(seller)
    db.commit()
    db.refresh(seller)

    seller_id = seller.id

    response = client.delete(f"/sellers/{seller_id}")

    assert response.status_code == 200
    assert response.json()["message"] == "Seller deleted successfully"

    deleted_seller = db.get(Seller, seller_id)

    assert deleted_seller is None


def test_delete_seller_not_found(client):
    seller_id = uuid.uuid4()

    response = client.delete(f"/sellers/{seller_id}")

    assert response.status_code == 404
    assert response.json()["detail"] == "Seller not found!"
