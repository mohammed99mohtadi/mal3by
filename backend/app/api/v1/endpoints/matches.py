from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.db.session import get_db
from app.models.match import MatchJoinRequestStatus, MatchStatus, SkillLevel
from app.models.user import User
from app.schemas.match import (
    InviteCodeResponse,
    JoinByCodeRequest,
    MatchCreate,
    MatchCreateResponse,
    MatchDetailResponse,
    MatchJoinRequestCreate,
    MatchJoinRequestResponse,
    MatchParticipantManagementResponse,
    MatchPublicResponse,
    MatchUpdate,
)
from app.services import match_service

router = APIRouter()


@router.post("", response_model=MatchCreateResponse, status_code=status.HTTP_201_CREATED)
def create_new_match(
    match_in: MatchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = match_service.create_match(db, current_user, match_in)
    return match_service.serialize_match(db, match, current_user, detail=True, include_invite=True)


@router.get("", response_model=list[MatchPublicResponse])
def list_matches(
    court_id: int | None = Query(default=None, gt=0),
    sport_type: str | None = Query(default=None, min_length=1, max_length=100),
    skill_level: SkillLevel | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    status_filter: MatchStatus | None = Query(default=None, alias="status"),
    has_available_spots: bool | None = None,
    sort: str = Query(default="start_time", pattern="^(start_time|newest|oldest)$"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    matches = match_service.list_public_matches(
        db, current_user, court_id, sport_type, skill_level, start_date, end_date,
        status_filter, has_available_spots, sort, skip, limit,
    )
    return [match_service.serialize_match(db, match, current_user) for match in matches]


@router.post("/join-by-code", response_model=MatchDetailResponse)
def join_private_match(
    join_in: JoinByCodeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = match_service.join_match_by_code(db, join_in.invite_code, current_user)
    return match_service.serialize_match(db, match, current_user, detail=True)


@router.get("/me/created", response_model=list[MatchPublicResponse])
def get_my_created_matches(
    status_filter: MatchStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return [match_service.serialize_match(db, match, current_user) for match in match_service.list_created_matches(db, current_user, status_filter, skip, limit)]


@router.get("/me/joined", response_model=list[MatchPublicResponse])
def get_my_joined_matches(
    status_filter: MatchStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return [match_service.serialize_match(db, match, current_user) for match in match_service.list_joined_matches(db, current_user, status_filter, skip, limit)]


@router.get("/me/join-requests", response_model=list[MatchJoinRequestResponse])
def get_my_join_requests(
    status_filter: MatchJoinRequestStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return match_service.list_user_join_requests(db, current_user, status_filter, skip, limit)


@router.get("/{match_id}", response_model=MatchDetailResponse)
def get_match_details(
    match_id: int,
    invite_code: str | None = Query(default=None, min_length=16, max_length=128),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = match_service.get_match_for_view(db, match_id, current_user, invite_code)
    return match_service.serialize_match(db, match, current_user, detail=True)


@router.post("/{match_id}/join", response_model=MatchDetailResponse)
def join_public_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = match_service.join_match(db, match_id, current_user)
    return match_service.serialize_match(db, match, current_user, detail=True)


@router.post("/{match_id}/leave", response_model=MatchDetailResponse)
def leave_current_match(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    match = match_service.leave_match(db, match_id, current_user)
    return match_service.serialize_match(db, match, current_user, detail=True)


@router.get("/{match_id}/participants", response_model=list[MatchParticipantManagementResponse])
def get_match_participants(
    match_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    participants = match_service.list_participants(db, match_id, current_user)
    return [{
        "id": item.id, "user_id": item.user_id, "user_name": item.user.full_name, "status": item.status,
        "joined_at": item.joined_at, "approved_at": item.approved_at, "rejected_at": item.rejected_at,
        "left_at": item.left_at, "created_at": item.created_at,
    } for item in participants]


@router.post("/{match_id}/participants/{participant_id}/approve", response_model=MatchDetailResponse)
def approve_match_participant(match_id: int, participant_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    match = match_service.approve_participant(db, match_id, participant_id, current_user)
    return match_service.serialize_match(db, match, current_user, detail=True)


@router.post("/{match_id}/participants/{participant_id}/reject", response_model=MatchDetailResponse)
def reject_match_participant(match_id: int, participant_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    match = match_service.reject_participant(db, match_id, participant_id, current_user)
    return match_service.serialize_match(db, match, current_user, detail=True)


@router.post("/{match_id}/participants/{participant_id}/remove", response_model=MatchDetailResponse)
def remove_match_participant(match_id: int, participant_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    match = match_service.remove_participant(db, match_id, participant_id, current_user)
    return match_service.serialize_match(db, match, current_user, detail=True)


@router.patch("/{match_id}", response_model=MatchDetailResponse)
def update_existing_match(match_id: int, match_in: MatchUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    match = match_service.update_match(db, match_id, match_in, current_user)
    return match_service.serialize_match(db, match, current_user, detail=True)


@router.post("/{match_id}/regenerate-invite-code", response_model=InviteCodeResponse)
def regenerate_match_invite_code(match_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    match = match_service.regenerate_invite_code(db, match_id, current_user)
    return {"invite_code": match.invite_code}


@router.post("/{match_id}/cancel", response_model=MatchDetailResponse)
def cancel_existing_match(match_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    match = match_service.cancel_match(db, match_id, current_user)
    return match_service.serialize_match(db, match, current_user, detail=True)


@router.post("/{match_id}/complete", response_model=MatchDetailResponse)
def complete_existing_match(match_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    match = match_service.complete_match(db, match_id, current_user)
    return match_service.serialize_match(db, match, current_user, detail=True)


@router.post("/{match_id}/join-requests", response_model=MatchJoinRequestResponse, status_code=status.HTTP_201_CREATED)
def create_join_request_endpoint(
    match_id: int,
    request_in: MatchJoinRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return match_service.create_join_request(
        db, match_id, current_user, position_code=request_in.position_code
    )


@router.post("/{match_id}/join-requests/{request_id}/withdraw", response_model=MatchJoinRequestResponse)
def withdraw_join_request_endpoint(
    match_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return match_service.withdraw_join_request(
        db, request_id, current_user, expected_match_id=match_id
    )


@router.post("/{match_id}/join-requests/{request_id}/approve", response_model=MatchJoinRequestResponse)
def approve_join_request_endpoint(
    match_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return match_service.approve_join_request(
        db, request_id, current_user, expected_match_id=match_id
    )


@router.post("/{match_id}/join-requests/{request_id}/reject", response_model=MatchJoinRequestResponse)
def reject_join_request_endpoint(
    match_id: int,
    request_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return match_service.reject_join_request(
        db, request_id, current_user, expected_match_id=match_id
    )


@router.get("/{match_id}/join-requests", response_model=list[MatchJoinRequestResponse])
def list_match_join_requests_endpoint(
    match_id: int,
    status_filter: MatchJoinRequestStatus | None = Query(default=None, alias="status"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return match_service.list_match_join_requests(
        db, match_id, current_user, status_filter, skip, limit
    )

