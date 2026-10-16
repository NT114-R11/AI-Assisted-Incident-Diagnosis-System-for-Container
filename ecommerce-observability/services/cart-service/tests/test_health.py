def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "cart-service",
    }


def test_ready(client):
    response = client.get("/ready")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "ready"
    assert data["service"] == "cart-service"
    assert data["database"] == "up"


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": "cart-service",
        "status": "running",
    }
