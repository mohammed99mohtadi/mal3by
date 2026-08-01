"""
Owner Management Router — Milestone 7.

All endpoints here are restricted to authenticated users with
UserRole.OWNER (or UserRole.ADMIN).  Owners may only access and
mutate resources that belong to them.  Admins may access any
resource in every endpoint.
"""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.api.dependencies import get_current_user, require_owner
from app.db.session import get_db
from app.models.booking import Booking, BookingStatus
from app.models.court import Court
from app.models.user import User, UserRole
from app.schemas.availability import (
    CourtAvailabilityRuleCreate,
    CourtAvailabilityRuleRead,
    CourtAvailabilityRuleUpdate,
    CourtClosureCreate,
    CourtClosureRead,
    CourtClosureUpdate,
    CourtWorkingHoursCreate,
    CourtWorkingHoursRead,
)
from app.schemas.booking import BookingRead, BookingStatusUpdate
from app.schemas.court import CourtCreate, CourtResponse, CourtUpdate
from app.schemas.pricing import (
    CourtDatePriceOverrideCreate,
    CourtDatePriceOverrideRead,
    CourtDatePriceOverrideUpdate,
    CourtPricingRuleCreate,
    CourtPricingRuleRead,
    CourtPricingRuleUpdate,
)
from app.services.availability_service import (
    create_court_closure,
    delete_court_closure,
    delete_working_hours,
    get_or_create_availability_rule,
    list_court_closures,
    list_working_hours,
    update_availability_rule,
    update_court_closure,
    upsert_working_hours,
)
from app.services.booking_service import (
    get_booking_by_id,
    update_booking_status,
)
from app.services.court_service import (
    create_court,
    delete_court,
    get_court_by_id,
    get_courts,
    update_court,
)
from app.services.pricing_service import (
    create_date_override,
    create_pricing_rule,
    delete_date_override,
    delete_pricing_rule,
    get_date_override,
    get_pricing_rule,
    list_date_overrides,
    list_pricing_rules,
    update_date_override,
    update_pricing_rule,
)

router = APIRouter()


# ── helpers ──────────────────────────────────────────────────────────────────


def _is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN or user.is_admin


def _resolve_court(db: Session, court_id: int, current_user: User) -> Court:
    """Return the court if it exists and belongs to the caller (or caller is admin)."""
    court = get_court_by_id(db=db, court_id=court_id)
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court with id {court_id} not found",
        )
    if not (_is_admin(current_user) or court.owner_id == current_user.id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to manage this court",
        )
    return court


# ── Court CRUD ────────────────────────────────────────────────────────────────


@router.post("/courts", response_model=CourtResponse, status_code=status.HTTP_201_CREATED)
def owner_create_court(
    court_in: CourtCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Create a new court owned by the authenticated owner."""
    return create_court(db=db, court_in=court_in, owner_id=current_user.id)


@router.get("/courts", response_model=list[CourtResponse])
def owner_list_courts(
    is_active: bool | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """List courts owned by the authenticated owner (admins see all courts)."""
    if _is_admin(current_user):
        # Admins may list every court without ownership restriction
        return get_courts(db=db, is_active=is_active, skip=skip, limit=limit)

    query = select(Court).where(Court.owner_id == current_user.id)
    if is_active is not None:
        query = query.where(Court.is_active == is_active)
    query = query.offset(skip).limit(limit)
    return list(db.execute(query).scalars().all())


@router.get("/courts/{court_id}", response_model=CourtResponse)
def owner_get_court(
    court_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Get a single court owned by the authenticated owner."""
    return _resolve_court(db=db, court_id=court_id, current_user=current_user)


@router.patch("/courts/{court_id}", response_model=CourtResponse)
def owner_update_court(
    court_id: int,
    court_in: CourtUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Update a court owned by the authenticated owner."""
    court = _resolve_court(db=db, court_id=court_id, current_user=current_user)
    return update_court(db=db, court=court, court_in=court_in)


@router.patch("/courts/{court_id}/toggle-active", response_model=CourtResponse)
def owner_toggle_court_active(
    court_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Toggle the active/inactive status of a court.

    Deactivating a court prevents it from appearing in public availability
    and disables new bookings.  Historical bookings are preserved.
    """
    court = _resolve_court(db=db, court_id=court_id, current_user=current_user)
    from app.schemas.court import CourtUpdate as _CourtUpdate
    return update_court(db=db, court=court, court_in=_CourtUpdate(is_active=not court.is_active))


@router.delete("/courts/{court_id}", status_code=status.HTTP_204_NO_CONTENT)
def owner_delete_court(
    court_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Delete a court owned by the authenticated owner."""
    court = _resolve_court(db=db, court_id=court_id, current_user=current_user)
    delete_court(db=db, court=court)
    return None


# ── Availability — Working Hours ──────────────────────────────────────────────


@router.get("/courts/{court_id}/working-hours", response_model=list[CourtWorkingHoursRead])
def owner_list_working_hours(
    court_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """List working-hours schedule for a court."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    return list_working_hours(db=db, court_id=court_id)


@router.put("/courts/{court_id}/working-hours", response_model=CourtWorkingHoursRead)
def owner_upsert_working_hours(
    court_id: int,
    hours_in: CourtWorkingHoursCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Create or update a working-hours slot for a given day of week."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    return upsert_working_hours(db=db, court_id=court_id, hours_in=hours_in)


@router.delete("/courts/{court_id}/working-hours/{day_of_week}", status_code=status.HTTP_204_NO_CONTENT)
def owner_delete_working_hours(
    court_id: int,
    day_of_week: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Delete working-hours for a specific day of week."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    delete_working_hours(db=db, court_id=court_id, day_of_week=day_of_week)
    return None


# ── Availability — Rules ──────────────────────────────────────────────────────


@router.get("/courts/{court_id}/availability-rules", response_model=CourtAvailabilityRuleRead)
def owner_get_availability_rule(
    court_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Get (or auto-create) the booking-interval / buffer-time rule for a court."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    return get_or_create_availability_rule(db=db, court_id=court_id)


@router.put("/courts/{court_id}/availability-rules", response_model=CourtAvailabilityRuleRead)
def owner_update_availability_rule(
    court_id: int,
    rule_in: CourtAvailabilityRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Update the availability rule for a court."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    return update_availability_rule(db=db, court_id=court_id, rule_in=rule_in)


# ── Availability — Closures ───────────────────────────────────────────────────


@router.get("/courts/{court_id}/closures", response_model=list[CourtClosureRead])
def owner_list_closures(
    court_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """List court closures."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    return list_court_closures(db=db, court_id=court_id)


@router.post("/courts/{court_id}/closures", response_model=CourtClosureRead, status_code=status.HTTP_201_CREATED)
def owner_create_closure(
    court_id: int,
    closure_in: CourtClosureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Create a court closure."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    return create_court_closure(db=db, court_id=court_id, closure_in=closure_in)


@router.patch("/courts/{court_id}/closures/{closure_id}", response_model=CourtClosureRead)
def owner_update_closure(
    court_id: int,
    closure_id: int,
    closure_in: CourtClosureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Update an existing court closure."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    return update_court_closure(db=db, closure_id=closure_id, closure_in=closure_in)


@router.delete("/courts/{court_id}/closures/{closure_id}", status_code=status.HTTP_204_NO_CONTENT)
def owner_delete_closure(
    court_id: int,
    closure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Delete a court closure."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    delete_court_closure(db=db, closure_id=closure_id)
    return None


# ── Pricing — Rules ───────────────────────────────────────────────────────────


@router.get("/courts/{court_id}/pricing/rules", response_model=list[CourtPricingRuleRead])
def owner_list_pricing_rules(
    court_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """List pricing rules for a court."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    return list_pricing_rules(db=db, court_id=court_id)


@router.post("/courts/{court_id}/pricing/rules", response_model=CourtPricingRuleRead, status_code=status.HTTP_201_CREATED)
def owner_create_pricing_rule(
    court_id: int,
    rule_in: CourtPricingRuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Create a pricing rule for a court."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    return create_pricing_rule(db=db, court_id=court_id, rule_in=rule_in, created_by_id=current_user.id)


@router.patch("/courts/{court_id}/pricing/rules/{rule_id}", response_model=CourtPricingRuleRead)
def owner_update_pricing_rule(
    court_id: int,
    rule_id: int,
    rule_in: CourtPricingRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Update a pricing rule."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    rule = get_pricing_rule(db=db, rule_id=rule_id)
    if not rule or rule.court_id != court_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pricing rule {rule_id} not found")
    return update_pricing_rule(db=db, rule_id=rule_id, rule_in=rule_in)


@router.delete("/courts/{court_id}/pricing/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def owner_delete_pricing_rule(
    court_id: int,
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Delete a pricing rule."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    rule = get_pricing_rule(db=db, rule_id=rule_id)
    if not rule or rule.court_id != court_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Pricing rule {rule_id} not found")
    delete_pricing_rule(db=db, rule_id=rule_id)
    return None


# ── Pricing — Date Overrides ──────────────────────────────────────────────────


@router.get("/courts/{court_id}/pricing/overrides", response_model=list[CourtDatePriceOverrideRead])
def owner_list_date_overrides(
    court_id: int,
    start_date: date | None = Query(default=None),
    end_date: date | None = Query(default=None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """List date-specific price overrides for a court."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    return list_date_overrides(db=db, court_id=court_id, start_date=start_date, end_date=end_date)


@router.post("/courts/{court_id}/pricing/overrides", response_model=CourtDatePriceOverrideRead, status_code=status.HTTP_201_CREATED)
def owner_create_date_override(
    court_id: int,
    override_in: CourtDatePriceOverrideCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Create a date-specific price override."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    return create_date_override(db=db, court_id=court_id, override_in=override_in, created_by_id=current_user.id)


@router.patch("/courts/{court_id}/pricing/overrides/{override_id}", response_model=CourtDatePriceOverrideRead)
def owner_update_date_override(
    court_id: int,
    override_id: int,
    override_in: CourtDatePriceOverrideUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Update a date-specific price override."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    override = get_date_override(db=db, override_id=override_id)
    if not override or override.court_id != court_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Date override {override_id} not found")
    return update_date_override(db=db, override_id=override_id, override_in=override_in)


@router.delete("/courts/{court_id}/pricing/overrides/{override_id}", status_code=status.HTTP_204_NO_CONTENT)
def owner_delete_date_override(
    court_id: int,
    override_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Delete a date-specific price override."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    override = get_date_override(db=db, override_id=override_id)
    if not override or override.court_id != court_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Date override {override_id} not found")
    delete_date_override(db=db, override_id=override_id)
    return None


# ── Bookings — Owner View ─────────────────────────────────────────────────────


@router.get("/courts/{court_id}/bookings", response_model=list[BookingRead])
def owner_list_court_bookings(
    court_id: int,
    booking_status: BookingStatus | None = Query(default=None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """List bookings for a court owned by the authenticated owner.

    Inactive and active courts are both queryable — historical bookings
    are always preserved.
    """
    _resolve_court(db=db, court_id=court_id, current_user=current_user)

    query = (
        select(Booking)
        .options(
            joinedload(Booking.court),
            joinedload(Booking.user),
        )
        .where(Booking.court_id == court_id)
    )
    if booking_status is not None:
        query = query.where(Booking.status == booking_status)
    query = query.offset(skip).limit(limit)
    return list(db.execute(query).scalars().unique().all())


@router.get("/courts/{court_id}/bookings/{booking_id}", response_model=BookingRead)
def owner_get_court_booking(
    court_id: int,
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Get a single booking on an owner's court."""
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    booking = get_booking_by_id(db=db, booking_id=booking_id)
    if not booking or booking.court_id != court_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking {booking_id} not found on court {court_id}",
        )
    return booking


@router.patch("/courts/{court_id}/bookings/{booking_id}/status", response_model=BookingRead)
def owner_update_booking_status(
    court_id: int,
    booking_id: int,
    status_in: BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Update a booking's status (confirm, cancel, reject, complete, etc.).

    Owners may only update bookings on their own courts.
    Admins may update any booking through this endpoint.
    """
    _resolve_court(db=db, court_id=court_id, current_user=current_user)
    booking = get_booking_by_id(db=db, booking_id=booking_id)
    if not booking or booking.court_id != court_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking {booking_id} not found on court {court_id}",
        )
    return update_booking_status(
        db=db,
        booking_id=booking.id,
        status_update=status_in,
        current_user=current_user,
    )


# ── Owner Dashboard Summary ───────────────────────────────────────────────────


@router.get("/dashboard")
def owner_dashboard(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """Return a quick dashboard summary for the authenticated owner.

    Returns court count, active court count, and booking counts grouped
    by status for all courts owned by the caller.
    """
    if _is_admin(current_user):
        courts_query = select(Court)
    else:
        courts_query = select(Court).where(Court.owner_id == current_user.id)

    courts = list(db.execute(courts_query).scalars().all())
    court_ids = [c.id for c in courts]
    total_courts = len(courts)
    active_courts = sum(1 for c in courts if c.is_active)

    booking_counts: dict[str, int] = {}
    if court_ids:
        bookings_query = (
            select(Booking.status, )
            .where(Booking.court_id.in_(court_ids))
        )
        rows = db.execute(bookings_query).all()
        for row in rows:
            key = row[0].value if hasattr(row[0], "value") else str(row[0])
            booking_counts[key] = booking_counts.get(key, 0) + 1

    return {
        "owner_id": current_user.id,
        "total_courts": total_courts,
        "active_courts": active_courts,
        "inactive_courts": total_courts - active_courts,
        "bookings_by_status": booking_counts,
    }
