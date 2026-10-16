
def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "user-service"


def test_root(client):
    response = client.get("/")

    assert response.status_code == 200

    data = response.json()

    assert data["service"] == "User service"
    assert data["status"] == "running"