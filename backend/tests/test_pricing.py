from datetime import date, datetime, time as dtime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi import status

from app.models.pricing import PricingRuleType
from app.models.user import UserRole
from app.models.court import Court


def register_user(client, db_session, email: str, role: UserRole = UserRole.PLAYER) -> tuple[int, str]:
    payload = {
        "email": email,
        "full_name": "Test User",
        "password": "Password123",
    }
    reg_resp = client.post("/api/v1/auth/register", json=payload)
    user_id = reg_resp.json()["id"]

    if role != UserRole.PLAYER:
        from app.models.user import User
        user = db_session.query(User).filter(User.id == user_id).first()
        user.role = role
        user.is_admin = (role == UserRole.ADMIN)
        db_session.commit()

    login_resp = client.post("/api/v1/auth/login", json={"email": email, "password": "Password123"})
    token = login_resp.json()["access_token"]
    return user_id, token


def create_court(client, db_session, token: str, price_per_hour: float = 10.0) -> int:
    headers = {"Authorization": f"Bearer {token}"}

    from app.models.sport import Sport
    sport = db_session.query(Sport).first()
    if not sport:
        sport = Sport(name_en="Padel", name_ar="بادل", slug="padel")
        db_session.add(sport)
        db_session.commit()
        db_session.refresh(sport)


    court_payload = {
        "sport_id": sport.id,
        "name_en": "Center Court",
        "name_ar": "الملعب الرئيسي",
        "area": "Salmiya",
        "address": "Block 5",
        "price_per_hour": price_per_hour,
        "capacity": 4,
    }
    resp = client.post("/api/v1/courts", json=court_payload, headers=headers)
    return resp.json()["id"]



def get_aligned_future_datetime(days_offset: int = 5, hour: int = 10, minute: int = 0) -> datetime:
    now_utc = datetime.now(timezone.utc)
    base = now_utc + timedelta(days=days_offset)
    # Convert to Kuwait local time (+3), adjust hour/minute, then back to UTC
    tz_offset = timedelta(hours=3)
    local_base = (base + tz_offset).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return (local_base - tz_offset).astimezone(timezone.utc)


# 1. Court with no pricing rules uses base price
def test_no_rules_uses_base_price(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p1@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
    )
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert float(data["total"]) == 10.0
    assert float(data["base_price_per_hour"]) == 10.0


# 2. Ninety-minute booking is priced proportionally
def test_ninety_minute_booking_proportional_price(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p2@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(minutes=90)  # 1.5 hours * 10.0 = 15.0

    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
    )
    assert r.status_code == status.HTTP_200_OK
    assert float(r.json()["total"]) == 15.0


# 3. Admin can create a pricing rule
def test_admin_can_create_pricing_rule(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p3@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    r = client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={
            "name": "Peak Evening",
            "rule_type": "fixed_hourly_price",
            "starts_at": "18:00:00",
            "ends_at": "22:00:00",
            "value": 15.0,
            "priority": 10,
        },
        headers=h_admin,
    )
    assert r.status_code == status.HTTP_201_CREATED
    assert r.json()["name"] == "Peak Evening"


# 4. Court owner can create a pricing rule for their court
def test_owner_can_create_pricing_rule(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p4@example.com", UserRole.ADMIN)
    owner_id, owner_token = register_user(client, db_session, "owner_p4@example.com", UserRole.OWNER)

    court_id = create_court(client, db_session, admin_token)
    db_session.query(Court).filter(Court.id == court_id).update({"owner_id": owner_id})
    db_session.commit()
    db_session.expire_all()

    h_owner = {"Authorization": f"Bearer {owner_token}"}
    r = client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={
            "name": "Weekend Special",
            "rule_type": "percentage_adjustment",
            "weekday": 4,
            "value": 20.0,
        },
        headers=h_owner,
    )
    assert r.status_code == status.HTTP_201_CREATED


# 5. Court owner cannot modify another owner’s court
def test_owner_cannot_modify_other_owner_court(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p5@example.com", UserRole.ADMIN)
    o1_id, o1_token = register_user(client, db_session, "o1_p5@example.com", UserRole.OWNER)
    _, o2_token = register_user(client, db_session, "o2_p5@example.com", UserRole.OWNER)

    court_id = create_court(client, db_session, admin_token)
    db_session.query(Court).filter(Court.id == court_id).update({"owner_id": o1_id})
    db_session.commit()
    db_session.expire_all()

    h_o2 = {"Authorization": f"Bearer {o2_token}"}
    r = client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Hacker Rule", "rule_type": "fixed_hourly_price", "value": 1.0},
        headers=h_o2,
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


# 6. Normal user cannot create pricing rules
def test_player_cannot_create_pricing_rules(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p6@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_p6@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token)

    h_user = {"Authorization": f"Bearer {user_token}"}
    r = client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Player Rule", "rule_type": "fixed_hourly_price", "value": 5.0},
        headers=h_user,
    )
    assert r.status_code == status.HTTP_403_FORBIDDEN


# 7. Fixed hourly pricing rule works
def test_fixed_hourly_price_rule(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p7@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Flat Peak", "rule_type": "fixed_hourly_price", "value": 15.0},
        headers=h_admin,
    )

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
    )
    assert float(r.json()["total"]) == 15.0


# 8. Percentage increase works
def test_percentage_increase_rule(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p8@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "20 Percent Surge", "rule_type": "percentage_adjustment", "value": 20.0},
        headers=h_admin,
    )

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
    )
    assert float(r.json()["total"]) == 12.0


# 9. Percentage discount works
def test_percentage_discount_rule(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p9@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "10 Percent Discount", "rule_type": "percentage_adjustment", "value": -10.0},
        headers=h_admin,
    )

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
    )
    assert float(r.json()["total"]) == 9.0


# 10. Fixed hourly adjustment works
def test_fixed_hourly_adjustment_rule(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p10@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Add 2.5 KD", "rule_type": "fixed_hourly_adjustment", "value": 2.5},
        headers=h_admin,
    )

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
    )
    assert float(r.json()["total"]) == 12.5


# 11. Final hourly rate cannot become negative
def test_final_hourly_rate_floored_at_zero(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p11@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Huge Discount", "rule_type": "fixed_hourly_adjustment", "value": -50.0},
        headers=h_admin,
    )

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
    )
    assert float(r.json()["total"]) == 0.0


# 12 & 13. Weekday-specific rule vs null weekday (applies every day)
def test_weekday_specific_rule(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p12@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    # Friday is weekday 4
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Friday Surge", "rule_type": "fixed_hourly_price", "weekday": 4, "value": 20.0},
        headers=h_admin,
    )

    tz_offset = timedelta(hours=3)
    now_utc = datetime.now(timezone.utc)
    # Find next Friday in local time
    local_now = now_utc + tz_offset
    days_to_fri = (4 - local_now.weekday()) % 7
    if days_to_fri == 0:
        days_to_fri = 7

    fri_local = (local_now + timedelta(days=days_to_fri)).replace(hour=10, minute=0, second=0, microsecond=0)
    fri_utc = (fri_local - tz_offset).astimezone(timezone.utc)

    # Friday quote
    r_fri = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": fri_utc.isoformat(), "end_time": (fri_utc + timedelta(hours=1)).isoformat()},
    )
    assert float(r_fri.json()["total"]) == 20.0

    # Thursday quote (weekday 3)
    thu_utc = fri_utc - timedelta(days=1)
    r_thu = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": thu_utc.isoformat(), "end_time": (thu_utc + timedelta(hours=1)).isoformat()},
    )
    assert float(r_thu.json()["total"]) == 10.0


# 14. All-day rule works
def test_all_day_rule_applies(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p14@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "All Day Increase", "rule_type": "fixed_hourly_price", "starts_at": None, "ends_at": None, "value": 18.0},
        headers=h_admin,
    )

    start_t = get_aligned_future_datetime(days_offset=5, hour=14, minute=0)
    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()},
    )
    assert float(r.json()["total"]) == 18.0


# 15. Inactive rule is ignored
def test_inactive_rule_ignored(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p15@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Inactive Rule", "rule_type": "fixed_hourly_price", "value": 50.0, "is_active": False},
        headers=h_admin,
    )

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()},
    )
    assert float(r.json()["total"]) == 10.0


# 16 & 17. valid_from and valid_until enforcement
def test_validity_date_range_enforcement(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p16@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    today = date.today()
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={
            "name": "Summer Special",
            "rule_type": "fixed_hourly_price",
            "value": 25.0,
            "valid_from": (today + timedelta(days=10)).isoformat(),
            "valid_until": (today + timedelta(days=20)).isoformat(),
        },
        headers=h_admin,
    )

    # Day 5 (before valid_from) -> base 10.0
    start_before = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    r_before = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_before.isoformat(), "end_time": (start_before + timedelta(hours=1)).isoformat()},
    )
    assert float(r_before.json()["total"]) == 10.0

    # Day 15 (inside valid range) -> 25.0
    start_inside = get_aligned_future_datetime(days_offset=15, hour=10, minute=0)
    r_inside = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_inside.isoformat(), "end_time": (start_inside + timedelta(hours=1)).isoformat()},
    )
    assert float(r_inside.json()["total"]) == 25.0


# 18 & 19. Rule priority and deterministic execution order
def test_rule_priority_order(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p18@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}

    # Priority 0: Fixed price 15.0
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Flat Peak", "rule_type": "fixed_hourly_price", "value": 15.0, "priority": 0},
        headers=h_admin,
    )
    # Priority 10: Percentage discount -10%
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Promo Discount", "rule_type": "percentage_adjustment", "value": -10.0, "priority": 10},
        headers=h_admin,
    )

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()},
    )
    # Base 10 -> Priority 0 replaces with 15.0 -> Priority 10 discounts by 10% = 13.5
    assert float(r.json()["total"]) == 13.5


# 20. Evening peak rule works
def test_evening_peak_rule(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p20@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={
            "name": "Evening Peak",
            "rule_type": "fixed_hourly_price",
            "starts_at": "18:00:00",
            "ends_at": "23:00:00",
            "value": 15.0,
        },
        headers=h_admin,
    )

    # 19:00 -> 20:00 local time
    start_t = get_aligned_future_datetime(days_offset=5, hour=19, minute=0)
    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()},
    )
    assert float(r.json()["total"]) == 15.0


# 21 & 22. Overnight pricing rule works before and after midnight
def test_overnight_pricing_rule(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p21@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    # Thursday (weekday 3) overnight rule: 22:00 -> 02:00
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={
            "name": "Thu Night Owl",
            "rule_type": "fixed_hourly_price",
            "weekday": 3,
            "starts_at": "22:00:00",
            "ends_at": "02:00:00",
            "value": 18.0,
        },
        headers=h_admin,
    )

    tz_offset = timedelta(hours=3)
    local_now = datetime.now(timezone.utc) + tz_offset
    days_to_thu = (3 - local_now.weekday()) % 7
    if days_to_thu == 0:
        days_to_thu = 7

    # Thursday 23:00 local time (before midnight)
    thu_before_mid_local = (local_now + timedelta(days=days_to_thu)).replace(hour=23, minute=0, second=0, microsecond=0)
    thu_before_mid_utc = (thu_before_mid_local - tz_offset).astimezone(timezone.utc)

    r_before = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": thu_before_mid_utc.isoformat(), "end_time": (thu_before_mid_utc + timedelta(hours=1)).isoformat()},
    )
    assert float(r_before.json()["total"]) == 18.0

    # Friday 00:30 local time (after midnight, part of Thursday overnight)
    fri_after_mid_local = (thu_before_mid_local + timedelta(hours=1, minutes=30)).replace(minute=30)
    fri_after_mid_utc = (fri_after_mid_local - tz_offset).astimezone(timezone.utc)

    r_after = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": fri_after_mid_utc.isoformat(), "end_time": (fri_after_mid_utc + timedelta(hours=1)).isoformat()},
    )
    assert float(r_after.json()["total"]) == 18.0


# 23. Booking spanning base and peak rates is split correctly
def test_multi_segment_booking_split(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p23@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={
            "name": "Evening Peak",
            "rule_type": "fixed_hourly_price",
            "starts_at": "18:00:00",
            "ends_at": "22:00:00",
            "value": 15.0,
        },
        headers=h_admin,
    )

    # 17:30 -> 19:30 local time (30 mins @ 10.0 + 90 mins @ 15.0 = 5.0 + 22.5 = 27.5)
    start_t = get_aligned_future_datetime(days_offset=5, hour=17, minute=30)
    end_t = start_t + timedelta(hours=2)

    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
    )
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert float(data["total"]) == 27.5
    assert len(data["segments"]) == 2


# 24. Booking crossing midnight is split correctly
def test_booking_crossing_midnight_split(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p24@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    # 23:30 to 00:30 local time
    start_t = get_aligned_future_datetime(days_offset=5, hour=23, minute=30)
    end_t = start_t + timedelta(hours=1)

    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
    )
    assert r.status_code == status.HTTP_200_OK
    assert len(r.json()["segments"]) == 2


# 25 & 26. Date override fixed price and percentage adjustment
def test_date_price_override(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p25@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    tz_offset = timedelta(hours=3)
    target_date = (datetime.now(timezone.utc) + timedelta(days=6) + tz_offset).date()

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/date-overrides",
        json={
            "name": "National Day Holiday",
            "local_date": target_date.isoformat(),
            "override_type": "fixed_hourly_price",
            "value": 30.0,
            "priority": 100,
        },
        headers=h_admin,
    )

    start_t = get_aligned_future_datetime(days_offset=6, hour=10, minute=0)
    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()},
    )
    assert float(r.json()["total"]) == 30.0


# 27. Recurring and date rules combine by priority
def test_recurring_and_date_override_combine_by_priority(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p27@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    tz_offset = timedelta(hours=3)
    target_date = (datetime.now(timezone.utc) + timedelta(days=6) + tz_offset).date()

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    # Priority 10: Recurring peak 15.0
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Peak Rate", "rule_type": "fixed_hourly_price", "value": 15.0, "priority": 10},
        headers=h_admin,
    )
    # Priority 100: Holiday +25%
    client.post(
        f"/api/v1/courts/{court_id}/pricing/date-overrides",
        json={"name": "Holiday Increase", "local_date": target_date.isoformat(), "override_type": "percentage_adjustment", "value": 25.0, "priority": 100},
        headers=h_admin,
    )

    start_t = get_aligned_future_datetime(days_offset=6, hour=10, minute=0)
    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": (start_t + timedelta(hours=1)).isoformat()},
    )
    # Base 10 -> Priority 10 sets 15.0 -> Priority 100 adds +25% = 18.750
    assert float(r.json()["total"]) == 18.75


# 28 & 29. Date override update and deletion
def test_date_override_update_and_delete(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p28@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    r_create = client.post(
        f"/api/v1/courts/{court_id}/pricing/date-overrides",
        json={"name": "Festival", "local_date": "2026-08-15", "override_type": "fixed_hourly_price", "value": 20.0},
        headers=h_admin,
    )
    ov_id = r_create.json()["id"]

    # Update
    r_patch = client.patch(
        f"/api/v1/courts/{court_id}/pricing/date-overrides/{ov_id}",
        json={"value": 25.0},
        headers=h_admin,
    )
    assert float(r_patch.json()["value"]) == 25.0

    # Delete
    r_del = client.delete(f"/api/v1/courts/{court_id}/pricing/date-overrides/{ov_id}", headers=h_admin)
    assert r_del.status_code == status.HTTP_204_NO_CONTENT


# 30 & 31. Pricing rule update and deletion
def test_pricing_rule_update_and_delete(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p30@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    r_create = client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Temp Rule", "rule_type": "fixed_hourly_price", "value": 12.0},
        headers=h_admin,
    )
    rule_id = r_create.json()["id"]

    # Update
    r_patch = client.patch(
        f"/api/v1/courts/{court_id}/pricing/rules/{rule_id}",
        json={"name": "Updated Rule", "value": 14.0},
        headers=h_admin,
    )
    assert r_patch.json()["name"] == "Updated Rule"

    # Delete
    r_del = client.delete(f"/api/v1/courts/{court_id}/pricing/rules/{rule_id}", headers=h_admin)
    assert r_del.status_code == status.HTTP_204_NO_CONTENT


# 32 & 33 & 34. Price quote API details & informational non-persistence
def test_price_quote_informational_response(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p32@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
    )
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert data["court_id"] == court_id
    assert "available" in data
    assert "disclaimer" in data

    # Verify no booking was created
    from app.models.booking import Booking
    assert db_session.query(Booking).filter(Booking.court_id == court_id).count() == 0


# 35 & 36 & 37 & 38. Booking stores base price, total price, currency, breakdown snapshots
def test_booking_stores_pricing_snapshots(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p35@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_p35@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    h_user = {"Authorization": f"Bearer {user_token}"}
    r = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
        headers=h_user,
    )
    assert r.status_code == status.HTTP_201_CREATED
    data = r.json()
    assert float(data["total_price"]) == 10.0
    assert float(data["base_price_per_hour"]) == 10.0
    assert data["currency"] == "KWD"
    assert data["pricing_breakdown"] is not None


# 39. Historical booking price does not change after rule update
def test_historical_booking_price_immutable_after_rule_change(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p39@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_p39@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    # 1. Create booking at base 10.0
    h_user = {"Authorization": f"Bearer {user_token}"}
    r_b = client.post(
        "/api/v1/bookings",
        json={"court_id": court_id, "start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
        headers=h_user,
    )
    booking_id = r_b.json()["id"]

    # 2. Admin adds rule that doubles price
    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Surge Rule", "rule_type": "fixed_hourly_price", "value": 50.0},
        headers=h_admin,
    )

    # 3. Read historical booking
    r_get = client.get(f"/api/v1/bookings/{booking_id}", headers=h_user)
    assert float(r_get.json()["total_price"]) == 10.0


# 40. Client-supplied price is ignored or rejected safely
def test_client_supplied_price_ignored(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p40@example.com", UserRole.ADMIN)
    _, user_token = register_user(client, db_session, "user_p40@example.com", UserRole.PLAYER)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(hours=1)

    h_user = {"Authorization": f"Bearer {user_token}"}
    # Client tries to pass total_price = 0.001
    payload = {"court_id": court_id, "start_time": start_t.isoformat(), "end_time": end_t.isoformat(), "total_price": 0.001}
    r = client.post("/api/v1/bookings", json=payload, headers=h_user)
    assert r.status_code == status.HTTP_201_CREATED
    assert float(r.json()["total_price"]) == 10.0  # Server calculated price enforced


# 41. Available slots include calculated total price
def test_available_slots_includes_calculated_price(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p41@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Surge", "rule_type": "fixed_hourly_price", "value": 20.0},
        headers=h_admin,
    )

    tz_offset = timedelta(hours=3)
    target_date = (datetime.now(timezone.utc) + timedelta(days=6) + tz_offset).date().isoformat()

    r = client.get(f"/api/v1/courts/{court_id}/available-slots?date={target_date}&duration_minutes=60")
    assert r.status_code == status.HTTP_200_OK
    slots = r.json()["slots"]
    assert len(slots) > 0
    assert float(slots[0]["total_price"]) == 20.0


# 42. All monetary results use three decimal places
def test_three_decimal_places_monetary_precision(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p42@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    start_t = get_aligned_future_datetime(days_offset=5, hour=10, minute=0)
    end_t = start_t + timedelta(minutes=45)  # 0.75 hours * 10 = 7.500

    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_t.isoformat(), "end_time": end_t.isoformat()},
    )
    assert r.status_code == status.HTTP_200_OK
    assert str(r.json()["total"]) == "7.500"


# 43. Naive datetimes are rejected
def test_naive_datetime_quote_rejected(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p43@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token)

    r = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": "2026-08-10T10:00:00", "end_time": "2026-08-10T11:00:00"},
    )
    assert r.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


# 44. Invalid date range is rejected
def test_invalid_validity_date_range_rejected(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p44@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    r = client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={
            "name": "Invalid Dates",
            "rule_type": "fixed_hourly_price",
            "value": 15.0,
            "valid_from": "2026-08-20",
            "valid_until": "2026-08-10",
        },
        headers=h_admin,
    )
    assert r.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


# 45. Invalid rule type is rejected
def test_invalid_rule_type_rejected(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p45@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    r = client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Bad Type", "rule_type": "invalid_type", "value": 15.0},
        headers=h_admin,
    )
    assert r.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


# 46. Negative fixed hourly price is rejected
def test_negative_fixed_price_rejected(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p46@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    r = client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={"name": "Negative Price", "rule_type": "fixed_hourly_price", "value": -10.0},
        headers=h_admin,
    )
    assert r.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY]


# 47 & 48. Exact boundary at rule start and end
def test_exact_rule_boundaries(client, db_session):
    _, admin_token = register_user(client, db_session, "admin_p47@example.com", UserRole.ADMIN)
    court_id = create_court(client, db_session, admin_token, price_per_hour=10.0)

    h_admin = {"Authorization": f"Bearer {admin_token}"}
    client.post(
        f"/api/v1/courts/{court_id}/pricing/rules",
        json={
            "name": "Peak 18 to 20",
            "rule_type": "fixed_hourly_price",
            "starts_at": "18:00:00",
            "ends_at": "20:00:00",
            "value": 15.0,
        },
        headers=h_admin,
    )

    # 18:00 -> 19:00 (exact start boundary) -> 15.0
    start_exact = get_aligned_future_datetime(days_offset=5, hour=18, minute=0)
    r1 = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": start_exact.isoformat(), "end_time": (start_exact + timedelta(hours=1)).isoformat()},
    )
    assert float(r1.json()["total"]) == 15.0

    # 20:00 -> 21:00 (exact end boundary stops using rule) -> base 10.0
    end_exact = get_aligned_future_datetime(days_offset=5, hour=20, minute=0)
    r2 = client.post(
        f"/api/v1/courts/{court_id}/price-quote",
        json={"start_time": end_exact.isoformat(), "end_time": (end_exact + timedelta(hours=1)).isoformat()},
    )
    assert float(r2.json()["total"]) == 10.0


# 49. Migration has one Alembic head
def test_single_alembic_head():
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    alembic_cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(alembic_cfg)
    heads = script.get_heads()
    assert len(heads) == 1
    assert heads[0] == "e4f5a6b7c8d9"
