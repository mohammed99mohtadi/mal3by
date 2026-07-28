from datetime import datetime, timezone
from decimal import Decimal
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking, BookingStatus
from app.models.court import Court
from app.models.user import User, UserRole
from app.schemas.booking import BookingCreate, BookingStatusUpdate

ALLOWED_TRANSITIONS = {
    BookingStatus.PENDING: {
        BookingStatus.CONFIRMED,
        BookingStatus.REJECTED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.CONFIRMED: {
        BookingStatus.COMPLETED,
        BookingStatus.CANCELLED,
    },
    BookingStatus.CANCELLED: set(),
    BookingStatus.COMPLETED: set(),
    BookingStatus.REJECTED: set(),
}


def get_booking_by_id(db: Session, booking_id: int) -> Booking | None:
    statement = (
        select(Booking)
        .options(
            joinedload(Booking.court).joinedload(Court.sport),
            joinedload(Booking.user),
        )
        .where(Booking.id == booking_id)
    )
    return db.execute(statement).scalar_one_or_none()


def create_booking(db: Session, user_id: int, booking_in: BookingCreate) -> Booking:
    # 1. Full availability & business rule validation via availability service
    from app.services.availability_service import validate_requested_booking_time
    validate_requested_booking_time(
        db=db,
        court_id=booking_in.court_id,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
    )

    # 2. Get court for price calculation
    court_stmt = select(Court).where(Court.id == booking_in.court_id)
    court = db.execute(court_stmt).scalar_one_or_none()

    # 3. Calculate total_price on server (quantized Decimal)
    duration_seconds = Decimal(str((booking_in.end_time - booking_in.start_time).total_seconds()))
    duration_hours = duration_seconds / Decimal("3600")
    total_price = (duration_hours * court.price_per_hour).quantize(Decimal("0.001"))


    # 6. Save booking
    db_booking = Booking(
        user_id=user_id,
        court_id=booking_in.court_id,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
        total_price=total_price,
        status=BookingStatus.PENDING,
    )
    try:
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create booking",
        )

    return get_booking_by_id(db, db_booking.id)


def check_court_availability(
    db: Session,
    court_id: int,
    start_time: datetime,
    end_time: datetime,
) -> bool:
    court_stmt = select(Court).where(Court.id == court_id)
    court = db.execute(court_stmt).scalar_one_or_none()
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court with id {court_id} not found",
        )

    if end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_time must be after start_time",
        )

    overlap_stmt = select(Booking).where(
        Booking.court_id == court_id,
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED]),
        Booking.start_time < end_time,
        Booking.end_time > start_time,
    )
    return db.execute(overlap_stmt).first() is None


def list_user_bookings(
    db: Session,
    user_id: int,
    status_filter: BookingStatus | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Booking]:
    query = (
        select(Booking)
        .options(joinedload(Booking.court).joinedload(Court.sport))
        .where(Booking.user_id == user_id)
    )
    if status_filter is not None:
        query = query.where(Booking.status == status_filter)

    query = query.order_by(Booking.created_at.desc()).offset(skip).limit(limit)
    return list(db.execute(query).scalars().all())


def list_court_bookings(
    db: Session,
    court_id: int,
    skip: int = 0,
    limit: int = 20,
) -> list[Booking]:
    query = (
        select(Booking)
        .options(joinedload(Booking.court).joinedload(Court.sport))
        .where(Booking.court_id == court_id)
        .order_by(Booking.start_time.asc())
        .offset(skip)
        .limit(limit)
    )
    return list(db.execute(query).scalars().all())


def cancel_booking(
    db: Session,
    booking: Booking,
    current_user: User,
    reason: str | None = None,
) -> Booking:
    # Authorization: Owner of booking, court owner, or admin
    is_booking_owner = booking.user_id == current_user.id
    is_court_owner = booking.court and booking.court.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN or current_user.is_admin

    if not (is_booking_owner or is_court_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to cancel this booking",
        )

    # State check: Cannot cancel if already terminal
    cur_status = BookingStatus(booking.status) if isinstance(booking.status, str) else booking.status
    if cur_status in [BookingStatus.CANCELLED, BookingStatus.COMPLETED, BookingStatus.REJECTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel a booking that is already cancelled, completed, or rejected.",
        )

    booking.status = BookingStatus.CANCELLED
    booking.cancellation_reason = reason
    booking.cancelled_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(booking)
    return get_booking_by_id(db, booking.id)


def update_booking_status(
    db: Session,
    booking: Booking,
    status_update: BookingStatusUpdate,
    current_user: User,
) -> Booking:
    new_status = status_update.status

    # Permission check: Admin or court owner
    is_court_owner = booking.court and booking.court.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN or current_user.is_admin

    if not (is_court_owner or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only administrators or court owners can update booking status.",
        )

    # Convert status strings/enums to BookingStatus enum
    cur_status_enum = BookingStatus(booking.status) if isinstance(booking.status, str) else booking.status
    new_status_enum = BookingStatus(new_status) if isinstance(new_status, str) else new_status

    # Allowed status transition check
    valid_next_statuses = ALLOWED_TRANSITIONS.get(cur_status_enum, set())
    if new_status_enum not in valid_next_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from {cur_status_enum.value} to {new_status_enum.value}",
        )

    booking.status = new_status_enum
    if new_status_enum == BookingStatus.CANCELLED and not booking.cancelled_at:
        booking.cancelled_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(booking)
    return get_booking_by_id(db, booking.id)
