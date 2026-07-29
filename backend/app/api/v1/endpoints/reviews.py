from fastapi import APIRouter, Depends, Query, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user, require_admin
from app.core.security import decode_access_token
from app.db.session import get_db
from app.models.review import ReviewStatus
from app.models.user import User
from app.schemas.review import CourtReviewCreate, CourtReviewManagementResponse, CourtReviewPublicResponse, CourtReviewResponseCreate, CourtReviewResponseUpdate, CourtReviewUpdate, ModerationRequest, RatingSummaryResponse
from app.services import review_service
from app.services.auth_service import get_user_by_id

router = APIRouter()
admin_router = APIRouter()
optional_oauth = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def optional_user(token: str | None = Depends(optional_oauth), db: Session = Depends(get_db)) -> User | None:
    if not token: return None
    payload = decode_access_token(token)
    user = get_user_by_id(db, int(payload["sub"])) if payload and payload.get("sub", "").isdigit() else None
    return user if user and user.is_active else None


@router.post("", response_model=CourtReviewManagementResponse, status_code=status.HTTP_201_CREATED)
def create_review(data: CourtReviewCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return review_service.serialize(review_service.create_review(db, user, data), management=True)


@router.get("/me", response_model=list[CourtReviewManagementResponse])
def my_reviews(status_filter: ReviewStatus | None = Query(None, alias="status"), court_id: int | None = Query(None, gt=0), skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return [review_service.serialize(item, management=True) for item in review_service.list_my_reviews(db, user, status_filter, court_id, skip, limit)]


@router.get("/{review_id}", response_model=CourtReviewPublicResponse | CourtReviewManagementResponse)
def review_detail(review_id: int, db: Session = Depends(get_db), user: User | None = Depends(optional_user)):
    review = review_service.view_review(db, review_id, user)
    management = user is not None and (user.id == review.reviewer_id or user.id == review.court.owner_id or review_service._admin(user))
    return review_service.serialize(review, management=management)


@router.patch("/{review_id}", response_model=CourtReviewManagementResponse)
def patch_review(review_id: int, data: CourtReviewUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return review_service.serialize(review_service.update_review(db, review_id, user, data), management=True)


@router.delete("/{review_id}", response_model=CourtReviewManagementResponse)
def remove_review(review_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return review_service.serialize(review_service.delete_review(db, review_id, user), management=True)


@router.post("/{review_id}/response", response_model=CourtReviewPublicResponse)
def create_response(review_id: int, data: CourtReviewResponseCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    review_service.owner_response(db, review_id, user, data)
    return review_service.serialize(review_service.get_review(db, review_id))


@router.patch("/{review_id}/response", response_model=CourtReviewPublicResponse)
def patch_response(review_id: int, data: CourtReviewResponseUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    review_service.owner_response(db, review_id, user, data, update=True)
    return review_service.serialize(review_service.get_review(db, review_id))


@router.delete("/{review_id}/response", status_code=status.HTTP_204_NO_CONTENT)
def remove_response(review_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    review_service.delete_owner_response(db, review_id, user)


@admin_router.post("/{review_id}/hide", response_model=CourtReviewManagementResponse)
def hide_review(review_id: int, data: ModerationRequest | None = None, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return review_service.serialize(review_service.moderate(db, review_id, user, "hide", data or ModerationRequest()), management=True)


@admin_router.post("/{review_id}/publish", response_model=CourtReviewManagementResponse)
def publish_review(review_id: int, data: ModerationRequest | None = None, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return review_service.serialize(review_service.moderate(db, review_id, user, "publish", data or ModerationRequest()), management=True)


@admin_router.post("/{review_id}/remove", response_model=CourtReviewManagementResponse)
def admin_remove_review(review_id: int, data: ModerationRequest | None = None, db: Session = Depends(get_db), user: User = Depends(require_admin)):
    return review_service.serialize(review_service.moderate(db, review_id, user, "remove", data or ModerationRequest()), management=True)


court_router = APIRouter()


@court_router.get("/{court_id}/reviews", response_model=list[CourtReviewPublicResponse])
def court_reviews(court_id: int, rating: int | None = Query(None, ge=1, le=5), minimum_rating: int | None = Query(None, ge=1, le=5), maximum_rating: int | None = Query(None, ge=1, le=5), verified_only: bool | None = None, has_comment: bool | None = None, sort: str = Query("newest", pattern="^(newest|oldest|highest_rating|lowest_rating)$"), skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    return [review_service.serialize(item) for item in review_service.list_court_reviews(db, court_id, rating, minimum_rating, maximum_rating, verified_only, has_comment, sort, skip, limit)]


@court_router.get("/{court_id}/rating-summary", response_model=RatingSummaryResponse)
def court_rating_summary(court_id: int, db: Session = Depends(get_db)):
    return review_service.rating_summary(db, court_id)
