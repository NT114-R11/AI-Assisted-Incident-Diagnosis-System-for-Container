def create_user(client, email, password="123456"):
    response = client.post(
        "/users/",
        json={
            "email": email,
            "password": password,
            "enable": True,
        },
    )

    assert response.status_code == 201


def login(client, email, password="123456"):
    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        }
    )

    assert response.status_code == 200

    return response.json()["access_token"]


def create_admin(db, email):
    from app.models.authority import Authority

    authority = Authority(
        email=email,
        authority="ADMIN",
    )

    db.add(authority)
    db.commit()


def test_create_authority_as_admin(client, db):
    create_user(client, "admin-auth@example.com")
    create_user(client, "target-auth@example.com")

    create_admin(db, "admin-auth@example.com")

    token = login(client,"admin-auth@example.com",)

    response = client.post(
        "/authorities/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "email": "target-auth@example.com",
            "authority": "SELLER",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "target-auth@example.com"
    assert data["authority"] == "SELLER"


def test_create_authority_uppercase(client, db):
    create_user(client, "admin-upper@example.com")
    create_user(client, "target-upper@example.com")

    create_admin(db, "admin-upper@example.com")

    token = login(client,"admin-upper@example.com")

    response = client.post(
        "/authorities/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "email": "target-upper@example.com",
            "authority": "seller",
        },
    )

    assert response.status_code == 201
    assert response.json()["authority"] == "SELLER"


def test_create_authority_user_not_found(client, db):
    create_user(client, "admin-notfound@example.com")

    create_admin(db,"admin-notfound@example.com")

    token = login(client,"admin-notfound@example.com")

    response = client.post(
        "/authorities/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "email": "doesnotexist@example.com",
            "authority": "SELLER",
        }
    )

    assert response.status_code == 404


def test_create_duplicate_authority(client, db):
    create_user(client, "admin-duplicate@example.com")
    create_user(client, "target-duplicate@example.com")

    create_admin(db,"admin-duplicate@example.com")

    token = login(client,"admin-duplicate@example.com")

    first_response = client.post(
        "/authorities/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "email": "target-duplicate@example.com",
            "authority": "SELLER",
        }
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/authorities/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "email": "target-duplicate@example.com",
            "authority": "SELLER",
        }
    )

    assert second_response.status_code == 400


def test_create_authority_as_normal_user(client):
    create_user(client, "normal-auth@example.com")
    create_user(client, "target-normal@example.com")

    token = login(client,"normal-auth@example.com")

    response = client.post(
        "/authorities/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "email": "target-normal@example.com",
            "authority": "SELLER",
        }
    )

    assert response.status_code == 403



def test_get_user_authorities_as_admin(client, db):
    create_user(client, "admin-get-auth@example.com")
    create_user(client, "target-get-auth@example.com")

    create_admin(db,"admin-get-auth@example.com",)

    token = login(client,"admin-get-auth@example.com",)

    # Create authority
    create_response = client.post(
        "/authorities/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "email": "target-get-auth@example.com",
            "authority": "SELLER",
        }
    )

    assert create_response.status_code == 201

    response = client.get(
        "/authorities/target-get-auth@example.com",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data) == 1
    assert data[0]["email"] == "target-get-auth@example.com"
    assert data[0]["authority"] == "SELLER"


def test_get_user_authorities_user_not_found(client, db):
    create_user(client, "admin-get404@example.com")

    create_admin(db,"admin-get404@example.com",)

    token = login(client,"admin-get404@example.com",)

    response = client.get("/authorities/notfound@example.com",headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 404


def test_get_user_authorities_as_normal_user(client):
    create_user(client, "normal-get-auth@example.com")
    create_user(client, "target-normal-get@example.com")

    token = login(client,"normal-get-auth@example.com",)

    response = client.get(
        "/authorities/target-normal-get@example.com",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403



def test_delete_authority_as_admin(client, db):
    create_user(client, "admin-delete-auth@example.com")
    create_user(client, "target-delete-auth@example.com")

    create_admin(db,"admin-delete-auth@example.com",)

    token = login(client,"admin-delete-auth@example.com",)

    # Create authority
    create_response = client.post(
        "/authorities/",
        headers={
            "Authorization": f"Bearer {token}"
        },
        json={
            "email": "target-delete-auth@example.com",
            "authority": "SELLER",
        }
    )

    assert create_response.status_code == 201

    # Delete authority
    response = client.delete(
        "/authorities/target-delete-auth@example.com/SELLER",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "Authority deleted successfully"


def test_delete_authority_not_found(client, db):
    create_user(client, "admin-delete404@example.com")

    create_admin(db,"admin-delete404@example.com",)

    token = login(client,"admin-delete404@example.com",)

    response = client.delete(
        "/authorities/admin-delete404@example.com/SELLER",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 404


def test_delete_authority_as_normal_user(client):
    create_user(client, "normal-delete-auth@example.com")
    create_user(client, "target-delete-normal@example.com")

    token = login(client,"normal-delete-auth@example.com")

    response = client.delete(
        "/authorities/target-delete-normal@example.com/SELLER",
        headers={
            "Authorization": f"Bearer {token}"
        }
    )

    assert response.status_code == 403