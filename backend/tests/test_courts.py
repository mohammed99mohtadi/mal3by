from decimal import Decimal
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


def create_test_sport(client, admin_token: str, name="Padel", slug="padel") -> int:
    headers = {"Authorization": f"Bearer {admin_token}"}
    resp = client.post(
        "/api/v1/sports",
        json={"name_en": name, "name_ar": name, "slug": slug},
        headers=headers,
    )
    assert resp.status_code == status.HTTP_201_CREATED
    return resp.json()["id"]


def test_owner_creates_court(client, db_session):
    admin_token = register_and_get_token(client, db_session, "admin_c1@example.com", UserRole.ADMIN)
    owner_token = register_and_get_token(client, db_session, "owner_c1@example.com", UserRole.OWNER)
    sport_id = create_test_sport(client, admin_token, "Padel 1", "padel-1")

    headers = {"Authorization": f"Bearer {owner_token}"}
    court_payload = {
        "sport_id": sport_id,
        "name_en": "Smash Padel Court 1",
        "name_ar": "ملعب سماش بادل 1",
        "description_en": "Premium indoor padel court",
        "area": "Salmiya",
        "address": "Block 4, Street 10",
        "price_per_hour": 15.5,
        "currency": "KWD",
        "capacity": 4,
    }
    resp = client.post("/api/v1/courts", json=court_payload, headers=headers)
    assert resp.status_code == status.HTTP_201_CREATED
    data = resp.json()
    assert data["name_en"] == "Smash Padel Court 1"
    assert data["area"] == "Salmiya"
    assert float(data["price_per_hour"]) == 15.5
    assert data["capacity"] == 4


def test_player_cannot_create_court(client, db_session):
    admin_token = register_and_get_token(client, db_session, "admin_c2@example.com", UserRole.ADMIN)
    player_token = register_and_get_token(client, db_session, "player_c2@example.com", UserRole.PLAYER)
    sport_id = create_test_sport(client, admin_token, "Padel 2", "padel-2")

    headers = {"Authorization": f"Bearer {player_token}"}
    court_payload = {
        "sport_id": sport_id,
        "name_en": "Player Court",
        "name_ar": "ملعب اللاعب",
        "area": "Hawally",
        "address": "Street 1",
        "price_per_hour": 10.0,
        "capacity": 2,
    }
    resp = client.post("/api/v1/courts", json=court_payload, headers=headers)
    assert resp.status_code == status.HTTP_403_FORBIDDEN


def test_price_and_capacity_positive_validation(client, db_session):
    admin_token = register_and_get_token(client, db_session, "admin_c3@example.com", UserRole.ADMIN)
    owner_token = register_and_get_token(client, db_session, "owner_c3@example.com", UserRole.OWNER)
    sport_id = create_test_sport(client, admin_token, "Football 1", "football-1")
    headers = {"Authorization": f"Bearer {owner_token}"}

    # Zero/negative price validation
    bad_price_payload = {
        "sport_id": sport_id,
        "name_en": "Bad Price Court",
        "name_ar": "ملعب سعر خاطئ",
        "area": "Salmiya",
        "address": "Street 1",
        "price_per_hour": -5.0,
        "capacity": 10,
    }
    resp1 = client.post("/api/v1/courts", json=bad_price_payload, headers=headers)
    assert resp1.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    # Zero/negative capacity validation
    bad_capacity_payload = {
        "sport_id": sport_id,
        "name_en": "Bad Capacity Court",
        "name_ar": "ملعب سعة خاطئة",
        "area": "Salmiya",
        "address": "Street 1",
        "price_per_hour": 10.0,
        "capacity": 0,
    }
    resp2 = client.post("/api/v1/courts", json=bad_capacity_payload, headers=headers)
    assert resp2.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_court_updates_permissions(client, db_session):
    admin_token = register_and_get_token(client, db_session, "admin_c4@example.com", UserRole.ADMIN)
    owner1_token = register_and_get_token(client, db_session, "owner1_c4@example.com", UserRole.OWNER)
    owner2_token = register_and_get_token(client, db_session, "owner2_c4@example.com", UserRole.OWNER)
    sport_id = create_test_sport(client, admin_token, "Tennis 1", "tennis-1")

    # Owner 1 creates court
    h1 = {"Authorization": f"Bearer {owner1_token}"}
    create_resp = client.post(
        "/api/v1/courts",
        json={
            "sport_id": sport_id,
            "name_en": "Owner 1 Tennis",
            "name_ar": "تنس المالك 1",
            "area": "Mishref",
            "address": "Block 1",
            "price_per_hour": 12.0,
            "capacity": 2,
        },
        headers=h1,
    )
    court_id = create_resp.json()["id"]

    # Owner 1 updates own court -> SUCCESS
    update_resp1 = client.patch(
        f"/api/v1/courts/{court_id}",
        json={"name_en": "Updated Owner 1 Tennis"},
        headers=h1,
    )
    assert update_resp1.status_code == status.HTTP_200_OK
    assert update_resp1.json()["name_en"] == "Updated Owner 1 Tennis"

    # Owner 2 attempts updating Owner 1's court -> FORBIDDEN
    h2 = {"Authorization": f"Bearer {owner2_token}"}
    update_resp2 = client.patch(
        f"/api/v1/courts/{court_id}",
        json={"name_en": "Hacked Court Name"},
        headers=h2,
    )
    assert update_resp2.status_code == status.HTTP_403_FORBIDDEN

    # Admin updates Owner 1's court -> SUCCESS
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    update_resp3 = client.patch(
        f"/api/v1/courts/{court_id}",
        json={"name_en": "Admin Modified Court"},
        headers=h_admin,
    )
    assert update_resp3.status_code == status.HTTP_200_OK
    assert update_resp3.json()["name_en"] == "Admin Modified Court"


def test_court_deletion_permissions(client, db_session):
    admin_token = register_and_get_token(client, db_session, "admin_c5@example.com", UserRole.ADMIN)
    owner1_token = register_and_get_token(client, db_session, "owner1_c5@example.com", UserRole.OWNER)
    player_token = register_and_get_token(client, db_session, "player_c5@example.com", UserRole.PLAYER)
    sport_id = create_test_sport(client, admin_token, "Basketball 1", "basketball-1")

    h1 = {"Authorization": f"Bearer {owner1_token}"}
    create_resp = client.post(
        "/api/v1/courts",
        json={
            "sport_id": sport_id,
            "name_en": "Basket Court",
            "name_ar": "ملعب سلة",
            "area": "Jabriya",
            "address": "Block 2",
            "price_per_hour": 20.0,
            "capacity": 10,
        },
        headers=h1,
    )
    court_id = create_resp.json()["id"]

    # Player attempts delete -> FORBIDDEN
    h_player = {"Authorization": f"Bearer {player_token}"}
    del_resp1 = client.delete(f"/api/v1/courts/{court_id}", headers=h_player)
    assert del_resp1.status_code == status.HTTP_403_FORBIDDEN

    # Owner deletes own court -> SUCCESS (204)
    del_resp2 = client.delete(f"/api/v1/courts/{court_id}", headers=h1)
    assert del_resp2.status_code == status.HTTP_204_NO_CONTENT

    # Fetch court -> 404
    get_resp = client.get(f"/api/v1/courts/{court_id}")
    assert get_resp.status_code == status.HTTP_404_NOT_FOUND


def test_court_filters_search_and_pagination(client, db_session):
    admin_token = register_and_get_token(client, db_session, "admin_c6@example.com", UserRole.ADMIN)
    owner_token = register_and_get_token(client, db_session, "owner_c6@example.com", UserRole.OWNER)
    sport1_id = create_test_sport(client, admin_token, "Padel 6", "padel-6")
    sport2_id = create_test_sport(client, admin_token, "Tennis 6", "tennis-6")
    h_owner = {"Authorization": f"Bearer {owner_token}"}

    client.post(
        "/api/v1/courts",
        json={
            "sport_id": sport1_id,
            "name_en": "Salmiya Arena Padel",
            "name_ar": "أرينا بادل السالمية",
            "area": "Salmiya",
            "address": "Street 5",
            "price_per_hour": 10.0,
            "capacity": 4,
        },
        headers=h_owner,
    )

    client.post(
        "/api/v1/courts",
        json={
            "sport_id": sport2_id,
            "name_en": "Hawally Tennis Hub",
            "name_ar": "مركز هولي للتنس",
            "area": "Hawally",
            "address": "Street 12",
            "price_per_hour": 25.0,
            "capacity": 2,
        },
        headers=h_owner,
    )

    # Filter by sport_id
    r_sport = client.get(f"/api/v1/courts?sport_id={sport1_id}")
    assert r_sport.status_code == status.HTTP_200_OK
    assert len(r_sport.json()) == 1
    assert r_sport.json()[0]["name_en"] == "Salmiya Arena Padel"

    # Filter by area
    r_area = client.get("/api/v1/courts?area=Hawally")
    assert r_area.status_code == status.HTTP_200_OK
    assert len(r_area.json()) == 1
    assert r_area.json()[0]["area"] == "Hawally"

    # Filter by price range
    r_price = client.get("/api/v1/courts?min_price=15.0&max_price=30.0")
    assert r_price.status_code == status.HTTP_200_OK
    assert len(r_price.json()) == 1
    assert float(r_price.json()[0]["price_per_hour"]) == 25.0

    # Search keyword
    r_search = client.get("/api/v1/courts?search=Salmiya")
    assert r_search.status_code == status.HTTP_200_OK
    assert len(r_search.json()) == 1

    # Pagination test
    r_page = client.get("/api/v1/courts?skip=0&limit=1")
    assert r_page.status_code == status.HTTP_200_OK
    assert len(r_page.json()) == 1
