"""
Milestone 7 — Court Owner Management Tests.

Covers:
  - Only OWNER / ADMIN role users can access /owner/* endpoints
  - Players are rejected with 403
  - Owners can only manage their own courts
  - Owners cannot access another owner's courts (403)
  - Admins can access any court
  - Court active/inactive toggle
  - Inactive courts hidden from public availability list (is_active filter)
  - Owner can list bookings on own court
  - Owner cannot see bookings on another owner's court
  - Owner dashboard summary
"""

from fastapi import status

from app.models.user import User, UserRole


# ── helpers ──────────────────────────────────────────────────────────────────


def _register_and_login(client, db_session, email: str, role: UserRole) -> tuple[int, str]:
    """Register a user, optionally set role in DB, return (user_id, access_token)."""
    reg = client.post(
        "/api/v1/auth/register",
        json={"email": email, "full_name": f"{role.value} user", "password": "Pass1234"},
    )
    assert reg.status_code == 201
    user_id = reg.json()["id"]

    if role != UserRole.PLAYER:
        u = db_session.query(User).filter(User.id == user_id).first()
        u.role = role
        u.is_admin = role == UserRole.ADMIN
        db_session.commit()

    login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Pass1234"},
    )
    assert login.status_code == 200
    return user_id, login.json()["access_token"]


def _auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def _create_sport(client, admin_token: str, slug: str) -> int:
    r = client.post(
        "/api/v1/sports",
        json={"name_en": slug, "name_ar": slug, "slug": slug},
        headers=_auth(admin_token),
    )
    assert r.status_code == 201
    return r.json()["id"]


def _owner_create_court(client, token: str, sport_id: int, name_suffix: str = "1") -> dict:
    payload = {
        "sport_id": sport_id,
        "name_en": f"Court {name_suffix}",
        "name_ar": f"ملعب {name_suffix}",
        "area": "Salmiya",
        "address": f"Block {name_suffix}",
        "price_per_hour": 10.0,
        "capacity": 4,
    }
    r = client.post("/api/v1/owner/courts", json=payload, headers=_auth(token))
    return r


# ── RBAC: players rejected ────────────────────────────────────────────────────


def test_player_cannot_access_owner_courts(client, db_session):
    _, admin_token = _register_and_login(client, db_session, "adm_rbac@x.com", UserRole.ADMIN)
    _, player_token = _register_and_login(client, db_session, "ply_rbac@x.com", UserRole.PLAYER)
    sport_id = _create_sport(client, admin_token, "futsal-rbac")

    r = _owner_create_court(client, player_token, sport_id, "P1")
    assert r.status_code == status.HTTP_403_FORBIDDEN

    r = client.get("/api/v1/owner/courts", headers=_auth(player_token))
    assert r.status_code == status.HTTP_403_FORBIDDEN

    r = client.get("/api/v1/owner/dashboard", headers=_auth(player_token))
    assert r.status_code == status.HTTP_403_FORBIDDEN


# ── Owner: create and list own courts ─────────────────────────────────────────


def test_owner_create_and_list_courts(client, db_session):
    _, admin_token = _register_and_login(client, db_session, "adm_cl@x.com", UserRole.ADMIN)
    _, owner_token = _register_and_login(client, db_session, "own_cl@x.com", UserRole.OWNER)
    sport_id = _create_sport(client, admin_token, "padel-cl")

    r = _owner_create_court(client, owner_token, sport_id, "A")
    assert r.status_code == 201
    court_id = r.json()["id"]
    assert r.json()["name_en"] == "Court A"

    r2 = client.get("/api/v1/owner/courts", headers=_auth(owner_token))
    assert r2.status_code == 200
    ids = [c["id"] for c in r2.json()]
    assert court_id in ids


# ── Owner: cannot see other owner's court ─────────────────────────────────────


def test_owner_cannot_access_other_owners_court(client, db_session):
    _, admin_token = _register_and_login(client, db_session, "adm_iso@x.com", UserRole.ADMIN)
    _, owner1_token = _register_and_login(client, db_session, "own1_iso@x.com", UserRole.OWNER)
    _, owner2_token = _register_and_login(client, db_session, "own2_iso@x.com", UserRole.OWNER)
    sport_id = _create_sport(client, admin_token, "tennis-iso")

    # owner1 creates a court
    r = _owner_create_court(client, owner1_token, sport_id, "O1")
    assert r.status_code == 201
    court_id = r.json()["id"]

    # owner2 cannot get that court via owner endpoint
    r_get = client.get(f"/api/v1/owner/courts/{court_id}", headers=_auth(owner2_token))
    assert r_get.status_code == status.HTTP_403_FORBIDDEN

    # owner2 cannot update it
    r_patch = client.patch(
        f"/api/v1/owner/courts/{court_id}",
        json={"name_en": "Hacked"},
        headers=_auth(owner2_token),
    )
    assert r_patch.status_code == status.HTTP_403_FORBIDDEN

    # owner2 cannot delete it
    r_del = client.delete(f"/api/v1/owner/courts/{court_id}", headers=_auth(owner2_token))
    assert r_del.status_code == status.HTTP_403_FORBIDDEN


# ── Admin can access any owner's court via /owner endpoints ──────────────────


def test_admin_can_access_all_owner_courts(client, db_session):
    _, admin_token = _register_and_login(client, db_session, "adm_any@x.com", UserRole.ADMIN)
    _, owner_token = _register_and_login(client, db_session, "own_any@x.com", UserRole.OWNER)
    sport_id = _create_sport(client, admin_token, "volleyball-any")

    r = _owner_create_court(client, owner_token, sport_id, "V1")
    assert r.status_code == 201
    court_id = r.json()["id"]

    # Admin retrieves the court
    r_get = client.get(f"/api/v1/owner/courts/{court_id}", headers=_auth(admin_token))
    assert r_get.status_code == 200
    assert r_get.json()["id"] == court_id


# ── Toggle active/inactive ────────────────────────────────────────────────────


def test_owner_toggle_court_active(client, db_session):
    _, admin_token = _register_and_login(client, db_session, "adm_tog@x.com", UserRole.ADMIN)
    _, owner_token = _register_and_login(client, db_session, "own_tog@x.com", UserRole.OWNER)
    sport_id = _create_sport(client, admin_token, "badminton-tog")

    r = _owner_create_court(client, owner_token, sport_id, "T1")
    assert r.status_code == 201
    court_id = r.json()["id"]
    assert r.json()["is_active"] is True

    # Deactivate
    r2 = client.patch(f"/api/v1/owner/courts/{court_id}/toggle-active", headers=_auth(owner_token))
    assert r2.status_code == 200
    assert r2.json()["is_active"] is False

    # Reactivate
    r3 = client.patch(f"/api/v1/owner/courts/{court_id}/toggle-active", headers=_auth(owner_token))
    assert r3.status_code == 200
    assert r3.json()["is_active"] is True


def test_inactive_court_hidden_from_public_active_filter(client, db_session):
    """When is_active=True is applied in the public list, deactivated courts vanish."""
    _, admin_token = _register_and_login(client, db_session, "adm_hide@x.com", UserRole.ADMIN)
    _, owner_token = _register_and_login(client, db_session, "own_hide@x.com", UserRole.OWNER)
    sport_id = _create_sport(client, admin_token, "squash-hide")

    r = _owner_create_court(client, owner_token, sport_id, "H1")
    assert r.status_code == 201
    court_id = r.json()["id"]

    # Deactivate via owner endpoint
    r_tog = client.patch(f"/api/v1/owner/courts/{court_id}/toggle-active", headers=_auth(owner_token))
    assert r_tog.status_code == 200

    # Public court list with is_active=true should not contain it
    r_pub = client.get("/api/v1/courts?is_active=true")
    assert r_pub.status_code == 200
    public_ids = [c["id"] for c in r_pub.json()]
    assert court_id not in public_ids


# ── Owner-specific court list shows only own courts ───────────────────────────


def test_owner_list_shows_only_own_courts(client, db_session):
    _, admin_token = _register_and_login(client, db_session, "adm_lst@x.com", UserRole.ADMIN)
    _, owner1_token = _register_and_login(client, db_session, "own1_lst@x.com", UserRole.OWNER)
    _, owner2_token = _register_and_login(client, db_session, "own2_lst@x.com", UserRole.OWNER)
    sport_id = _create_sport(client, admin_token, "football-lst")

    r1 = _owner_create_court(client, owner1_token, sport_id, "L1")
    r2 = _owner_create_court(client, owner2_token, sport_id, "L2")
    court1_id = r1.json()["id"]
    court2_id = r2.json()["id"]

    # owner1 list → only court1
    list1 = client.get("/api/v1/owner/courts", headers=_auth(owner1_token)).json()
    ids1 = [c["id"] for c in list1]
    assert court1_id in ids1
    assert court2_id not in ids1

    # owner2 list → only court2
    list2 = client.get("/api/v1/owner/courts", headers=_auth(owner2_token)).json()
    ids2 = [c["id"] for c in list2]
    assert court2_id in ids2
    assert court1_id not in ids2


# ── Owner bookings: visibility ────────────────────────────────────────────────


def test_owner_list_court_bookings(client, db_session):
    """Owner can list bookings on their court; another owner cannot."""
    _, admin_token = _register_and_login(client, db_session, "adm_bk@x.com", UserRole.ADMIN)
    _, owner1_token = _register_and_login(client, db_session, "own1_bk@x.com", UserRole.OWNER)
    _, owner2_token = _register_and_login(client, db_session, "own2_bk@x.com", UserRole.OWNER)
    _, player_token = _register_and_login(client, db_session, "ply_bk@x.com", UserRole.PLAYER)
    sport_id = _create_sport(client, admin_token, "basketball-bk")

    r = _owner_create_court(client, owner1_token, sport_id, "BK1")
    assert r.status_code == 201
    court_id = r.json()["id"]

    # owner1 can list bookings (empty for now)
    r_own1 = client.get(f"/api/v1/owner/courts/{court_id}/bookings", headers=_auth(owner1_token))
    assert r_own1.status_code == 200
    assert isinstance(r_own1.json(), list)

    # owner2 cannot list bookings on owner1's court
    r_own2 = client.get(f"/api/v1/owner/courts/{court_id}/bookings", headers=_auth(owner2_token))
    assert r_own2.status_code == status.HTTP_403_FORBIDDEN

    # player cannot access owner bookings endpoint
    r_ply = client.get(f"/api/v1/owner/courts/{court_id}/bookings", headers=_auth(player_token))
    assert r_ply.status_code == status.HTTP_403_FORBIDDEN


# ── Dashboard ─────────────────────────────────────────────────────────────────


def test_owner_dashboard(client, db_session):
    _, admin_token = _register_and_login(client, db_session, "adm_dash@x.com", UserRole.ADMIN)
    _, owner_token = _register_and_login(client, db_session, "own_dash@x.com", UserRole.OWNER)
    sport_id = _create_sport(client, admin_token, "hockey-dash")

    _owner_create_court(client, owner_token, sport_id, "D1")
    _owner_create_court(client, owner_token, sport_id, "D2")

    r = client.get("/api/v1/owner/dashboard", headers=_auth(owner_token))
    assert r.status_code == 200
    data = r.json()
    assert data["total_courts"] == 2
    assert data["active_courts"] == 2
    assert data["inactive_courts"] == 0
    assert "bookings_by_status" in data


def test_owner_dashboard_reflects_deactivation(client, db_session):
    _, admin_token = _register_and_login(client, db_session, "adm_dactv@x.com", UserRole.ADMIN)
    _, owner_token = _register_and_login(client, db_session, "own_dactv@x.com", UserRole.OWNER)
    sport_id = _create_sport(client, admin_token, "rugby-dactv")

    r = _owner_create_court(client, owner_token, sport_id, "R1")
    court_id = r.json()["id"]

    client.patch(f"/api/v1/owner/courts/{court_id}/toggle-active", headers=_auth(owner_token))

    r_dash = client.get("/api/v1/owner/dashboard", headers=_auth(owner_token))
    data = r_dash.json()
    assert data["inactive_courts"] == 1
    assert data["active_courts"] == 0


# ── Update ────────────────────────────────────────────────────────────────────


def test_owner_update_own_court(client, db_session):
    _, admin_token = _register_and_login(client, db_session, "adm_upd@x.com", UserRole.ADMIN)
    _, owner_token = _register_and_login(client, db_session, "own_upd@x.com", UserRole.OWNER)
    sport_id = _create_sport(client, admin_token, "golf-upd")

    r = _owner_create_court(client, owner_token, sport_id, "G1")
    court_id = r.json()["id"]

    r2 = client.patch(
        f"/api/v1/owner/courts/{court_id}",
        json={"name_en": "Golf Court Updated", "price_per_hour": 25.0},
        headers=_auth(owner_token),
    )
    assert r2.status_code == 200
    assert r2.json()["name_en"] == "Golf Court Updated"
    assert float(r2.json()["price_per_hour"]) == 25.0


# ── Delete ────────────────────────────────────────────────────────────────────


def test_owner_delete_own_court(client, db_session):
    _, admin_token = _register_and_login(client, db_session, "adm_del@x.com", UserRole.ADMIN)
    _, owner_token = _register_and_login(client, db_session, "own_del@x.com", UserRole.OWNER)
    sport_id = _create_sport(client, admin_token, "cricket-del")

    r = _owner_create_court(client, owner_token, sport_id, "C1")
    court_id = r.json()["id"]

    r_del = client.delete(f"/api/v1/owner/courts/{court_id}", headers=_auth(owner_token))
    assert r_del.status_code == status.HTTP_204_NO_CONTENT

    # Verify gone
    r_get = client.get(f"/api/v1/owner/courts/{court_id}", headers=_auth(owner_token))
    assert r_get.status_code == status.HTTP_404_NOT_FOUND
