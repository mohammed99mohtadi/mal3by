from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.booking import Booking, BookingStatus
from app.models.court import Court
from app.models.review import CourtReview, CourtReviewResponse, ReviewStatus
from app.models.user import User, UserRole
from app.schemas.review import CourtReviewCreate, CourtReviewResponseCreate, CourtReviewUpdate, ModerationRequest


def _now(): return datetime.now(timezone.utc)
def _aware(value): return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
def _status(value): return value if isinstance(value, ReviewStatus) else ReviewStatus(value)
def _admin(user): return user.role == UserRole.ADMIN or user.is_admin
def _query(): return select(CourtReview).options(joinedload(CourtReview.court), joinedload(CourtReview.booking), joinedload(CourtReview.reviewer), joinedload(CourtReview.response))
def _not_found(): return HTTPException(status_code=404, detail="Review not found")


def get_review(db: Session, review_id: int) -> CourtReview | None:
    return db.execute(_query().where(CourtReview.id == review_id)).unique().scalar_one_or_none()


def _owner_or_admin(review: CourtReview, user: User):
    if not (_admin(user) or review.court.owner_id == user.id):
        raise HTTPException(status_code=403, detail="Only the court owner or an administrator can manage this response")


def _public(review: CourtReview) -> bool:
    return _status(review.status) == ReviewStatus.PUBLISHED and review.deleted_at is None


def create_review(db: Session, user: User, data: CourtReviewCreate) -> CourtReview:
    booking = db.execute(select(Booking).options(joinedload(Booking.court)).where(Booking.id == data.booking_id)).scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.user_id != user.id:
        raise HTTPException(status_code=403, detail="You can only review your own booking")
    if booking.status != BookingStatus.COMPLETED or _aware(booking.end_time) > _now():
        raise HTTPException(status_code=409, detail="Review requires a completed booking whose end time has passed")
    if db.scalar(select(CourtReview.id).where(CourtReview.booking_id == booking.id)):
        raise HTTPException(status_code=409, detail="This booking has already been reviewed")
    review = CourtReview(court_id=booking.court_id, booking_id=booking.id, reviewer_id=user.id, rating=data.rating, comment=data.comment, status=ReviewStatus.PUBLISHED, is_verified_booking=True)
    try:
        db.add(review); db.commit()
    except IntegrityError:
        db.rollback(); raise HTTPException(status_code=409, detail="This booking has already been reviewed")
    return get_review(db, review.id)


def view_review(db: Session, review_id: int, user: User | None) -> CourtReview:
    review = get_review(db, review_id)
    if not review: raise _not_found()
    if not _public(review) and not (user and (user.id == review.reviewer_id or user.id == review.court.owner_id or _admin(user))):
        raise _not_found()
    return review


def list_court_reviews(db: Session, court_id: int, rating=None, minimum_rating=None, maximum_rating=None, verified_only=None, has_comment=None, sort="newest", skip=0, limit=20):
    if not db.get(Court, court_id): raise HTTPException(status_code=404, detail="Court not found")
    statement = _query().where(CourtReview.court_id == court_id, CourtReview.status == ReviewStatus.PUBLISHED, CourtReview.deleted_at.is_(None))
    if rating: statement = statement.where(CourtReview.rating == rating)
    if minimum_rating: statement = statement.where(CourtReview.rating >= minimum_rating)
    if maximum_rating: statement = statement.where(CourtReview.rating <= maximum_rating)
    if verified_only: statement = statement.where(CourtReview.is_verified_booking.is_(True))
    if has_comment: statement = statement.where(CourtReview.comment.is_not(None), CourtReview.comment != "")
    order = {"newest": CourtReview.created_at.desc(), "oldest": CourtReview.created_at.asc(), "highest_rating": CourtReview.rating.desc(), "lowest_rating": CourtReview.rating.asc()}[sort]
    return list(db.execute(statement.order_by(order).offset(skip).limit(limit)).unique().scalars())


def list_my_reviews(db: Session, user: User, status_filter=None, court_id=None, skip=0, limit=20):
    statement = _query().where(CourtReview.reviewer_id == user.id)
    if status_filter: statement = statement.where(CourtReview.status == status_filter)
    if court_id: statement = statement.where(CourtReview.court_id == court_id)
    return list(db.execute(statement.order_by(CourtReview.created_at.desc()).offset(skip).limit(limit)).unique().scalars())


def update_review(db: Session, review_id: int, user: User, data: CourtReviewUpdate) -> CourtReview:
    review = get_review(db, review_id)
    if not review: raise _not_found()
    if not (_admin(user) or review.reviewer_id == user.id): raise HTTPException(status_code=403, detail="Only the reviewer or an administrator can update this review")
    if review.reviewer_id != user.id and _admin(user): raise HTTPException(status_code=403, detail="Administrators moderate reviews instead of editing content")
    if _status(review.status) == ReviewStatus.REMOVED or review.deleted_at: raise HTTPException(status_code=409, detail="Removed review cannot be edited")
    for field, value in data.model_dump(exclude_unset=True).items(): setattr(review, field, value)
    db.commit(); return get_review(db, review.id)


def delete_review(db: Session, review_id: int, user: User) -> CourtReview:
    review = get_review(db, review_id)
    if not review: raise _not_found()
    if not (_admin(user) or review.reviewer_id == user.id): raise HTTPException(status_code=403, detail="Only the reviewer or an administrator can delete this review")
    if not review.deleted_at:
        review.status = ReviewStatus.REMOVED; review.deleted_at = _now(); db.commit()
    return get_review(db, review.id)


def owner_response(db: Session, review_id: int, user: User, data: CourtReviewResponseCreate, update=False) -> CourtReviewResponse:
    review = get_review(db, review_id)
    if not review: raise _not_found()
    _owner_or_admin(review, user)
    response = review.response
    if update:
        if not response or response.deleted_at: raise HTTPException(status_code=404, detail="Review response not found")
        response.response_text = data.response_text
    else:
        if response and not response.deleted_at: raise HTTPException(status_code=409, detail="Review already has an active response")
        if response: response.response_text, response.deleted_at = data.response_text, None
        else: response = CourtReviewResponse(review_id=review.id, owner_id=user.id, response_text=data.response_text); db.add(response)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Review already has an active response")
    db.refresh(response); return response


def delete_owner_response(db: Session, review_id: int, user: User):
    review = get_review(db, review_id)
    if not review or not review.response or review.response.deleted_at: raise HTTPException(status_code=404, detail="Review response not found")
    _owner_or_admin(review, user); review.response.deleted_at = _now(); db.commit()


def moderate(db: Session, review_id: int, user: User, action: str, data: ModerationRequest) -> CourtReview:
    if not _admin(user): raise HTTPException(status_code=403, detail="Only administrators can moderate reviews")
    review = get_review(db, review_id)
    if not review: raise _not_found()
    current = _status(review.status)
    target = {"hide": ReviewStatus.HIDDEN, "publish": ReviewStatus.PUBLISHED, "remove": ReviewStatus.REMOVED}[action]
    if action == "publish" and current != ReviewStatus.HIDDEN: raise HTTPException(status_code=409, detail="Only hidden reviews can be published")
    if action in ("hide", "remove") and current == ReviewStatus.REMOVED: raise HTTPException(status_code=409, detail="Removed review cannot be moderated")
    review.status, review.moderated_at, review.moderated_by_id, review.moderation_reason = target, _now(), user.id, data.moderation_reason
    if action == "remove": review.deleted_at = _now()
    db.commit(); return get_review(db, review.id)


def rating_summary(db: Session, court_id: int):
    if not db.get(Court, court_id): raise HTTPException(status_code=404, detail="Court not found")
    rows = db.execute(select(CourtReview.rating, func.count(CourtReview.id)).where(CourtReview.court_id == court_id, CourtReview.status == ReviewStatus.PUBLISHED, CourtReview.deleted_at.is_(None)).group_by(CourtReview.rating)).all()
    distribution = {rating: 0 for rating in range(1, 6)}
    for rating, count in rows: distribution[rating] = count
    total = sum(distribution.values()); weighted = sum(rating * count for rating, count in distribution.items())
    verified = db.scalar(select(func.count(CourtReview.id)).where(CourtReview.court_id == court_id, CourtReview.status == ReviewStatus.PUBLISHED, CourtReview.deleted_at.is_(None), CourtReview.is_verified_booking.is_(True))) or 0
    return {"average_rating": (Decimal(weighted) / Decimal(total)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) if total else Decimal("0.00"), "total_reviews": total, "verified_reviews": verified, "rating_distribution": {"one": distribution[1], "two": distribution[2], "three": distribution[3], "four": distribution[4], "five": distribution[5]}}


def serialize(review: CourtReview, management=False):
    response = review.response if review.response and not review.response.deleted_at and _public(review) else None
    data = {"id": review.id, "rating": review.rating, "comment": review.comment, "is_verified_booking": review.is_verified_booking, "created_at": _aware(review.created_at), "updated_at": _aware(review.updated_at), "reviewer": {"id": review.reviewer.id, "full_name": review.reviewer.full_name}, "owner_response": {"id": response.id, "response_text": response.response_text, "created_at": response.created_at, "updated_at": response.updated_at} if response else None}
    if management: data.update({"status": review.status, "deleted_at": review.deleted_at, "moderation_reason": review.moderation_reason, "booking_id": review.booking_id, "court_id": review.court_id})
    return data
