import secrets
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking, BookingStatus
from app.models.court import Court
from app.models.match import (
    Match,
    MatchJoinPolicy,
    MatchJoinRequest,
    MatchJoinRequestStatus,
    MatchParticipant,
    MatchPositionRequirement,
    MatchStatus,
    MatchVisibility,
    ParticipantStatus,
)
from app.models.user import User, UserRole
from app.schemas.match import MatchCreate, MatchUpdate


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)


def _enum(value, enum_type):
    return value if isinstance(value, enum_type) else enum_type(value)


def _is_admin(user: User) -> bool:
    return user.role == UserRole.ADMIN or user.is_admin


def _is_manager(match: Match, user: User) -> bool:
    return match.creator_id == user.id or _is_admin(user)


def _match_query():
    return select(Match).options(
        joinedload(Match.creator),
        joinedload(Match.court),
        joinedload(Match.booking),
        joinedload(Match.participants).joinedload(MatchParticipant.user),
    )


def get_match(db: Session, match_id: int, lock: bool = False) -> Match | None:
    statement = _match_query().where(Match.id == match_id)
    if lock:
        statement = statement.with_for_update().execution_options(populate_existing=True)
    return db.execute(statement).unique().scalar_one_or_none()


def _get_join_request(db: Session, request_id: int, lock: bool = False) -> MatchJoinRequest | None:
    statement = select(MatchJoinRequest).where(MatchJoinRequest.id == request_id)
    if lock:
        statement = statement.with_for_update().execution_options(populate_existing=True)
    return db.execute(statement).scalar_one_or_none()


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Match not found")


def _require_manager(match: Match, current_user: User) -> None:
    if not _is_manager(match, current_user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the match creator or an administrator can manage this match")


def _approved_count(db: Session, match_id: int) -> int:
    return int(db.scalar(select(func.count(MatchParticipant.id)).where(
        MatchParticipant.match_id == match_id,
        MatchParticipant.status == ParticipantStatus.APPROVED,
    )) or 0)


def _pending_count(db: Session, match_id: int) -> int:
    return int(db.scalar(select(func.count(MatchParticipant.id)).where(
        MatchParticipant.match_id == match_id,
        MatchParticipant.status == ParticipantStatus.PENDING,
    )) or 0)


def _pending_join_request_count(db: Session, match_id: int) -> int:
    return int(db.scalar(
        select(func.count(MatchJoinRequest.id)).where(
            MatchJoinRequest.match_id == match_id,
            MatchJoinRequest.status == MatchJoinRequestStatus.PENDING,
        )
    ) or 0)


def _has_active_join_request(db: Session, match_id: int, user_id: int) -> bool:
    return bool(db.scalar(
        select(MatchJoinRequest.id).where(
            MatchJoinRequest.match_id == match_id,
            MatchJoinRequest.user_id == user_id,
            MatchJoinRequest.status == MatchJoinRequestStatus.PENDING,
        )
    ))


def _validate_requested_position(db: Session, match_id: int, position_code: str | None) -> str | None:
    if position_code is None:
        return None
    code = position_code.strip()
    if not code:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Position code cannot be empty")
    has_requirements = bool(db.scalar(
        select(MatchPositionRequirement.id).where(MatchPositionRequirement.match_id == match_id)
    ))
    if has_requirements:
        valid = bool(db.scalar(
            select(MatchPositionRequirement.id).where(
                MatchPositionRequirement.match_id == match_id,
                MatchPositionRequirement.position_code == code,
            )
        ))
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Requested position is not available for this match",
            )
    return code


def _approved_position_count(db: Session, match_id: int, position_code: str) -> int:
    code = position_code.strip()
    if not code:
        return 0
    return int(db.scalar(
        select(func.count(func.distinct(MatchParticipant.user_id))).join(
            MatchJoinRequest,
            (MatchParticipant.match_id == MatchJoinRequest.match_id) & (MatchParticipant.user_id == MatchJoinRequest.user_id),
        ).where(
            MatchParticipant.match_id == match_id,
            MatchParticipant.status == ParticipantStatus.APPROVED,
            MatchJoinRequest.requested_position_code == code,
            MatchJoinRequest.status == MatchJoinRequestStatus.APPROVED,
        )
    ) or 0)


def _ensure_position_capacity(db: Session, match_id: int, position_code: str | None) -> None:
    if position_code is None:
        return
    code = position_code.strip()
    if not code:
        return
    requirement = db.execute(
        select(MatchPositionRequirement).where(
            MatchPositionRequirement.match_id == match_id,
            MatchPositionRequirement.position_code == code,
        )
    ).scalar_one_or_none()
    if not requirement:
        return
    current_approved = _approved_position_count(db, match_id, code)
    if current_approved >= requirement.required_count:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Requested position is at full capacity",
        )


def _refresh_capacity_status(db: Session, match: Match) -> None:

    if _enum(match.status, MatchStatus) in (MatchStatus.CANCELLED, MatchStatus.COMPLETED):
        return
    match.status = MatchStatus.FULL if _approved_count(db, match.id) >= match.max_players else MatchStatus.OPEN


def _generate_invite_code(db: Session) -> str:
    for _ in range(5):
        code = secrets.token_urlsafe(24)
        if not db.scalar(select(Match.id).where(Match.invite_code == code)):
            return code
    raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to generate invite code")


def _ensure_active_for_participation(match: Match) -> None:
    current_status = _enum(match.status, MatchStatus)
    if current_status not in (MatchStatus.OPEN, MatchStatus.FULL):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match is not open for joining")
    if _aware(match.start_time) <= _now():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match has already started")
    booking_status = _enum(match.booking.status, BookingStatus)
    if booking_status != BookingStatus.CONFIRMED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match booking is no longer active")


def _ensure_joinable(match: Match) -> None:
    _ensure_active_for_participation(match)
    if _enum(match.status, MatchStatus) != MatchStatus.OPEN:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match is full")


def create_match(db: Session, current_user: User, match_in: MatchCreate) -> Match:
    booking = db.execute(
        select(Booking).options(joinedload(Booking.court).joinedload(Court.sport)).where(Booking.id == match_in.booking_id)
    ).scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    if booking.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only create a match from your own booking")
    if _enum(booking.status, BookingStatus) != BookingStatus.CONFIRMED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match requires a confirmed booking")
    if not booking.court.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot create a match on an inactive court")
    if _aware(booking.start_time) <= _now():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot create a match that has already started")
    if db.scalar(select(Match.id).where(Match.booking_id == booking.id)):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking is already linked to a match")

    now = _now()
    match = Match(
        creator_id=current_user.id,
        court_id=booking.court_id,
        booking_id=booking.id,
        title=match_in.title,
        description=match_in.description,
        sport_type=booking.court.sport.slug,
        visibility=match_in.visibility,
        join_policy=match_in.join_policy,
        skill_level=match_in.skill_level,
        min_players=match_in.min_players,
        max_players=match_in.max_players,
        start_time=_aware(booking.start_time),
        end_time=_aware(booking.end_time),
        invite_code=_generate_invite_code(db) if match_in.visibility == MatchVisibility.PRIVATE else None,
        status=MatchStatus.OPEN,
    )
    try:
        db.add(match)
        db.flush()
        db.add(MatchParticipant(
            match_id=match.id,
            user_id=current_user.id,
            status=ParticipantStatus.APPROVED,
            joined_at=now,
            approved_at=now,
        ))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Booking is already linked to a match")
    except Exception:
        db.rollback()
        raise
    return get_match(db, match.id)


def get_match_for_view(db: Session, match_id: int, current_user: User, invite_code: str | None = None) -> Match:
    match = get_match(db, match_id)
    if not match:
        raise _not_found()
    if _enum(match.visibility, MatchVisibility) == MatchVisibility.PRIVATE:
        participant = next((item for item in match.participants if item.user_id == current_user.id and _enum(item.status, ParticipantStatus) in (ParticipantStatus.APPROVED, ParticipantStatus.PENDING)), None)
        if not (_is_manager(match, current_user) or participant or (invite_code and secrets.compare_digest(match.invite_code or "", invite_code))):
            raise _not_found()
    return match


def list_public_matches(db: Session, current_user: User, court_id: int | None = None, sport_type: str | None = None,
                        skill_level=None, start_date: datetime | None = None, end_date: datetime | None = None,
                        match_status=None, has_available_spots: bool | None = None, sort: str = "start_time",
                        skip: int = 0, limit: int = 20) -> list[Match]:
    statement = _match_query().where(Match.visibility == MatchVisibility.PUBLIC)
    if court_id:
        statement = statement.where(Match.court_id == court_id)
    if sport_type:
        statement = statement.where(Match.sport_type == sport_type)
    if skill_level:
        statement = statement.where(Match.skill_level == skill_level)
    if start_date:
        statement = statement.where(Match.start_time >= _aware(start_date))
    if end_date:
        statement = statement.where(Match.start_time <= _aware(end_date))
    if match_status:
        statement = statement.where(Match.status == match_status)
    if has_available_spots:
        approved = select(func.count(MatchParticipant.id)).where(
            MatchParticipant.match_id == Match.id,
            MatchParticipant.status == ParticipantStatus.APPROVED,
        ).correlate(Match).scalar_subquery()
        statement = statement.where(approved < Match.max_players)
    ordering = Match.start_time.asc() if sort == "start_time" else (Match.created_at.desc() if sort == "newest" else Match.created_at.asc())
    return list(db.execute(statement.order_by(ordering).offset(skip).limit(limit)).unique().scalars().all())


def _join(db: Session, match: Match, current_user: User) -> Match:
    _ensure_joinable(match)
    if match.creator_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match creator is already a participant")
    participant = next((item for item in match.participants if item.user_id == current_user.id), None)
    if participant and _enum(participant.status, ParticipantStatus) != ParticipantStatus.LEFT:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a participant record for this match")
    policy = _enum(match.join_policy, MatchJoinPolicy)
    approved_count = _approved_count(db, match.id)
    if policy == MatchJoinPolicy.OPEN and approved_count >= match.max_players:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match is full")
    now = _now()
    next_status = ParticipantStatus.APPROVED if policy == MatchJoinPolicy.OPEN else ParticipantStatus.PENDING
    if participant:
        participant.status = next_status
        participant.joined_at = now
        participant.approved_at = now if next_status == ParticipantStatus.APPROVED else None
        participant.rejected_at = None
    else:
        participant = MatchParticipant(match_id=match.id, user_id=current_user.id, status=next_status, joined_at=now,
                                       approved_at=now if next_status == ParticipantStatus.APPROVED else None)
        db.add(participant)
    db.flush()
    _refresh_capacity_status(db, match)
    db.commit()
    return get_match(db, match.id)


def join_match(db: Session, match_id: int, current_user: User) -> Match:
    match = get_match(db, match_id, lock=True)
    if not match or _enum(match.visibility, MatchVisibility) != MatchVisibility.PUBLIC:
        raise _not_found()
    try:
        return _join(db, match, current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already joined this match")


def join_match_by_code(db: Session, invite_code: str, current_user: User) -> Match:
    match = db.execute(_match_query().where(Match.invite_code == invite_code).with_for_update()).unique().scalar_one_or_none()
    if not match or _enum(match.visibility, MatchVisibility) != MatchVisibility.PRIVATE:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid invite code")
    try:
        return _join(db, match, current_user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already joined this match")


def leave_match(db: Session, match_id: int, current_user: User) -> Match:
    match = get_match(db, match_id, lock=True)
    if not match:
        raise _not_found()
    _ensure_active_for_participation(match)
    if match.creator_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match creator cannot leave their own match")
    participant = next((item for item in match.participants if item.user_id == current_user.id), None)
    if not participant or _enum(participant.status, ParticipantStatus) not in (ParticipantStatus.APPROVED, ParticipantStatus.PENDING):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You are not an active participant in this match")
    participant.status = ParticipantStatus.LEFT
    participant.left_at = _now()
    db.flush()
    _refresh_capacity_status(db, match)
    db.commit()
    return get_match(db, match.id)


def list_participants(db: Session, match_id: int, current_user: User) -> list[MatchParticipant]:
    match = get_match(db, match_id)
    if not match:
        raise _not_found()
    _require_manager(match, current_user)
    return match.participants


def _managed_participant(db: Session, match_id: int, participant_id: int, current_user: User) -> tuple[Match, MatchParticipant]:
    match = get_match(db, match_id, lock=True)
    if not match:
        raise _not_found()
    _require_manager(match, current_user)
    participant = next((item for item in match.participants if item.id == participant_id), None)
    if not participant:
        raise _not_found()
    if participant.user_id == match.creator_id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Creator participant cannot be managed")
    return match, participant


def approve_participant(db: Session, match_id: int, participant_id: int, current_user: User) -> Match:
    match, participant = _managed_participant(db, match_id, participant_id, current_user)
    _ensure_joinable(match)
    if _enum(participant.status, ParticipantStatus) != ParticipantStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending participants can be approved")
    if _approved_count(db, match.id) >= match.max_players:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match is full")
    participant.status = ParticipantStatus.APPROVED
    participant.approved_at = _now()
    db.flush()
    _refresh_capacity_status(db, match)
    db.commit()
    return get_match(db, match.id)


def reject_participant(db: Session, match_id: int, participant_id: int, current_user: User) -> Match:
    match, participant = _managed_participant(db, match_id, participant_id, current_user)
    if _enum(participant.status, ParticipantStatus) != ParticipantStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only pending participants can be rejected")
    participant.status = ParticipantStatus.REJECTED
    participant.rejected_at = _now()
    db.commit()
    return get_match(db, match.id)


def remove_participant(db: Session, match_id: int, participant_id: int, current_user: User) -> Match:
    match, participant = _managed_participant(db, match_id, participant_id, current_user)
    if _enum(participant.status, ParticipantStatus) not in (ParticipantStatus.APPROVED, ParticipantStatus.PENDING):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only active participants can be removed")
    participant.status = ParticipantStatus.LEFT
    participant.left_at = _now()
    db.flush()
    _refresh_capacity_status(db, match)
    db.commit()
    return get_match(db, match.id)


def update_match(db: Session, match_id: int, match_in: MatchUpdate, current_user: User) -> Match:
    match = get_match(db, match_id, lock=True)
    if not match:
        raise _not_found()
    _require_manager(match, current_user)
    if _enum(match.status, MatchStatus) in (MatchStatus.CANCELLED, MatchStatus.COMPLETED) or _aware(match.start_time) <= _now():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This match can no longer be updated")
    changes = match_in.model_dump(exclude_unset=True)
    max_players = changes.get("max_players", match.max_players)
    min_players = changes.get("min_players", match.min_players)
    if min_players > max_players:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="min_players cannot exceed max_players")
    if max_players < _approved_count(db, match.id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="max_players cannot be below approved participant count")
    for field, value in changes.items():
        setattr(match, field, value)
    if _enum(match.visibility, MatchVisibility) == MatchVisibility.PRIVATE and not match.invite_code:
        match.invite_code = _generate_invite_code(db)
    _refresh_capacity_status(db, match)
    db.commit()
    return get_match(db, match.id)


def regenerate_invite_code(db: Session, match_id: int, current_user: User) -> Match:
    match = get_match(db, match_id, lock=True)
    if not match:
        raise _not_found()
    _require_manager(match, current_user)
    if _enum(match.visibility, MatchVisibility) != MatchVisibility.PRIVATE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Only private matches have invite codes")
    if _enum(match.status, MatchStatus) in (MatchStatus.CANCELLED, MatchStatus.COMPLETED) or _aware(match.start_time) <= _now():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Invite code cannot be regenerated for this match")
    match.invite_code = _generate_invite_code(db)
    db.commit()
    return get_match(db, match.id)


def cancel_match(db: Session, match_id: int, current_user: User) -> Match:
    match = get_match(db, match_id, lock=True)
    if not match:
        raise _not_found()
    _require_manager(match, current_user)
    if _enum(match.status, MatchStatus) == MatchStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Completed match cannot be cancelled")
    if _enum(match.status, MatchStatus) != MatchStatus.CANCELLED:
        match.status = MatchStatus.CANCELLED
        match.cancelled_at = _now()
        db.commit()
    return get_match(db, match.id)


def complete_match(db: Session, match_id: int, current_user: User) -> Match:
    match = get_match(db, match_id, lock=True)
    if not match:
        raise _not_found()
    _require_manager(match, current_user)
    if _enum(match.status, MatchStatus) == MatchStatus.CANCELLED:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cancelled match cannot be completed")
    if _aware(match.end_time) > _now():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Match cannot be completed before its end time")
    if _enum(match.status, MatchStatus) != MatchStatus.COMPLETED:
        match.status = MatchStatus.COMPLETED
        match.completed_at = _now()
        db.commit()
    return get_match(db, match.id)


def list_created_matches(db: Session, current_user: User, match_status=None, skip: int = 0, limit: int = 20) -> list[Match]:
    statement = _match_query().where(Match.creator_id == current_user.id)
    if match_status:
        statement = statement.where(Match.status == match_status)
    return list(db.execute(statement.order_by(Match.start_time.asc()).offset(skip).limit(limit)).unique().scalars().all())


def list_joined_matches(db: Session, current_user: User, match_status=None, skip: int = 0, limit: int = 20) -> list[Match]:
    statement = _match_query().join(MatchParticipant).where(
        MatchParticipant.user_id == current_user.id,
        MatchParticipant.status.in_((ParticipantStatus.APPROVED, ParticipantStatus.PENDING)),
        Match.creator_id != current_user.id,
    )
    if match_status:
        statement = statement.where(Match.status == match_status)
    return list(db.execute(statement.order_by(Match.start_time.asc()).offset(skip).limit(limit)).unique().scalars().all())


def serialize_match(db: Session, match: Match, current_user: User, detail: bool = False, include_invite: bool = False) -> dict:
    participant = next((item for item in match.participants if item.user_id == current_user.id), None)
    approved_count = sum(1 for item in match.participants if _enum(item.status, ParticipantStatus) == ParticipantStatus.APPROVED)
    pending_count = sum(1 for item in match.participants if _enum(item.status, ParticipantStatus) == ParticipantStatus.PENDING)
    data = {
        "id": match.id, "title": match.title, "description": match.description, "sport_type": match.sport_type,
        "visibility": match.visibility, "join_policy": match.join_policy, "status": match.status,
        "skill_level": match.skill_level, "min_players": match.min_players, "max_players": match.max_players,
        "start_time": _aware(match.start_time), "end_time": _aware(match.end_time), "created_at": _aware(match.created_at),
        "creator": {"id": match.creator.id, "full_name": match.creator.full_name},
        "court": {"id": match.court.id, "name_en": match.court.name_en, "name_ar": match.court.name_ar, "area": match.court.area},
        "approved_participant_count": approved_count, "available_spots": max(0, match.max_players - approved_count),
        "has_joined": participant is not None and _enum(participant.status, ParticipantStatus) in (ParticipantStatus.APPROVED, ParticipantStatus.PENDING),
        "current_user_participant_status": participant.status if participant else None,
        "can_manage": _is_manager(match, current_user),
    }
    if detail:
        data["booking_id"] = match.booking_id
        data["pending_participant_count"] = pending_count if _is_manager(match, current_user) else None
        data["participants"] = [
            {"id": item.id, "user_id": item.user_id, "status": item.status, "joined_at": item.joined_at,
             "approved_at": item.approved_at, "rejected_at": item.rejected_at, "left_at": item.left_at,
             "created_at": item.created_at}
            for item in match.participants
        ] if _is_manager(match, current_user) else None
    if include_invite:
        data["invite_code"] = match.invite_code
    return data


def create_join_request(
    db: Session,
    match_id: int,
    current_user: User,
    position_code: str | None = None,
) -> MatchJoinRequest:
    match = get_match(db, match_id, lock=True)
    if not match:
        raise _not_found()
    if _enum(match.join_policy, MatchJoinPolicy) != MatchJoinPolicy.APPROVAL_REQUIRED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Match does not require approval to join",
        )
    _ensure_joinable(match)
    if match.creator_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Match creator cannot create a join request for their own match",
        )
    participant = next((item for item in match.participants if item.user_id == current_user.id), None)
    if participant and _enum(participant.status, ParticipantStatus) == ParticipantStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already an approved participant in this match",
        )
    if _has_active_join_request(db, match.id, current_user.id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending join request for this match",
        )
    normalized_position = _validate_requested_position(db, match.id, position_code)

    join_request = MatchJoinRequest(
        match_id=match.id,
        user_id=current_user.id,
        status=MatchJoinRequestStatus.PENDING,
        requested_position_code=normalized_position,
    )
    try:
        db.add(join_request)
        db.flush()
        db.commit()
        return join_request
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You already have a pending join request for this match",
        )


def withdraw_join_request(
    db: Session,
    request_id: int,
    current_user: User,
) -> MatchJoinRequest:
    request = _get_join_request(db, request_id, lock=True)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Join request not found",
        )
    if request.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only withdraw your own join request",
        )
    if _enum(request.status, MatchJoinRequestStatus) != MatchJoinRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending join requests can be withdrawn",
        )
    request.status = MatchJoinRequestStatus.WITHDRAWN
    db.commit()
    return request


def approve_join_request(
    db: Session,
    request_id: int,
    current_user: User,
) -> MatchJoinRequest:
    initial_req = _get_join_request(db, request_id, lock=False)
    if not initial_req:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Join request not found",
        )
    match = get_match(db, initial_req.match_id, lock=True)
    if not match:
        raise _not_found()
    request = _get_join_request(db, request_id, lock=True)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Join request not found",
        )
    if request.match_id != match.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Join request does not match the target match",
        )
    _require_manager(match, current_user)
    if _enum(request.status, MatchJoinRequestStatus) != MatchJoinRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending join requests can be approved",
        )
    _ensure_active_for_participation(match)

    participant = next((item for item in match.participants if item.user_id == request.user_id), None)
    if participant and _enum(participant.status, ParticipantStatus) == ParticipantStatus.APPROVED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already an approved participant in this match",
        )

    if _approved_count(db, match.id) >= match.max_players:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Match is full",
        )

    _ensure_position_capacity(db, match.id, request.requested_position_code)

    now = _now()
    if participant:
        participant.status = ParticipantStatus.APPROVED
        participant.joined_at = now
        participant.approved_at = now
        participant.rejected_at = None
        participant.left_at = None
    else:
        participant = MatchParticipant(
            match_id=match.id,
            user_id=request.user_id,
            status=ParticipantStatus.APPROVED,
            joined_at=now,
            approved_at=now,
        )
        db.add(participant)

    request.status = MatchJoinRequestStatus.APPROVED
    request.reviewed_by_user_id = current_user.id
    request.reviewed_at = now

    try:
        db.flush()
        _refresh_capacity_status(db, match)
        db.commit()
        return request
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already an approved participant in this match",
        )


def reject_join_request(
    db: Session,
    request_id: int,
    current_user: User,
) -> MatchJoinRequest:
    request = _get_join_request(db, request_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Join request not found",
        )
    match = get_match(db, request.match_id)
    if not match:
        raise _not_found()
    _require_manager(match, current_user)
    if _enum(request.status, MatchJoinRequestStatus) != MatchJoinRequestStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending join requests can be rejected",
        )

    now = _now()
    request.status = MatchJoinRequestStatus.REJECTED
    request.reviewed_by_user_id = current_user.id
    request.reviewed_at = now

    db.commit()
    return request


