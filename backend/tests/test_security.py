from fastapi import status

from app.models.user import UserRole


def register_and_get_token(client, email: str) -> tuple[int, str]:
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "full_name": "Test User",
            "password": "Password123",
        },
    )
    assert reg_resp.status_code == status.HTTP_201_CREATED
    user_id = reg_resp.json()["id"]

    login_resp = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Password123"},
    )
    assert login_resp.status_code == status.HTTP_200_OK
    token = login_resp.json()["access_token"]
    return user_id, token


def promote_user_to_admin(db_session, user_id: int):
    """Helper to set admin role directly in test DB for setup."""
    from app.models.user import User
    user = db_session.query(User).filter(User.id == user_id).first()
    user.role = UserRole.ADMIN
    user.is_admin = True
    db_session.commit()


def test_public_registration_cannot_set_admin_or_owner(client):
    # Attempt registration passing role='admin'
    admin_attempt = client.post(
        "/api/v1/auth/register",
        json={
            "email": "hacker_admin@example.com",
            "full_name": "Hacker Admin",
            "password": "Password123",
            "role": "admin",
        },
    )
    assert admin_attempt.status_code == status.HTTP_201_CREATED
    data_admin = admin_attempt.json()
    assert data_admin["role"] == "player"
    assert data_admin["is_admin"] is False

    # Attempt registration passing role='owner'
    owner_attempt = client.post(
        "/api/v1/auth/register",
        json={
            "email": "hacker_owner@example.com",
            "full_name": "Hacker Owner",
            "password": "Password123",
            "role": "owner",
        },
    )
    assert owner_attempt.status_code == status.HTTP_201_CREATED
    data_owner = owner_attempt.json()
    assert data_owner["role"] == "player"
    assert data_owner["is_admin"] is False


def test_admin_updates_user_role(client, db_session):
    admin_id, admin_token = register_and_get_token(client, "admin1@example.com")
    promote_user_to_admin(db_session, admin_id)

    target_id, _ = register_and_get_token(client, "player1@example.com")

    # Admin promotes player to owner
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    resp1 = client.patch(
        f"/api/v1/admin/users/{target_id}/role",
        json={"role": "owner"},
        headers=h_admin,
    )
    assert resp1.status_code == status.HTTP_200_OK
    assert resp1.json()["role"] == "owner"
    assert resp1.json()["is_admin"] is False

    # Admin promotes owner to admin
    resp2 = client.patch(
        f"/api/v1/admin/users/{target_id}/role",
        json={"role": "admin"},
        headers=h_admin,
    )
    assert resp2.status_code == status.HTTP_200_OK
    assert resp2.json()["role"] == "admin"
    assert resp2.json()["is_admin"] is True


def test_non_admin_cannot_change_roles(client, db_session):
    admin_id, admin_token = register_and_get_token(client, "admin2@example.com")
    promote_user_to_admin(db_session, admin_id)

    player_id, player_token = register_and_get_token(client, "player2@example.com")

    # Player tries to promote self to owner -> 403 Forbidden
    h_player = {"Authorization": f"Bearer {player_token}"}
    resp = client.patch(
        f"/api/v1/admin/users/{player_id}/role",
        json={"role": "owner"},
        headers=h_player,
    )
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_prevent_demoting_only_remaining_admin(client, db_session):
    admin_id, admin_token = register_and_get_token(client, "sole_admin@example.com")
    promote_user_to_admin(db_session, admin_id)

    h_admin = {"Authorization": f"Bearer {admin_token}"}

    # Sole admin attempts self-demotion -> 400 Bad Request
    demote_resp = client.patch(
        f"/api/v1/admin/users/{admin_id}/role",
        json={"role": "player"},
        headers=h_admin,
    )
    assert demote_resp.status_code == status.HTTP_400_BAD_REQUEST
    assert "only remaining active administrator" in demote_resp.json()["detail"].lower()

    # Create second admin
    admin2_id, _ = register_and_get_token(client, "second_admin@example.com")
    promote_user_to_admin(db_session, admin2_id)

    # Now demotion of first admin succeeds
    demote_resp2 = client.patch(
        f"/api/v1/admin/users/{admin_id}/role",
        json={"role": "player"},
        headers=h_admin,
    )
    assert demote_resp2.status_code == status.HTTP_200_OK
    assert demote_resp2.json()["role"] == "player"
    assert demote_resp2.json()["is_admin"] is False


def test_admin_role_update_invalid_user_and_role(client, db_session):
    admin_id, admin_token = register_and_get_token(client, "admin3@example.com")
    promote_user_to_admin(db_session, admin_id)
    h_admin = {"Authorization": f"Bearer {admin_token}"}

    # Non-existent user id -> 404
    resp_404 = client.patch(
        "/api/v1/admin/users/99999/role",
        json={"role": "owner"},
        headers=h_admin,
    )
    assert resp_404.status_code == status.HTTP_404_NOT_FOUND

    # Invalid role enum -> 422
    resp_422 = client.patch(
        f"/api/v1/admin/users/{admin_id}/role",
        json={"role": "superhero"},
        headers=h_admin,
    )
    assert resp_422.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
