from fastapi import status


def test_root_and_health_endpoints(client):
    response = client.get("/")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "MAL3AB API is running", "status": "success"}

    health_resp = client.get("/health")
    assert health_resp.status_code == status.HTTP_200_OK
    assert health_resp.json() == {"status": "healthy", "database": "connected"}


def test_register_user_success(client):
    payload = {
        "email": "testuser@example.com",
        "full_name": "Test User",
        "password": "securepassword123",
        "phone_number": "+1234567890",
    }
    response = client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert data["full_name"] == "Test User"
    assert "id" in data
    assert "hashed_password" not in data
    assert "password" not in data


def test_register_duplicate_email(client):
    payload = {
        "email": "duplicate@example.com",
        "full_name": "First User",
        "password": "securepassword123",
    }
    first_resp = client.post("/api/v1/auth/register", json=payload)
    assert first_resp.status_code == status.HTTP_201_CREATED

    duplicate_payload = {
        "email": "DUPLICATE@example.com",  # Should test case-insensitivity
        "full_name": "Second User",
        "password": "anotherpassword123",
    }
    second_resp = client.post("/api/v1/auth/register", json=duplicate_payload)
    assert second_resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "already exists" in second_resp.json()["detail"].lower()


def test_register_invalid_email_and_short_password(client):
    # Invalid email format
    invalid_email_resp = client.post(
        "/api/v1/auth/register",
        json={"email": "invalid-email", "full_name": "Invalid", "password": "securepassword123"},
    )
    assert invalid_email_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Short password (< 8 chars)
    short_pwd_resp = client.post(
        "/api/v1/auth/register",
        json={"email": "short@example.com", "full_name": "Short Pwd", "password": "123"},
    )
    assert short_pwd_resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_login_success(client):
    # Register user first
    reg_payload = {
        "email": "login_user@example.com",
        "full_name": "Login User",
        "password": "mypassword123",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "login_user@example.com",
        "password": "mypassword123",
    }
    response = client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


def test_login_invalid_credentials(client):
    # Non-existent user
    resp1 = client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "somepassword"},
    )
    assert resp1.status_code == status.HTTP_401_UNAUTHORIZED

    # Register user
    reg_payload = {
        "email": "user_wrong_pwd@example.com",
        "full_name": "Wrong Password User",
        "password": "correctpassword",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    # Wrong password
    resp2 = client.post(
        "/api/v1/auth/login",
        json={"email": "user_wrong_pwd@example.com", "password": "wrongpassword"},
    )
    assert resp2.status_code == status.HTTP_401_UNAUTHORIZED


def test_protected_me_endpoint(client):
    # Unauthenticated access
    unauth_resp = client.get("/api/v1/users/me")
    assert unauth_resp.status_code == status.HTTP_401_UNAUTHORIZED

    # Register and login
    reg_payload = {
        "email": "me_user@example.com",
        "full_name": "Me User",
        "password": "mypassword123",
    }
    client.post("/api/v1/auth/register", json=reg_payload)

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": "me_user@example.com", "password": "mypassword123"},
    )
    token = login_resp.json()["access_token"]

    # Authenticated access
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = client.get("/api/v1/users/me", headers=headers)
    assert me_resp.status_code == status.HTTP_200_OK
    user_data = me_resp.json()
    assert user_data["email"] == "me_user@example.com"
    assert user_data["full_name"] == "Me User"
    assert "hashed_password" not in user_data


def test_invalid_jwt_token(client):
    headers = {"Authorization": "Bearer invalid_jwt_token_string"}
    resp = client.get("/api/v1/users/me", headers=headers)
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED
