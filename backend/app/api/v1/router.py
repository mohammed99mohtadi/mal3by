from fastapi import APIRouter

from app.api.v1.endpoints import admin, auth, availability, bookings, courts, matches, owner, pricing, reviews, sports, users

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(sports.router, prefix="/sports", tags=["sports"])
api_router.include_router(courts.router, prefix="/courts", tags=["courts"])
api_router.include_router(availability.router, prefix="/courts", tags=["availability"])
api_router.include_router(pricing.router, prefix="/courts", tags=["pricing"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(bookings.router, prefix="/bookings", tags=["bookings"])
api_router.include_router(owner.router, prefix="/owner", tags=["owner-management"])
api_router.include_router(matches.router, prefix="/matches", tags=["matches"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["reviews"])
api_router.include_router(reviews.court_router, prefix="/courts", tags=["reviews"])
api_router.include_router(reviews.admin_router, prefix="/admin/reviews", tags=["review-moderation"])
