---
name: mal3aby-booking
description: Implement and review MAL3ABY court availability, pricing, booking holds and lifecycle, overlap protection, ownership, and booking-linked matches. Use for courts, availability rules, pricing rules, bookings, concurrency, or Kuwait time handling.
---

# MAL3ABY Booking

- Read affected court, availability, pricing, booking, and match models/schemas/services/endpoints and tests. The backend is business authority.
- Frontend availability and price are estimates until the backend validates and snapshots them. Never invent client-only business rules.
- Preserve authenticated booking ownership and owner/admin court authorization.
- Respect per-court duration bounds, interval, buffer, advance windows, weekly hours, closures, inactivity, elapsed slots, and active overlaps.
- Interpret schedules in the court timezone, default `Asia/Kuwait`; persist/transport aware instants and avoid naive comparisons.
- Expire outdated holds before availability/overlap decisions where the service requires it.
- Resolve date overrides and recurring pricing through `pricing_service`, including priority and validity.
- Use `Decimal`, three-decimal KWD, and existing rounding. Preserve total, base price, currency, breakdown, and calculation timestamp snapshots.
- Use only defined states: pending, pending_payment, confirmed, cancelled, expired, completed, rejected, refunded; permit service-approved transitions.
- Preserve hold expiry and lifecycle timestamps. Confirmation must revalidate state/hold as implemented.
- Keep the PostgreSQL active-booking exclusion constraint as final overlap guard and translate races into domain conflicts.
- A match links one-to-one to a booking and must preserve creator, court, time, status, capacity, participant, and join-policy rules.
- Test lifecycle, authorization, price snapshot, timezone, closure/hours, overlap, rollback, and PostgreSQL concurrency as applicable.
- Pair with backend, database, and testing skills.
