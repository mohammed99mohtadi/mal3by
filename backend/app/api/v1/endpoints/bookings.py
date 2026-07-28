from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.booking import BookingStatus
from app.models.user import User, UserRole
from app.schemas.booking import (
    BookingCancel,
    BookingCreate,
    BookingRead,
    BookingStatusUpdate,
)
from app.services.booking_service import (
    cancel_booking,
    check_court_availability,
    create_booking,
    get_booking_by_id,
    list_user_bookings,
    update_booking_status,
)

router = APIRouter()


@router.post("", response_model=BookingRead, status_code=status.HTTP_201_CREATED)
def create_new_booking(
    booking_in: BookingCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new booking for the authenticated user."""
    return create_booking(db=db, user_id=current_user.id, booking_in=booking_in)


@router.get("/me", response_model=list[BookingRead])
def get_my_bookings(
    status_filter: BookingStatus | None = Query(default=None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve current authenticated user's bookings."""
    return list_user_bookings(
        db=db,
        user_id=current_user.id,
        status_filter=status_filter,
        skip=skip,
        limit=limit,
    )


@router.get("/availability/{court_id}")
def check_availability(
    court_id: int,
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    db: Session = Depends(get_db),
):
    """Check court availability for a specific time range."""
    if start_time.tzinfo is None or end_time.tzinfo is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="start_time and end_time must be timezone-aware",
        )
    is_available = check_court_availability(
        db=db,
        court_id=court_id,
        start_time=start_time,
        end_time=end_time,
    )
    return {
        "court_id": court_id,
        "available": is_available,
        "start_time": start_time,
        "end_time": end_time,
    }


@router.get("/{booking_id}", response_model=BookingRead)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve details of a booking."""
    booking = get_booking_by_id(db=db, booking_id=booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with id {booking_id} not found",
        )

    # Permission: Booking owner, Court owner, or Admin
    is_owner = booking.user_id == current_user.id
    is_court_owner = booking.court and booking.court.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN or current_user.is_admin

    if not (is_owner or is_court_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this booking",
        )

    return booking


@router.post("/{booking_id}/cancel", response_model=BookingRead)
def cancel_my_booking(
    booking_id: int,
    cancel_in: BookingCancel | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Cancel an authenticated user's booking."""
    booking = get_booking_by_id(db=db, booking_id=booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with id {booking_id} not found",
        )

    reason = cancel_in.cancellation_reason if cancel_in else None
    return cancel_booking(db=db, booking=booking, current_user=current_user, reason=reason)


@router.patch("/{booking_id}/status", response_model=BookingRead)
def update_status(
    booking_id: int,
    status_in: BookingStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update booking status (Admin or Court Owner only)."""
    booking = get_booking_by_id(db=db, booking_id=booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with id {booking_id} not found",
        )

    return update_booking_status(
        db=db,
        booking=booking,
        status_update=status_in,
        current_user=current_user,
    )
