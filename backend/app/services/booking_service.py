from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import NoReturn
from fastapi import HTTPException, status
from sqlalchemy import select, or_, and_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking, BookingStatus
from app.models.court import Court
from app.models.user import User, UserRole
from app.schemas.booking import BookingCreate, BookingHoldCreate, BookingHoldStatusResponse, BookingStatusUpdate
from app.services.availability_service import expire_outdated_holds, make_utc_aware, validate_requested_booking_time

from app.services.pricing_service import calculate_booking_price

BOOKING_ACTIVE_TIME_OVERLAP_CONSTRAINT = "excl_bookings_active_court_time_overlap"
BOOKING_OVERLAP_DETAIL = "The requested time slot overlaps with an existing booking or buffer period."
BOOKING_CONFIRMATION_FORBIDDEN_DETAIL = (
    "Booking confirmation requires a trusted internal payment flow or a privileged booking manager."
)
BOOKING_CONFIRMATION_CONFLICT_DETAIL = "Booking confirmation could not be completed because of a database conflict."
BOOKING_CONFIRMATION_INTERNAL_DETAIL = "Booking confirmation could not be completed."
BOOKING_LIFECYCLE_CONFLICT_DETAIL = "Booking state changed during this operation. Please retry."
BOOKING_LIFECYCLE_INTERNAL_DETAIL = "Booking lifecycle operation could not be completed."

ALLOWED_TRANSITIONS = {
    BookingStatus.PENDING_PAYMENT: {
        BookingStatus.CONFIRMED,
        BookingStatus.CANCELLED,
        BookingStatus.EXPIRED,
        BookingStatus.REJECTED,
    },

    BookingStatus.PENDING: {
        BookingStatus.CONFIRMED,
        BookingStatus.CANCELLED,
        BookingStatus.EXPIRED,
        BookingStatus.REJECTED,
    },
    BookingStatus.CONFIRMED: {
        BookingStatus.COMPLETED,
        BookingStatus.CANCELLED,
        BookingStatus.REFUNDED,
    },
    BookingStatus.COMPLETED: {
        BookingStatus.REFUNDED,
    },
    BookingStatus.CANCELLED: set(),
    BookingStatus.EXPIRED: set(),
    BookingStatus.REJECTED: set(),
    BookingStatus.REFUNDED: set(),
}


def _raise_lifecycle_error(db: Session, status_code: int, detail: str) -> NoReturn:
    db.rollback()
    raise HTTPException(status_code=status_code, detail=detail)


def get_booking_by_id(db: Session, booking_id: int, *, lock: bool = False) -> Booking | None:
    if lock:
        statement = (
            select(Booking)
            .where(Booking.id == booking_id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
        return db.execute(statement).scalar_one_or_none()

    statement = (
        select(Booking)
        .options(
            joinedload(Booking.court).joinedload(Court.sport),
            joinedload(Booking.user),
        )
        .where(Booking.id == booking_id)
    )
    return db.execute(statement).scalar_one_or_none()


def create_booking_hold(
    db: Session,
    user_id: int,
    booking_in: BookingHoldCreate,
) -> Booking:
    expire_outdated_holds(db)

    # 1. Full availability & business rule validation
    validate_requested_booking_time(
        db=db,
        court_id=booking_in.court_id,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
    )

    # 2. Get court for price calculation
    court_stmt = select(Court).where(Court.id == booking_in.court_id)
    court = db.execute(court_stmt).scalar_one_or_none()

    # 3. Calculate price via Pricing Engine
    breakdown = calculate_booking_price(db, court, booking_in.start_time, booking_in.end_time)

    # 4. Hold Expiration Timestamp
    now_utc = datetime.now(timezone.utc)
    hold_mins = booking_in.hold_minutes if booking_in.hold_minutes is not None else 10
    hold_expires_at = now_utc + timedelta(minutes=hold_mins)

    # 5. Save booking with PENDING_PAYMENT status and hold expiration
    db_booking = Booking(
        user_id=user_id,
        court_id=booking_in.court_id,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
        total_price=breakdown.total,
        base_price_per_hour=breakdown.base_price_per_hour,
        currency=breakdown.currency,
        pricing_breakdown=breakdown.model_dump(mode="json"),
        pricing_calculated_at=now_utc,
        status=BookingStatus.PENDING_PAYMENT,
        hold_expires_at=hold_expires_at,
        status_updated_at=now_utc,
    )

    try:
        db.add(db_booking)
        db.commit()
        db.refresh(db_booking)
    except IntegrityError as exc:
        db.rollback()
        constraint_name = getattr(getattr(exc.orig, "diag", None), "constraint_name", None)
        if constraint_name == BOOKING_ACTIVE_TIME_OVERLAP_CONSTRAINT:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=BOOKING_OVERLAP_DETAIL,
            ) from exc
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create booking hold",
        ) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create booking hold",
        ) from exc

    return get_booking_by_id(db, db_booking.id)


def create_booking(db: Session, user_id: int, booking_in: BookingCreate) -> Booking:
    hold_in = BookingHoldCreate(
        court_id=booking_in.court_id,
        start_time=booking_in.start_time,
        end_time=booking_in.end_time,
        hold_minutes=10,
    )
    return create_booking_hold(db, user_id, hold_in)


def get_hold_status(
    db: Session,
    booking_id: int,
    current_user: User,
) -> BookingHoldStatusResponse:
    booking = get_booking_by_id(db, booking_id, lock=True)
    if not booking:
        _raise_lifecycle_error(db, status.HTTP_404_NOT_FOUND, f"Booking with id {booking_id} not found")

    # Authorization check
    is_owner = booking.user_id == current_user.id
    is_court_owner = booking.court and booking.court.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN or current_user.is_admin

    if not (is_owner or is_court_owner or is_admin):
        _raise_lifecycle_error(db, status.HTTP_403_FORBIDDEN, "You do not have permission to view this hold status")

    now_utc = datetime.now(timezone.utc)
    cur_status = BookingStatus(booking.status) if isinstance(booking.status, str) else booking.status
    hold_exp = make_utc_aware(booking.hold_expires_at)

    # Auto expire if hold_expires_at passed
    if cur_status in [BookingStatus.PENDING_PAYMENT, BookingStatus.PENDING] and hold_exp:
        if hold_exp <= now_utc:
            booking.status = BookingStatus.EXPIRED
            booking.expired_at = now_utc
            booking.status_updated_at = now_utc
            _commit_lifecycle_change(db, booking)
            cur_status = BookingStatus.EXPIRED

    is_expired = cur_status == BookingStatus.EXPIRED
    secs_rem = 0
    if cur_status in [BookingStatus.PENDING_PAYMENT, BookingStatus.PENDING] and hold_exp:
        if hold_exp > now_utc:
            secs_rem = int((hold_exp - now_utc).total_seconds())
        else:
            is_expired = True

    return BookingHoldStatusResponse(
        booking_id=booking.id,
        status=cur_status,
        hold_expires_at=hold_exp,
        is_expired=is_expired,
        seconds_remaining=secs_rem,
    )



def cancel_user_hold(
    db: Session,
    booking_id: int,
    current_user: User,
    reason: str | None = None,
) -> Booking:
    booking = get_booking_by_id(db, booking_id, lock=True)
    if not booking:
        _raise_lifecycle_error(db, status.HTTP_404_NOT_FOUND, f"Booking with id {booking_id} not found")

    is_owner = booking.user_id == current_user.id
    is_court_owner = booking.court and booking.court.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN or current_user.is_admin

    if not (is_owner or is_court_owner or is_admin):
        _raise_lifecycle_error(db, status.HTTP_403_FORBIDDEN, "You do not have permission to cancel this hold")

    cur_status = BookingStatus(booking.status) if isinstance(booking.status, str) else booking.status
    if cur_status not in [BookingStatus.PENDING_PAYMENT, BookingStatus.PENDING]:
        _raise_lifecycle_error(db, status.HTTP_400_BAD_REQUEST, f"Cannot cancel hold in {cur_status.value} status")

    now_utc = datetime.now(timezone.utc)
    booking.status = BookingStatus.CANCELLED
    booking.cancelled_at = now_utc
    booking.cancellation_reason = reason or "User cancelled hold"
    booking.status_updated_at = now_utc

    _commit_lifecycle_change(db, booking)
    return get_booking_by_id(db, booking.id)


def reject_untrusted_booking_confirmation(
    db: Session,
    booking_id: int,
) -> Booking:
    booking = get_booking_by_id(db, booking_id)
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Booking with id {booking_id} not found",
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail=BOOKING_CONFIRMATION_FORBIDDEN_DETAIL,
    )


def _commit_lifecycle_change(
    db: Session,
    booking: Booking,
    *,
    conflict_detail: str = BOOKING_LIFECYCLE_CONFLICT_DETAIL,
    internal_detail: str = BOOKING_LIFECYCLE_INTERNAL_DETAIL,
) -> None:
    try:
        db.commit()
        db.refresh(booking)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=conflict_detail,
        ) from exc
    except SQLAlchemyError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=internal_detail,
        ) from exc


def _confirm_booking(db: Session, booking: Booking) -> Booking:
    """Apply confirmation after caller has established trusted authority."""

    now_utc = datetime.now(timezone.utc)
    cur_status = BookingStatus(booking.status) if isinstance(booking.status, str) else booking.status

    if cur_status not in [BookingStatus.PENDING_PAYMENT, BookingStatus.PENDING]:
        _raise_lifecycle_error(
            db,
            status.HTTP_400_BAD_REQUEST,
            f"Cannot confirm payment for booking in {cur_status.value} status",
        )

    # Check if expired
    hold_exp = make_utc_aware(booking.hold_expires_at)
    if hold_exp and hold_exp <= now_utc:
        booking.status = BookingStatus.EXPIRED
        booking.expired_at = now_utc
        booking.status_updated_at = now_utc
        _commit_lifecycle_change(
            db,
            booking,
            conflict_detail=BOOKING_CONFIRMATION_CONFLICT_DETAIL,
            internal_detail=BOOKING_CONFIRMATION_INTERNAL_DETAIL,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reservation hold has expired and cannot be confirmed.",
        )


    booking.status = BookingStatus.CONFIRMED
    booking.confirmed_at = now_utc
    booking.status_updated_at = now_utc

    _commit_lifecycle_change(
        db,
        booking,
        conflict_detail=BOOKING_CONFIRMATION_CONFLICT_DETAIL,
        internal_detail=BOOKING_CONFIRMATION_INTERNAL_DETAIL,
    )
    return get_booking_by_id(db, booking.id)


def confirm_booking_after_verified_payment(db: Session, booking_id: int) -> Booking:
    """Trusted internal extension point for a future verified payment handler.

    This function is intentionally not exposed by an HTTP route. Future payment
    code must verify provider authenticity, amount, currency, and replay safety
    before calling it.
    """
    booking = get_booking_by_id(db, booking_id, lock=True)
    if not booking:
        _raise_lifecycle_error(db, status.HTTP_404_NOT_FOUND, f"Booking with id {booking_id} not found")
    return _confirm_booking(db, booking)


def check_court_availability(
    db: Session,
    court_id: int,
    start_time: datetime,
    end_time: datetime,
) -> bool:
    from app.services.availability_service import (
        check_booking_overlap_with_buffer,
        get_or_create_availability_rule,
        is_court_closed_by_exception,
        is_court_open,
    )
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

    rule = get_or_create_availability_rule(db, court_id)
    tz_str = rule.timezone

    if not is_court_open(db, court_id, start_time, end_time, tz_str):
        return False
    if is_court_closed_by_exception(db, court_id, start_time, end_time):
        return False
    if check_booking_overlap_with_buffer(db, court_id, start_time, end_time, rule.buffer_minutes):
        return False

    return True


def list_user_bookings(

    db: Session,
    user_id: int,
    status_filter: BookingStatus | None = None,
    skip: int = 0,
    limit: int = 20,
) -> list[Booking]:
    expire_outdated_holds(db)
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
    expire_outdated_holds(db)
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
    booking_id: int,
    current_user: User,
    reason: str | None = None,
) -> Booking:
    booking = get_booking_by_id(db, booking_id, lock=True)
    if not booking:
        _raise_lifecycle_error(db, status.HTTP_404_NOT_FOUND, f"Booking with id {booking_id} not found")
    is_booking_owner = booking.user_id == current_user.id
    is_court_owner = booking.court and booking.court.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN or current_user.is_admin

    if not (is_booking_owner or is_court_owner or is_admin):
        _raise_lifecycle_error(db, status.HTTP_403_FORBIDDEN, "You do not have permission to cancel this booking")

    cur_status = BookingStatus(booking.status) if isinstance(booking.status, str) else booking.status
    valid_next = ALLOWED_TRANSITIONS.get(cur_status, set())
    if BookingStatus.CANCELLED not in valid_next and cur_status not in [BookingStatus.PENDING_PAYMENT, BookingStatus.PENDING, BookingStatus.CONFIRMED]:
        _raise_lifecycle_error(db, status.HTTP_400_BAD_REQUEST, f"Cannot cancel booking in {cur_status.value} status.")

    now_utc = datetime.now(timezone.utc)
    booking.status = BookingStatus.CANCELLED
    booking.cancellation_reason = reason
    booking.cancelled_at = now_utc
    booking.status_updated_at = now_utc
    _commit_lifecycle_change(db, booking)
    return get_booking_by_id(db, booking.id)


def update_booking_status(
    db: Session,
    booking_id: int,
    status_update: BookingStatusUpdate,
    current_user: User,
) -> Booking:
    booking = get_booking_by_id(db, booking_id, lock=True)
    if not booking:
        _raise_lifecycle_error(db, status.HTTP_404_NOT_FOUND, f"Booking with id {booking_id} not found")
    new_status = status_update.status

    is_court_owner = booking.court and booking.court.owner_id == current_user.id
    is_admin = current_user.role == UserRole.ADMIN or current_user.is_admin

    if not (is_court_owner or is_admin):
        _raise_lifecycle_error(
            db,
            status.HTTP_403_FORBIDDEN,
            "Only administrators or court owners can update booking status.",
        )

    cur_status_enum = BookingStatus(booking.status) if isinstance(booking.status, str) else booking.status
    new_status_enum = BookingStatus(new_status) if isinstance(new_status, str) else new_status

    valid_next_statuses = ALLOWED_TRANSITIONS.get(cur_status_enum, set())
    if new_status_enum not in valid_next_statuses:
        _raise_lifecycle_error(
            db,
            status.HTTP_400_BAD_REQUEST,
            f"Invalid status transition from {cur_status_enum.value} to {new_status_enum.value}",
        )

    if new_status_enum == BookingStatus.CONFIRMED:
        return _confirm_booking(db, booking)

    now_utc = datetime.now(timezone.utc)
    booking.status = new_status_enum
    booking.status_updated_at = now_utc

    if new_status_enum == BookingStatus.CONFIRMED and not booking.confirmed_at:
        booking.confirmed_at = now_utc
    elif new_status_enum == BookingStatus.CANCELLED and not booking.cancelled_at:
        booking.cancelled_at = now_utc
        if status_update.cancellation_reason:
            booking.cancellation_reason = status_update.cancellation_reason
    elif new_status_enum == BookingStatus.EXPIRED and not booking.expired_at:
        booking.expired_at = now_utc
    elif new_status_enum == BookingStatus.COMPLETED and not booking.completed_at:
        booking.completed_at = now_utc
    elif new_status_enum == BookingStatus.REFUNDED and not booking.refunded_at:
        booking.refunded_at = now_utc

    _commit_lifecycle_change(db, booking)
    return get_booking_by_id(db, booking.id)
