from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.court import Court
from app.models.user import User, UserRole
from app.schemas.availability import (
    CourtAvailabilityResponse,
    CourtAvailabilityRuleCreate,
    CourtAvailabilityRuleRead,
    CourtAvailabilityRuleUpdate,
    CourtClosureCreate,
    CourtClosureRead,
    CourtClosureUpdate,
    CourtWorkingHoursCreate,
    CourtWorkingHoursRead,
)
from app.services.availability_service import (
    create_court_closure,
    delete_court_closure,
    delete_working_hours,
    generate_available_slots,
    get_or_create_availability_rule,
    list_court_closures,
    list_working_hours,
    update_availability_rule,
    update_court_closure,
    upsert_working_hours,
)

router = APIRouter()


def check_court_owner_or_admin(db: Session, court_id: int, current_user: User) -> Court:
    court = db.query(Court).filter(Court.id == court_id).first()
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court with id {court_id} not found",
        )

    is_owner = court.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN or current_user.is_admin

    if not (is_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators or court owners can perform this action.",
        )
    return court


# Management Endpoints
@router.get("/{court_id}/availability-settings/rules", response_model=CourtAvailabilityRuleRead)
def get_court_rules(
    court_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve court availability rules."""
    return get_or_create_availability_rule(db, court_id)


@router.put("/{court_id}/availability-settings/rules", response_model=CourtAvailabilityRuleRead)
def set_court_rules(
    court_id: int,
    rule_in: CourtAvailabilityRuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update court availability rules (Admin or Court Owner only)."""
    check_court_owner_or_admin(db, court_id, current_user)
    return update_availability_rule(db, court_id, rule_in)


@router.get("/{court_id}/availability-settings/working-hours", response_model=list[CourtWorkingHoursRead])
def get_court_working_hours(
    court_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve all configured working hours for a court."""
    return list_working_hours(db, court_id)


@router.put("/{court_id}/availability-settings/working-hours/{weekday}", response_model=CourtWorkingHoursRead)
def set_court_working_hours(
    court_id: int,
    weekday: int,
    hours_in: CourtWorkingHoursCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create or update working hours for one weekday (Admin or Court Owner only)."""
    if weekday != hours_in.weekday:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Weekday in URL path ({weekday}) does not match body ({hours_in.weekday})",
        )
    check_court_owner_or_admin(db, court_id, current_user)
    return upsert_working_hours(db, court_id, hours_in)


@router.delete("/{court_id}/availability-settings/working-hours/{weekday}", status_code=status.HTTP_204_NO_CONTENT)
def remove_court_working_hours(
    court_id: int,
    weekday: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete working-hours configuration for a weekday (Admin or Court Owner only)."""
    check_court_owner_or_admin(db, court_id, current_user)
    delete_working_hours(db, court_id, weekday)
    return None


@router.get("/{court_id}/availability-settings/closures", response_model=list[CourtClosureRead])
def get_court_closures(
    court_id: int,
    start_range: datetime | None = Query(default=None),
    end_range: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Retrieve court closures with optional date range filter."""
    return list_court_closures(db, court_id, start_range, end_range)


@router.post("/{court_id}/availability-settings/closures", response_model=CourtClosureRead, status_code=status.HTTP_201_CREATED)
def add_court_closure(
    court_id: int,
    closure_in: CourtClosureCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a court closure (Admin or Court Owner only)."""
    check_court_owner_or_admin(db, court_id, current_user)
    return create_court_closure(db, court_id, closure_in, created_by_id=current_user.id)


@router.patch("/{court_id}/availability-settings/closures/{closure_id}", response_model=CourtClosureRead)
def modify_court_closure(
    court_id: int,
    closure_id: int,
    closure_in: CourtClosureUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a court closure (Admin or Court Owner only)."""
    check_court_owner_or_admin(db, court_id, current_user)
    return update_court_closure(db, closure_id, closure_in)


@router.delete("/{court_id}/availability-settings/closures/{closure_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_court_closure(
    court_id: int,
    closure_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a court closure (Admin or Court Owner only)."""
    check_court_owner_or_admin(db, court_id, current_user)
    delete_court_closure(db, closure_id)
    return None


# Public Available Slots Endpoint
@router.get("/{court_id}/available-slots", response_model=CourtAvailabilityResponse)
def get_available_slots(
    court_id: int,
    date_val: date = Query(..., alias="date"),
    duration_minutes: int = Query(..., ge=1),
    start_time: datetime | None = Query(default=None),
    end_time: datetime | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """Public endpoint to generate available booking slots for a court date."""
    return generate_available_slots(
        db=db,
        court_id=court_id,
        local_date=date_val,
        duration_minutes=duration_minutes,
        req_start_time=start_time,
        req_end_time=end_time,
    )
