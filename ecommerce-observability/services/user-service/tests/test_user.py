from sqlalchemy import select

from app.models.user import User
from app.models.authority import Authority


def create_user(client, email, password="123456", enable=True):
    response = client.post(
        "/users/",
        json={
            "email": email,
            "password": password,
            "enable": enable,
        },
    )

    assert response.status_code == 201

    return response


def create_admin(db, email):
    authority = Authority(
        email=email,
        authority="ADMIN",
    )

    db.add(authority)
    db.commit()


def login(client, email, password="123456"):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


# ============================================================
# POST /users/
# ============================================================

def test_create_user(client):
    response = create_user(
        client,
        "createuser@example.com",
    )

    data = response.json()

    assert response.status_code == 201
    assert data["email"] == "createuser@example.com"
    assert data["enable"] is True


def test_create_duplicate_user(client):
    create_user(
        client,
        "duplicateuser@example.com",
    )

    response = client.post(
        "/users/",
        json={
            "email": "duplicateuser@example.com",
            "password": "123456",
            "enable": True,
        },
    )

    assert response.status_code == 400


def test_create_user_invalid_email(client):
    response = client.post(
        "/users/",
        json={
            "email": "invalid-email",
            "password": "123456",
            "enable": True,
        },
    )

    assert response.status_code == 422


# ============================================================
# GET /users/me
# ============================================================

def test_get_current_user(client):
    create_user(
        client,
        "me@example.com",
    )

    token = login(
        client,
        "me@example.com",
    )

    response = client.get(
        "/users/me",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "me@example.com"


def test_get_current_user_without_token(client):
    response = client.get("/users/me")

    assert response.status_code == 401


def test_get_current_user_invalid_token(client):
    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer invalid-token"
        },
    )

    assert response.status_code == 401


def test_get_current_user_disabled(client):
    create_user(
        client,
        "disableduser@example.com",
        enable=False,
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "disableduser@example.com",
            "password": "123456",
        },
    )

    assert response.status_code == 403


# ============================================================
# GET /users/internal/{email}
# ============================================================

def test_get_user_internal(client):
    create_user(
        client,
        "internal@example.com",
    )

    response = client.get(
        "/users/internal/internal@example.com"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "internal@example.com"


def test_get_user_internal_not_found(client):
    response = client.get(
        "/users/internal/notfound@example.com"
    )

    assert response.status_code == 404


# ============================================================
# GET /users/ - ADMIN
# ============================================================

def test_get_users_as_admin(client, db):
    create_user(client,"admin@example.com",)

    create_admin(db,"admin@example.com",)

    create_user(client,"normaluser@example.com",)

    token = login(client,"admin@example.com",)

    response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)


def test_get_users_as_normal_user(client):
    create_user(client,"normal@example.com",)

    token = login(client,"normal@example.com",)

    response = client.get(
        "/users/",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 403



def test_get_user_as_admin(client, db):
    create_user(client,"adminget@example.com",)

    create_admin(db,"adminget@example.com",)

    create_user(client,"target@example.com",)

    token = login(client,"adminget@example.com",)

    response = client.get(
        "/users/target@example.com",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "target@example.com"


def test_get_user_not_found_as_admin(client, db):
    create_user(client,"adminnotfound@example.com",)

    create_admin(db,"adminnotfound@example.com",)

    token = login(client,"adminnotfound@example.com",)

    response = client.get(
        "/users/notfound@example.com",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404




def test_update_user_as_admin(client, db):
    create_user(client,"adminupdate@example.com",)

    create_admin(db,"adminupdate@example.com",)

    create_user(client,"update-target@example.com",)

    token = login(client,"adminupdate@example.com",)

    response = client.put(
        "/users/update-target@example.com",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "enable": False,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "update-target@example.com"
    assert data["enable"] is False


def test_update_user_not_found(client, db):
    create_user(client,"adminupdate404@example.com",)

    create_admin(db,"adminupdate404@example.com",)

    token = login(client,"adminupdate404@example.com",)

    response = client.put(
        "/users/notfound@example.com",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "enable": False,
        },
    )

    assert response.status_code == 404



def test_delete_user_as_admin(client, db):
    create_user(client,"admindelete@example.com",)

    create_admin(db,"admindelete@example.com",)

    create_user(client,"delete-target@example.com",)

    token = login(client,"admindelete@example.com",)

    response = client.delete(
        "/users/delete-target@example.com",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "User deleted successfully"

    # Verify user was actually deleted
    deleted_user = db.scalar(
        select(User).where(
            User.email == "delete-target@example.com"
        )
    )

    assert deleted_user is None


def test_delete_user_not_found(client, db):
    create_user(client,"admindelete404@example.com",)

    create_admin(db,"admindelete404@example.com",)

    token = login(client,"admindelete404@example.com",)

    response = client.delete(
        "/users/notfound@example.com",
        headers={
            "Authorization": f"Bearer {token}"
        },
    )

    assert response.status_code == 404