from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.match import MatchJoinPolicy, MatchJoinRequestStatus, MatchStatus, MatchVisibility, ParticipantStatus, SkillLevel


class MatchCreate(BaseModel):
    booking_id: int = Field(gt=0)
    title: str = Field(min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    visibility: MatchVisibility = MatchVisibility.PUBLIC
    join_policy: MatchJoinPolicy = MatchJoinPolicy.OPEN
    skill_level: SkillLevel = SkillLevel.ALL_LEVELS
    min_players: int = Field(ge=2, le=100)
    max_players: int = Field(ge=2, le=100)

    @model_validator(mode="after")
    def validate_player_range(self) -> "MatchCreate":
        if self.min_players > self.max_players:
            raise ValueError("min_players cannot exceed max_players")
        return self


class MatchUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = Field(default=None, max_length=2000)
    visibility: MatchVisibility | None = None
    join_policy: MatchJoinPolicy | None = None
    skill_level: SkillLevel | None = None
    min_players: int | None = Field(default=None, ge=2, le=100)
    max_players: int | None = Field(default=None, ge=2, le=100)


class JoinByCodeRequest(BaseModel):
    invite_code: str = Field(min_length=16, max_length=128)


class MatchCreatorResponse(BaseModel):
    id: int
    full_name: str


class MatchCourtResponse(BaseModel):
    id: int
    name_en: str
    name_ar: str
    area: str


class MatchParticipantResponse(BaseModel):
    id: int
    user_id: int
    status: ParticipantStatus
    joined_at: datetime | None
    approved_at: datetime | None
    rejected_at: datetime | None
    left_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MatchParticipantManagementResponse(MatchParticipantResponse):
    user_name: str


class MatchPublicResponse(BaseModel):
    id: int
    title: str
    description: str | None
    sport_type: str
    visibility: MatchVisibility
    join_policy: MatchJoinPolicy
    status: MatchStatus
    skill_level: SkillLevel
    min_players: int
    max_players: int
    start_time: datetime
    end_time: datetime
    created_at: datetime
    creator: MatchCreatorResponse
    court: MatchCourtResponse
    approved_participant_count: int
    available_spots: int
    has_joined: bool
    current_user_participant_status: ParticipantStatus | None
    can_manage: bool


class MatchDetailResponse(MatchPublicResponse):
    booking_id: int
    pending_participant_count: int | None = None
    participants: list[MatchParticipantResponse] | None = None


class MatchCreateResponse(MatchDetailResponse):
    invite_code: str | None = None


class InviteCodeResponse(BaseModel):
    invite_code: str


class MatchJoinRequestCreate(BaseModel):
    position_code: str | None = Field(default=None, max_length=100)


class MatchJoinRequestUserResponse(BaseModel):
    id: int
    full_name: str

    model_config = ConfigDict(from_attributes=True)


class MatchJoinRequestResponse(BaseModel):
    id: int
    match_id: int
    user_id: int
    status: MatchJoinRequestStatus
    requested_position_code: str | None = None
    reviewed_by_user_id: int | None = None
    reviewed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    requester: MatchJoinRequestUserResponse | None = None

    model_config = ConfigDict(from_attributes=True)

