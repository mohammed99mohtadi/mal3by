from datetime import date, datetime, time as dtime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
import zoneinfo
from fastapi import HTTPException, status
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import Session

from app.models.court import Court
from app.models.pricing import CourtDatePriceOverride, CourtPricingRule, PricingRuleType
from app.services.availability_service import (
    get_or_create_availability_rule,
    get_zone_info,
    make_utc_aware,
    is_court_open,
    is_court_closed_by_exception,
    check_booking_overlap_with_buffer,
)
from app.schemas.pricing import (
    AppliedPricingRule,
    BookingPriceQuoteResponse,
    CourtDatePriceOverrideCreate,
    CourtDatePriceOverrideUpdate,
    CourtPricingRuleCreate,
    CourtPricingRuleUpdate,
    PriceBreakdown,
    PriceSegment,
)


def list_pricing_rules(db: Session, court_id: int) -> list[CourtPricingRule]:
    stmt = (
        select(CourtPricingRule)
        .where(CourtPricingRule.court_id == court_id)
        .order_by(CourtPricingRule.priority.asc(), CourtPricingRule.created_at.asc())
    )
    return list(db.execute(stmt).scalars().all())


def get_pricing_rule(db: Session, rule_id: int) -> CourtPricingRule | None:
    stmt = select(CourtPricingRule).where(CourtPricingRule.id == rule_id)
    return db.execute(stmt).scalar_one_or_none()


def create_pricing_rule(
    db: Session,
    court_id: int,
    rule_in: CourtPricingRuleCreate,
    created_by_id: int | None = None,
) -> CourtPricingRule:
    rule = CourtPricingRule(
        court_id=court_id,
        name=rule_in.name,
        description=rule_in.description,
        rule_type=rule_in.rule_type,
        weekday=rule_in.weekday,
        starts_at=rule_in.starts_at,
        ends_at=rule_in.ends_at,
        value=rule_in.value,
        priority=rule_in.priority,
        is_active=rule_in.is_active,
        valid_from=rule_in.valid_from,
        valid_until=rule_in.valid_until,
        created_by_id=created_by_id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def update_pricing_rule(
    db: Session,
    rule_id: int,
    rule_in: CourtPricingRuleUpdate,
) -> CourtPricingRule:
    rule = get_pricing_rule(db, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule with id {rule_id} not found",
        )

    update_data = rule_in.model_dump(exclude_unset=True)

    starts_at = update_data.get("starts_at", rule.starts_at)
    ends_at = update_data.get("ends_at", rule.ends_at)
    if (starts_at is None) != (ends_at is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="starts_at and ends_at must both be provided or both be null",
        )

    valid_from = update_data.get("valid_from", rule.valid_from)
    valid_until = update_data.get("valid_until", rule.valid_until)
    if valid_from and valid_until and valid_until < valid_from:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="valid_until cannot be earlier than valid_from",
        )

    for field, value in update_data.items():
        setattr(rule, field, value)

    db.commit()
    db.refresh(rule)
    return rule


def delete_pricing_rule(db: Session, rule_id: int) -> None:
    rule = get_pricing_rule(db, rule_id)
    if not rule:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pricing rule with id {rule_id} not found",
        )
    db.delete(rule)
    db.commit()


# Date Override CRUD
def list_date_overrides(
    db: Session,
    court_id: int,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[CourtDatePriceOverride]:
    stmt = select(CourtDatePriceOverride).where(CourtDatePriceOverride.court_id == court_id)
    if start_date:
        stmt = stmt.where(CourtDatePriceOverride.local_date >= start_date)
    if end_date:
        stmt = stmt.where(CourtDatePriceOverride.local_date <= end_date)

    stmt = stmt.order_by(CourtDatePriceOverride.local_date.asc(), CourtDatePriceOverride.priority.asc())
    return list(db.execute(stmt).scalars().all())


def get_date_override(db: Session, override_id: int) -> CourtDatePriceOverride | None:
    stmt = select(CourtDatePriceOverride).where(CourtDatePriceOverride.id == override_id)
    return db.execute(stmt).scalar_one_or_none()


def create_date_override(
    db: Session,
    court_id: int,
    override_in: CourtDatePriceOverrideCreate,
    created_by_id: int | None = None,
) -> CourtDatePriceOverride:
    override = CourtDatePriceOverride(
        court_id=court_id,
        name=override_in.name,
        local_date=override_in.local_date,
        starts_at=override_in.starts_at,
        ends_at=override_in.ends_at,
        override_type=override_in.override_type,
        value=override_in.value,
        priority=override_in.priority,
        is_active=override_in.is_active,
        created_by_id=created_by_id,
    )
    db.add(override)
    db.commit()
    db.refresh(override)
    return override


def update_date_override(
    db: Session,
    override_id: int,
    override_in: CourtDatePriceOverrideUpdate,
) -> CourtDatePriceOverride:
    override = get_date_override(db, override_id)
    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Date price override with id {override_id} not found",
        )

    update_data = override_in.model_dump(exclude_unset=True)
    starts_at = update_data.get("starts_at", override.starts_at)
    ends_at = update_data.get("ends_at", override.ends_at)
    if (starts_at is None) != (ends_at is None):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="starts_at and ends_at must both be provided or both be null",
        )

    for field, value in update_data.items():
        setattr(override, field, value)

    db.commit()
    db.refresh(override)
    return override


def delete_date_override(db: Session, override_id: int) -> None:
    override = get_date_override(db, override_id)
    if not override:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Date price override with id {override_id} not found",
        )
    db.delete(override)
    db.commit()


# Helper: Check if a local time interval falls within a rule's time range
def _is_time_in_range(
    target_start: dtime,
    target_end: dtime,
    rule_start: dtime | None,
    rule_end: dtime | None,
) -> bool:
    if rule_start is None or rule_end is None:
        return True

    if rule_start < rule_end:
        # Same day time range (e.g. 18:00 to 22:00)
        return target_start >= rule_start and target_end <= rule_end
    else:
        # Overnight range (e.g. 20:00 to 02:00)
        # Matches if interval is completely in [rule_start, 24:00] OR completely in [00:00, rule_end]
        part1 = target_start >= rule_start and target_end > rule_start
        part2 = target_end <= rule_end and target_start < rule_end
        return part1 or part2


def calculate_booking_price(
    db: Session,
    court: Court,
    start_time: datetime,
    end_time: datetime,
) -> PriceBreakdown:
    start_time = make_utc_aware(start_time)
    end_time = make_utc_aware(end_time)

    avail_rule = get_or_create_availability_rule(db, court.id)
    tz_str = avail_rule.timezone
    tz = get_zone_info(tz_str)

    # 1. Fetch active recurring rules and date overrides
    rules_stmt = select(CourtPricingRule).where(
        CourtPricingRule.court_id == court.id,
        CourtPricingRule.is_active == True,
    )
    recurring_rules = list(db.execute(rules_stmt).scalars().all())

    overrides_stmt = select(CourtDatePriceOverride).where(
        CourtDatePriceOverride.court_id == court.id,
        CourtDatePriceOverride.is_active == True,
    )
    date_overrides = list(db.execute(overrides_stmt).scalars().all())

    # 2. Build sub-segment boundaries in UTC
    boundaries: set[datetime] = {start_time, end_time}

    # Add midnights in court local timezone
    local_start = start_time.astimezone(tz)
    local_end = end_time.astimezone(tz)

    curr_date = local_start.date()
    end_date = local_end.date()

    while curr_date <= end_date + timedelta(days=1):
        midnight_utc = datetime.combine(curr_date, dtime.min, tzinfo=tz).astimezone(timezone.utc)
        if start_time < midnight_utc < end_time:
            boundaries.add(midnight_utc)

        # Add time range boundaries for rules and overrides
        for r in recurring_rules:
            if r.starts_at and r.ends_at:
                t1_utc = datetime.combine(curr_date, r.starts_at, tzinfo=tz).astimezone(timezone.utc)
                t2_utc = datetime.combine(curr_date, r.ends_at, tzinfo=tz).astimezone(timezone.utc)
                if start_time < t1_utc < end_time:
                    boundaries.add(t1_utc)
                if start_time < t2_utc < end_time:
                    boundaries.add(t2_utc)

        for o in date_overrides:
            if o.local_date == curr_date and o.starts_at and o.ends_at:
                t1_utc = datetime.combine(curr_date, o.starts_at, tzinfo=tz).astimezone(timezone.utc)
                t2_utc = datetime.combine(curr_date, o.ends_at, tzinfo=tz).astimezone(timezone.utc)
                if start_time < t1_utc < end_time:
                    boundaries.add(t1_utc)
                if start_time < t2_utc < end_time:
                    boundaries.add(t2_utc)

        curr_date += timedelta(days=1)

    sorted_boundaries = sorted(list(boundaries))

    # 3. Process sub-segments
    segments: list[PriceSegment] = []
    base_hourly_rate = Decimal(str(court.price_per_hour))
    subtotal_sum = Decimal("0.000")

    for i in range(len(sorted_boundaries) - 1):
        seg_start = sorted_boundaries[i]
        seg_end = sorted_boundaries[i + 1]

        duration_mins = int((seg_end - seg_start).total_seconds() / 60)
        if duration_mins <= 0:
            continue

        seg_local_start = seg_start.astimezone(tz)
        seg_local_end = seg_end.astimezone(tz)

        seg_date = seg_local_start.date()
        seg_weekday = seg_date.weekday()

        seg_start_time = seg_local_start.time()
        seg_end_time = seg_local_end.time()
        if seg_end_time == dtime.min and seg_local_end.date() > seg_local_start.date():
            seg_end_time = dtime(23, 59, 59, 999999)

        matched_candidates: list[dict] = []

        # Check date overrides
        for o in date_overrides:
            if o.local_date == seg_date:
                if _is_time_in_range(seg_start_time, seg_end_time, o.starts_at, o.ends_at):
                    matched_candidates.append({
                        "type": "override",
                        "obj": o,
                        "priority": o.priority,
                        "created_at": o.created_at,
                        "id": o.id,
                    })

        # Check recurring rules
        for r in recurring_rules:
            # Validity date check
            if r.valid_from and seg_date < r.valid_from:
                continue
            if r.valid_until and seg_date > r.valid_until:
                continue

            # Check matching weekday:
            # 1) Direct match: r.weekday is None or r.weekday == seg_weekday
            # 2) Overnight match: rule for prev_weekday with starts_at >= ends_at spilling into seg_date before ends_at
            weekday_match = False
            if r.weekday is None or r.weekday == seg_weekday:
                if _is_time_in_range(seg_start_time, seg_end_time, r.starts_at, r.ends_at):
                    weekday_match = True
            elif r.starts_at and r.ends_at and r.starts_at >= r.ends_at:
                prev_weekday = (seg_weekday - 1) % 7
                if (r.weekday is None or r.weekday == prev_weekday) and seg_end_time <= r.ends_at:
                    weekday_match = True

            if weekday_match:
                matched_candidates.append({
                    "type": "rule",
                    "obj": r,
                    "priority": r.priority,
                    "created_at": r.created_at,
                    "id": r.id,
                })

        # Sort candidate rules deterministically by (priority asc, created_at asc, id asc)
        matched_candidates.sort(key=lambda item: (item["priority"], item["created_at"], item["id"]))

        # Apply rules in order
        hourly_rate = base_hourly_rate
        applied_rules_info: list[AppliedPricingRule] = []

        for cand in matched_candidates:
            obj = cand["obj"]
            r_type = obj.override_type if cand["type"] == "override" else obj.rule_type
            val = Decimal(str(obj.value))

            if r_type == PricingRuleType.FIXED_HOURLY_PRICE:
                hourly_rate = val
            elif r_type == PricingRuleType.PERCENTAGE_ADJUSTMENT:
                hourly_rate = hourly_rate * (Decimal("1") + (val / Decimal("100")))
            elif r_type == PricingRuleType.FIXED_HOURLY_ADJUSTMENT:
                hourly_rate = hourly_rate + val

            # Hourly rate cannot become negative
            if hourly_rate < Decimal("0"):
                hourly_rate = Decimal("0")

            applied_rules_info.append(
                AppliedPricingRule(
                    rule_id=obj.id if cand["type"] == "rule" else None,
                    override_id=obj.id if cand["type"] == "override" else None,
                    name=obj.name,
                    rule_type=r_type,
                    value=val,
                    priority=obj.priority,
                )
            )

        hourly_rate = hourly_rate.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)
        dur_hours = Decimal(str(duration_mins)) / Decimal("60")
        seg_subtotal = (hourly_rate * dur_hours).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

        subtotal_sum += seg_subtotal

        segments.append(
            PriceSegment(
                start_time=seg_start,
                end_time=seg_end,
                duration_minutes=duration_mins,
                hourly_rate=hourly_rate,
                subtotal=seg_subtotal,
                applied_rules=applied_rules_info,
            )
        )

    final_total = subtotal_sum.quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)

    return PriceBreakdown(
        currency="KWD",
        base_price_per_hour=base_hourly_rate.quantize(Decimal("0.001")),
        segments=segments,
        subtotal=final_total,
        total=final_total,
    )


def create_price_quote(
    db: Session,
    court_id: int,
    start_time: datetime,
    end_time: datetime,
) -> BookingPriceQuoteResponse:
    court_stmt = select(Court).where(Court.id == court_id)
    court = db.execute(court_stmt).scalar_one_or_none()
    if not court:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Court with id {court_id} not found",
        )

    if not court.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Court is inactive",
        )

    start_time = make_utc_aware(start_time)
    end_time = make_utc_aware(end_time)

    avail_rule = get_or_create_availability_rule(db, court_id)
    tz_str = avail_rule.timezone

    breakdown = calculate_booking_price(db, court, start_time, end_time)

    # Informational availability check
    is_available = True
    try:
        # Check basic working hours, closures, and overlaps
        if not is_court_open(db, court_id, start_time, end_time, tz_str):
            is_available = False
        elif is_court_closed_by_exception(db, court_id, start_time, end_time):
            is_available = False
        elif check_booking_overlap_with_buffer(db, court_id, start_time, end_time, avail_rule.buffer_minutes):
            is_available = False
    except Exception:
        is_available = False

    return BookingPriceQuoteResponse(
        court_id=court_id,
        start_time=start_time,
        end_time=end_time,
        court_timezone=tz_str,
        currency=breakdown.currency,
        base_price_per_hour=breakdown.base_price_per_hour,
        segments=breakdown.segments,
        subtotal=breakdown.subtotal,
        total=breakdown.total,
        available=is_available,
    )
