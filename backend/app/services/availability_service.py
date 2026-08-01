from datetime import date, datetime, time as dtime, timedelta, timezone
from decimal import Decimal
import zoneinfo
from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.orm import Session

from app.models.availability import (
    CourtAvailabilityRule,
    CourtClosure,
    CourtClosureType,
    CourtWorkingHours,
)
from app.models.booking import Booking, BookingStatus
from app.models.court import Court
from app.schemas.availability import (
    AvailableSlot,
    CourtAvailabilityResponse,
    CourtAvailabilityRuleCreate,
    CourtAvailabilityRuleUpdate,
    CourtClosureCreate,
    CourtClosureUpdate,
    CourtWorkingHoursCreate,
)


def get_zone_info(tz_str: str) -> timezone | zoneinfo.ZoneInfo:
    try:
        return zoneinfo.ZoneInfo(tz_str)
    except Exception:
        if tz_str == "Asia/Kuwait":
            return timezone(timedelta(hours=3))
        if tz_str == "UTC":
            return timezone.utc
        return timezone.utc


def make_utc_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_or_create_availability_rule(db: Session, court_id: int) -> CourtAvailabilityRule:
    stmt = select(CourtAvailabilityRule).where(CourtAvailabilityRule.court_id == court_id)
    rule = db.execute(stmt).scalar_one_or_none()
    if not rule:
        rule = CourtAvailabilityRule(
            court_id=court_id,
            minimum_booking_minutes=30,
            maximum_booking_minutes=360,
            booking_interval_minutes=30,
            buffer_minutes=0,
            maximum_advance_booking_days=30,
            minimum_advance_booking_minutes=0,
            timezone="Asia/Kuwait",
        )
        db.add(rule)
        db.commit()
        db.refresh(rule)
    return rule


def update_availability_rule(
    db: Session,
    court_id: int,
    rule_in: CourtAvailabilityRuleUpdate,
) -> CourtAvailabilityRule:
    rule = get_or_create_availability_rule(db, court_id)
    update_data = rule_in.model_dump(exclude_unset=True)

    min_mins = update_data.get("minimum_booking_minutes", rule.minimum_booking_minutes)
    max_mins = update_data.get("maximum_booking_minutes", rule.maximum_booking_minutes)

    if max_mins < min_mins:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="maximum_booking_minutes must be greater than or equal to minimum_booking_minutes",
        )

    for field, value in update_data.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)
    return rule


# Working Hours Services
def list_working_hours(db: Session, court_id: int) -> list[CourtWorkingHours]:
    stmt = (
        select(CourtWorkingHours)
        .where(CourtWorkingHours.court_id == court_id)
        .order_by(CourtWorkingHours.weekday.asc())
    )
    return list(db.execute(stmt).scalars().all())


def upsert_working_hours(
    db: Session,
    court_id: int,
    hours_in: CourtWorkingHoursCreate,
) -> CourtWorkingHours:
    try:
        hours_in.validate_working_hours()
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )

    stmt = select(CourtWorkingHours).where(
        CourtWorkingHours.court_id == court_id,
        CourtWorkingHours.weekday == hours_in.weekday,
    )
    existing = db.execute(stmt).scalar_one_or_none()

    if existing:
        existing.opens_at = hours_in.opens_at
        existing.closes_at = hours_in.closes_at
        existing.is_closed = hours_in.is_closed
        record = existing
    else:
        record = CourtWorkingHours(
            court_id=court_id,
            weekday=hours_in.weekday,
            opens_at=hours_in.opens_at,
            closes_at=hours_in.closes_at,
            is_closed=hours_in.is_closed,
        )
        db.add(record)

    db.commit()
    db.refresh(record)
    return record


def delete_working_hours(db: Session, court_id: int, weekday: int) -> None:
    stmt = select(CourtWorkingHours).where(
        CourtWorkingHours.court_id == court_id,
        CourtWorkingHours.weekday == weekday,
    )
    record = db.execute(stmt).scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Working hours for weekday {weekday} not found",
        )
    db.delete(record)
    db.commit()


# Closure Services
def list_court_closures(
    db: Session,
    court_id: int,
    start_range: datetime | None = None,
    end_range: datetime | None = None,
) -> list[CourtClosure]:
    query = select(CourtClosure).where(CourtClosure.court_id == court_id)
    if start_range:
        query = query.where(CourtClosure.end_time >= start_range)
    if end_range:
        query = query.where(CourtClosure.start_time <= end_range)

    query = query.order_by(CourtClosure.start_time.asc())
    return list(db.execute(query).scalars().all())


def create_court_closure(
    db: Session,
    court_id: int,
    closure_in: CourtClosureCreate,
    created_by_id: int | None = None,
) -> CourtClosure:
    try:
        closure_in.validate_times()
    except ValueError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(err),
        )

    closure = CourtClosure(
        court_id=court_id,
        start_time=closure_in.start_time,
        end_time=closure_in.end_time,
        reason=closure_in.reason,
        closure_type=closure_in.closure_type,
        created_by_id=created_by_id,
    )
    db.add(closure)
    db.commit()
    db.refresh(closure)
    return closure


def update_court_closure(
    db: Session,
    closure_id: int,
    closure_in: CourtClosureUpdate,
) -> CourtClosure:
    stmt = select(CourtClosure).where(CourtClosure.id == closure_id)
    closure = db.execute(stmt).scalar_one_or_none()
    if not closure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court closure with id {closure_id} not found",
        )

    update_data = closure_in.model_dump(exclude_unset=True)
    start_time = update_data.get("start_time", closure.start_time)
    end_time = update_data.get("end_time", closure.end_time)

    start_time = make_utc_aware(start_time)
    end_time = make_utc_aware(end_time)

    if end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Closure end_time must be after start_time",
        )

    for field, value in update_data.items():
        setattr(closure, field, value)

    db.commit()
    db.refresh(closure)
    return closure


def delete_court_closure(db: Session, closure_id: int) -> None:
    stmt = select(CourtClosure).where(CourtClosure.id == closure_id)
    closure = db.execute(stmt).scalar_one_or_none()
    if not closure:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court closure with id {closure_id} not found",
        )
    db.delete(closure)
    db.commit()


# Availability Calculation Helpers
def get_working_intervals_for_local_date(
    db: Session,
    court_id: int,
    local_date: date,
    tz_str: str,
) -> list[tuple[datetime, datetime]]:
    """Returns working datetime intervals in UTC for a specific local date."""
    working_hours_list = list_working_hours(db, court_id)
    tz = get_zone_info(tz_str)

    if not working_hours_list:
        # Default strategy: 24/7 open if no working hours configured
        day_start = datetime.combine(local_date, dtime.min, tzinfo=tz).astimezone(timezone.utc)
        day_end = datetime.combine(local_date + timedelta(days=1), dtime.min, tzinfo=tz).astimezone(timezone.utc)
        return [(day_start, day_end)]

    intervals = []

    # Check local_date weekday (0=Mon, 6=Sun)
    curr_weekday = local_date.weekday()
    curr_wh = next((wh for wh in working_hours_list if wh.weekday == curr_weekday), None)

    if curr_wh and not curr_wh.is_closed and curr_wh.opens_at and curr_wh.closes_at:
        if curr_wh.opens_at < curr_wh.closes_at:
            # Same-day interval
            start_local = datetime.combine(local_date, curr_wh.opens_at, tzinfo=tz)
            end_local = datetime.combine(local_date, curr_wh.closes_at, tzinfo=tz)
            intervals.append((start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)))
        else:
            # Overnight interval starting today
            start_local = datetime.combine(local_date, curr_wh.opens_at, tzinfo=tz)
            end_local = datetime.combine(local_date + timedelta(days=1), curr_wh.closes_at, tzinfo=tz)
            intervals.append((start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)))

    # Also check previous day's overnight hours that spill over into today
    prev_date = local_date - timedelta(days=1)
    prev_weekday = prev_date.weekday()
    prev_wh = next((wh for wh in working_hours_list if wh.weekday == prev_weekday), None)

    if prev_wh and not prev_wh.is_closed and prev_wh.opens_at and prev_wh.closes_at:
        if prev_wh.opens_at >= prev_wh.closes_at:
            # Previous day overnight interval
            start_local = datetime.combine(prev_date, prev_wh.opens_at, tzinfo=tz)
            end_local = datetime.combine(local_date, prev_wh.closes_at, tzinfo=tz)
            intervals.append((start_local.astimezone(timezone.utc), end_local.astimezone(timezone.utc)))

    return intervals


def is_court_open(
    db: Session,
    court_id: int,
    start_time: datetime,
    end_time: datetime,
    tz_str: str,
) -> bool:
    working_hours_list = list_working_hours(db, court_id)
    if not working_hours_list:
        # Default strategy: 24/7 open if no working hours configured
        return True

    tz = get_zone_info(tz_str)
    start_time = make_utc_aware(start_time)
    end_time = make_utc_aware(end_time)

    local_start = start_time.astimezone(tz)
    local_date = local_start.date()

    intervals = get_working_intervals_for_local_date(db, court_id, local_date, tz_str)
    intervals += get_working_intervals_for_local_date(db, court_id, local_date + timedelta(days=1), tz_str)

    # Check if requested [start_time, end_time] is completely within any working interval
    for int_start, int_end in intervals:
        if start_time >= int_start and end_time <= int_end:
            return True
    return False


def is_court_closed_by_exception(
    db: Session,
    court_id: int,
    start_time: datetime,
    end_time: datetime,
) -> bool:
    start_time = make_utc_aware(start_time)
    end_time = make_utc_aware(end_time)

    stmt = select(CourtClosure).where(CourtClosure.court_id == court_id)
    closures = list(db.execute(stmt).scalars().all())

    for c in closures:
        c_start = make_utc_aware(c.start_time)
        c_end = make_utc_aware(c.end_time)

        if c_start < end_time and c_end > start_time:
            return True
    return False


def expire_outdated_holds(db: Session) -> int:
    """Atomically lock and expire eligible holds, committing this cleanup unit."""
    now_utc = datetime.now(timezone.utc)
    stmt = (
        select(Booking)
        .where(
            Booking.status.in_([BookingStatus.PENDING_PAYMENT, BookingStatus.PENDING]),
            Booking.hold_expires_at.is_not(None),
            Booking.hold_expires_at <= now_utc,
        )
        .with_for_update(skip_locked=True)
        .execution_options(populate_existing=True)
    )
    expired_bookings = list(db.execute(stmt).scalars().all())

    count = 0
    for b in expired_bookings:
        b.status = BookingStatus.EXPIRED
        b.expired_at = now_utc
        b.status_updated_at = now_utc
        count += 1

    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        raise
    return count



def check_booking_overlap_with_buffer(
    db: Session,
    court_id: int,
    start_time: datetime,
    end_time: datetime,
    buffer_minutes: int,
) -> bool:
    expire_outdated_holds(db)
    start_time = make_utc_aware(start_time)
    end_time = make_utc_aware(end_time)
    now_utc = datetime.now(timezone.utc)

    # Fetch active candidate bookings (CONFIRMED, PENDING_PAYMENT, PENDING)
    stmt = select(Booking).where(
        Booking.court_id == court_id,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING_PAYMENT, BookingStatus.PENDING]),
    )
    raw_bookings = list(db.execute(stmt).scalars().all())

    active_bookings = []
    for b in raw_bookings:
        b_status = BookingStatus(b.status) if isinstance(b.status, str) else b.status
        if b_status == BookingStatus.CONFIRMED:
            active_bookings.append(b)
        elif b_status in [BookingStatus.PENDING_PAYMENT, BookingStatus.PENDING]:
            b_hold = make_utc_aware(b.hold_expires_at)
            if b_hold is None or b_hold > now_utc:
                active_bookings.append(b)

    buffer_delta = timedelta(minutes=buffer_minutes)
    for b in active_bookings:
        b_start = make_utc_aware(b.start_time)
        b_end = make_utc_aware(b.end_time)

        blocked_start = b_start - buffer_delta
        blocked_end = b_end + buffer_delta

        if blocked_start < end_time and blocked_end > start_time:
            return True
    return False




def validate_requested_booking_time(
    db: Session,
    court_id: int,
    start_time: datetime,
    end_time: datetime,
) -> CourtAvailabilityRule:
    """Validate all 13 availability requirements in order."""
    # 1. Court exists
    court_stmt = select(Court).where(Court.id == court_id)
    court = db.execute(court_stmt).scalar_one_or_none()
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court with id {court_id} not found",
        )

    # 2. Court active
    if not court.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Court is inactive and not available for booking",
        )

    # 3. Timezone-aware check
    if start_time.tzinfo is None or end_time.tzinfo is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_time and end_time must be timezone-aware",
        )

    start_time = make_utc_aware(start_time)
    end_time = make_utc_aware(end_time)

    if end_time <= start_time:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="end_time must be after start_time",
        )

    # 4. Start in future
    now_utc = datetime.now(timezone.utc)
    if start_time < now_utc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Booking start time cannot be in the past",
        )

    rule = get_or_create_availability_rule(db, court_id)
    duration_mins = int((end_time - start_time).total_seconds() / 60)

    # 5. Min and Max duration
    if duration_mins < rule.minimum_booking_minutes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking duration must be at least {rule.minimum_booking_minutes} minutes",
        )
    if duration_mins > rule.maximum_booking_minutes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking duration must not exceed {rule.maximum_booking_minutes} minutes",
        )

    # 6. Duration alignment
    if duration_mins % rule.booking_interval_minutes != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking duration must align with the interval of {rule.booking_interval_minutes} minutes",
        )

    # 7. Start time alignment with booking_interval_minutes in court timezone
    tz = get_zone_info(rule.timezone)
    local_start = start_time.astimezone(tz)
    start_minutes_from_midnight = local_start.hour * 60 + local_start.minute
    if start_minutes_from_midnight % rule.booking_interval_minutes != 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking start time must align with the interval of {rule.booking_interval_minutes} minutes",
        )

    # 8. Minimum advance booking minutes
    if rule.minimum_advance_booking_minutes > 0:
        earliest_start = now_utc + timedelta(minutes=rule.minimum_advance_booking_minutes)
        if start_time < earliest_start:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Booking must be made at least {rule.minimum_advance_booking_minutes} minutes in advance",
            )

    # 9. Maximum advance booking days
    latest_start = now_utc + timedelta(days=rule.maximum_advance_booking_days)
    if start_time > latest_start:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Booking cannot be made more than {rule.maximum_advance_booking_days} days in advance",
        )

    # 10. Open during working hours
    if not is_court_open(db, court_id, start_time, end_time, rule.timezone):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Court is closed during the requested time",
        )

    # 11. Not in CourtClosure
    if is_court_closed_by_exception(db, court_id, start_time, end_time):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Court is closed for maintenance or a special event during this time",
        )

    # 12 & 13. Active booking overlap with buffer
    if check_booking_overlap_with_buffer(db, court_id, start_time, end_time, rule.buffer_minutes):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="The requested time slot overlaps with an existing booking or buffer period.",
        )

    return rule


def generate_available_slots(
    db: Session,
    court_id: int,
    local_date: date,
    duration_minutes: int,
    req_start_time: datetime | None = None,
    req_end_time: datetime | None = None,
) -> CourtAvailabilityResponse:
    court_stmt = select(Court).where(Court.id == court_id)
    court = db.execute(court_stmt).scalar_one_or_none()
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court with id {court_id} not found",
        )

    rule = get_or_create_availability_rule(db, court_id)
    tz_str = rule.timezone

    if duration_minutes < rule.minimum_booking_minutes or duration_minutes > rule.maximum_booking_minutes:
        return CourtAvailabilityResponse(
            court_id=court_id,
            local_date=local_date,
            timezone=tz_str,
            duration_minutes=duration_minutes,
            slots=[],
            reason=f"Duration must be between {rule.minimum_booking_minutes} and {rule.maximum_booking_minutes} minutes.",
        )

    intervals = get_working_intervals_for_local_date(db, court_id, local_date, tz_str)
    if not intervals:
        return CourtAvailabilityResponse(
            court_id=court_id,
            local_date=local_date,
            timezone=tz_str,
            duration_minutes=duration_minutes,
            slots=[],
            reason="Court is closed on this date.",
        )

    now_utc = datetime.now(timezone.utc)
    interval_delta = timedelta(minutes=rule.booking_interval_minutes)
    slot_duration = timedelta(minutes=duration_minutes)

    if req_start_time:
        req_start_time = make_utc_aware(req_start_time)
    if req_end_time:
        req_end_time = make_utc_aware(req_end_time)

    slots = []
    for int_start, int_end in intervals:
        curr_start = int_start
        while curr_start + slot_duration <= int_end:
            curr_end = curr_start + slot_duration

            # Optional filter by req_start_time / req_end_time
            if req_start_time and curr_start < req_start_time:
                curr_start += interval_delta
                continue
            if req_end_time and curr_end > req_end_time:
                curr_start += interval_delta
                continue

            # Skip past slots
            if curr_start <= now_utc:
                curr_start += interval_delta
                continue

            # Check advance window
            if rule.minimum_advance_booking_minutes > 0:
                if curr_start < now_utc + timedelta(minutes=rule.minimum_advance_booking_minutes):
                    curr_start += interval_delta
                    continue
            if curr_start > now_utc + timedelta(days=rule.maximum_advance_booking_days):
                curr_start += interval_delta
                continue

            # Check closures & booking buffer overlaps
            is_closed = is_court_closed_by_exception(db, court_id, curr_start, curr_end)
            has_overlap = check_booking_overlap_with_buffer(db, court_id, curr_start, curr_end, rule.buffer_minutes)

            is_available = (not is_closed) and (not has_overlap)

            # Calculate price via Pricing Engine
            from app.services.pricing_service import calculate_booking_price
            price_breakdown = calculate_booking_price(db, court, curr_start, curr_end)
            price = price_breakdown.total


            slots.append(
                AvailableSlot(
                    start_time=curr_start,
                    end_time=curr_end,
                    total_price=price,
                    available=is_available,
                )
            )
            curr_start += interval_delta

    return CourtAvailabilityResponse(
        court_id=court_id,
        local_date=local_date,
        timezone=tz_str,
        duration_minutes=duration_minutes,
        slots=slots,
    )
