# Mal3by Frontend

Next.js App Router frontend for Arabic and English court discovery.

## Setup

Copy `.env.example` to `.env.local`, set `NEXT_PUBLIC_API_BASE_URL`, then run:

```bash
npm run dev
npm run lint
npm run typecheck
npm run build
```

Run the FastAPI backend on port 8000 first. The frontend uses actual court, review, rating-summary, availability, authentication, and current-user APIs.

## Authentication

FastAPI currently returns bearer tokens only. Next.js route handlers exchange login credentials with FastAPI and store the access token in an HttpOnly, SameSite=Lax cookie. Client JavaScript never reads the token and no token is stored in localStorage. Secure is enabled in production. Because this is a cookie bridge, production deployment should keep the frontend origin trusted and assess CSRF protections before adding state-changing proxy routes.

## Scope

Included: locale routes `/ar` and `/en`, login, registration, profile, court discovery, court details, availability preview, public reviews, and rating summaries.

Not included: booking checkout, My Bookings, match UI, review creation UI, owner dashboard, payments, or notifications.
