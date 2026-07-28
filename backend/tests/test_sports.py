from fastapi import status

from app.models.user import User, UserRole


def register_and_get_token(client, db_session, email: str, role: UserRole) -> str:
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": f"{role.value.capitalize()} User",
            "password": "Password123",
        },
    )
    assert reg_resp.status_code == status.HTTP_201_CREATED
    user_id = reg_resp.json()["id"]

    if role != UserRole.PLAYER:
        user = db_session.query(User).filter(User.id == user_id).first()
        user.role = role
        user.is_admin = (role == UserRole.ADMIN)
        db_session.commit()

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123"},
    )
    assert login_resp.status_code == status.HTTP_200_OK
    return login_resp.json()["access_token"]


def test_public_sports_list(client):
    response = client.get("/api/v1/sports")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_admin_creates_sport(client, db_session):
    admin_token = register_and_get_token(client, db_session, "admin_sport@example.com", UserRole.ADMIN)
    headers = {"Authorization": f"Bearer {admin_token}"}

    payload = {
        "name_en": "Squash",
        "name_ar": "سكواش",
        "slug": "squash",
        "icon": "squash-racket",
    }
    resp = client.post("/api/v1/sports", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["slug"] == "squash"
    assert data["name_en"] == "Squash"
    assert "id" in data

    # Test get sport by id
    get_resp = client.get(f"/api/v1/sports/{data['id']}")
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["slug"] == "squash"


def test_player_cannot_create_sport(client, db_session):
    player_token = register_and_get_token(client, db_session, "player_sport@example.com", UserRole.PLAYER)
    headers = {"Authorization": f"Bearer {player_token}"}

    payload = {
        "name_en": "Golf",
        "name_ar": "غولف",
        "slug": "golf",
    }
    resp = client.post("/api/v1/sports", json=payload, headers=headers)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_sport_not_found(client):
    resp = client.get("/api/v1/sports/99999")
    assert resp.status_code == status.HTTP_404_NOT_FOUND
