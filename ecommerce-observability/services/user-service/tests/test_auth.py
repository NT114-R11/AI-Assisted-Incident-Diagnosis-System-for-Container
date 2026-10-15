def test_register_user(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "testuser2@example.com",
            "password": "123456",
        }
    )

    assert response.status_code == 201


def test_register_existing_user(client):
    # First, register the user
    first_response = client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "123456"
    })

    assert first_response.status_code == 201

    # Then, try to register the same user again
    second_response = client.post("/auth/register", json={
        "email": "duplicate@example.com",
        "password": "123457"
    })

    assert second_response.status_code == 400

def test_register_short_password(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "testuser3@example.com",
            "password": "123"
        }
    )

    assert response.status_code == 422

def test_missing_email(client):
    response = client.post(
        "/auth/register",
        json={
            "password": "123456"
        }
    )

    assert response.status_code == 422

def test_missing_password(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "testuser4@example.com"
        },
    )
    assert response.status_code == 422

def test_register_user_invalid_email(client):
    response = client.post(
        "/auth/register",
        json={
            "email": "invalid-email",
            "password": "123456",
        }
    )

    assert response.status_code == 422



def test_login_success(client):
    # First, register the user
    register_response = client.post("/auth/register", json={
        "email": "testuser2@example.com",
        "password": "123456"
    })
    assert register_response.status_code == 201

    # Then, attempt to log in

    login_response = client.post("/auth/login", json={
        "email": "testuser2@example.com",
        "password": "123456"
    })
    assert login_response.status_code == 200
    data = login_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_wrong_password(client):
    # First, register the user
    register_response = client.post("/auth/register", json={
        "email": "testuser2@example.com",
        "password": "123456"
    })
    assert register_response.status_code == 201

    # Then, attempt to log in with the wrong password
    login_response = client.post("/auth/login", json={
        "email": "testuser2@example.com",
        "password": "wrongpassword"
    })
    assert login_response.status_code == 401

def test_login_unknown_email(client):
    login_response = client.post("/auth/login", json={
        "email": "doesnotexist@example.com",
        "password": "123456"
    })
    assert login_response.status_code == 401