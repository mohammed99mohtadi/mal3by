# MAL3AB Backend API

FastAPI backend service for MAL3AB sports court booking platform.

## Technology Stack
- Python 3.14
- FastAPI
- SQLAlchemy 2 & Alembic
- Pydantic v2
- SQLite (Development) / PostgreSQL (Production ready)
- JWT Authentication

## Environment Setup

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Virtual Environment & Dependencies:
   ```bash
   python -m venv .venv
   .\.venv\Scripts\activate
   pip install -r requirements.txt
   ```

## Database Migrations (Alembic)

To run migrations and bring the database to the latest schema:
```bash
alembic upgrade head
```

To view current migration revision:
```bash
alembic current
```

To view migration heads:
```bash
alembic heads
```

To create a new migration after model changes:
```bash
alembic revision --autogenerate -m "description_of_changes"
```

To seed default sports data (Football, Padel, Tennis, Basketball):
```bash
python -m app.db.seed
```

## Running the Server

Start the Uvicorn development server:
```bash
uvicorn app.main:app --reload --port 8000
```
Interactive API Documentation is accessible at `http://127.0.0.1:8000/docs`.

## Automated Testing

Run the full pytest suite (uses isolated in-memory database):
```bash
pytest -q
```

## Community Matches (Milestone 8)

Authenticated users can create a match from one of their own confirmed court bookings. A match copies the court sport and booking time, and a booking can be linked to only one match. The creator is recorded as an approved participant atomically with match creation.

### Lifecycle and participation

- Matches start as `open`, become `full` when approved participants reach capacity, and can be `cancelled` or `completed`.
- Join policies are `open` (immediate approval) and `approval_required` (pending creator/admin approval).
- Participant states are `pending`, `approved`, `rejected`, and `left`. Leaving preserves the participant record.
- Creators and admins can approve, reject, remove participants, update allowed pre-start fields, cancel, complete after the booking time ends, and regenerate private invite codes.
- Court owners do not gain match-management access solely through court ownership.

### Visibility and invite codes

- Public matches appear at `GET /api/v1/matches`.
- Private matches are hidden from unrelated users and require creator/admin/participant access, or a valid invite code where permitted.
- Private matches receive a server-generated unpredictable invite code. Codes are returned only on creation and regeneration, never by normal match retrieval or listing.
- `POST /api/v1/matches/join-by-code` joins a private match without exposing its code in public schemas.

### Booking integration

A match requires an active confirmed booking at creation. A later cancelled, expired, or otherwise non-confirmed linked booking blocks new joins. Cancelling a match does not cancel its booking; booking cancellation remains a separate booking operation. Production deployments should add periodic synchronization/notifications for booking changes and database locking appropriate to their database engine; SQLite cannot provide strong row-level locking for simultaneous final-slot joins.

### Match API overview

- `POST /api/v1/matches`, `GET /api/v1/matches`, `GET /api/v1/matches/{match_id}`
- `POST /api/v1/matches/{match_id}/join`, `POST /api/v1/matches/join-by-code`, `POST /api/v1/matches/{match_id}/leave`
- `PATCH /api/v1/matches/{match_id}`, `POST /api/v1/matches/{match_id}/cancel`, `POST /api/v1/matches/{match_id}/complete`
- `GET /api/v1/matches/me/created`, `GET /api/v1/matches/me/joined`
- Creator/admin participant management: `GET /api/v1/matches/{match_id}/participants` and approve, reject, remove actions.

Run match tests with:
```bash
pytest tests/test_matches.py -q
```

## Court Reviews (Milestone 9)

Players may create one verified 1-5 star review for their own booking only after it is `completed` and its end time has passed. Reviews are tied permanently to the booking, so soft-deleting a review does not allow another review for that booking.

Hidden reviews remain editable by their reviewer but cannot be republished by that reviewer. Removed or soft-deleted reviews cannot be edited.

Published, non-deleted reviews appear at `GET /api/v1/courts/{court_id}/reviews`; `GET /api/v1/courts/{court_id}/rating-summary` calculates the published rating distribution and average. Court owners may post one official response. Admins can hide, publish, or remove reviews. Hidden and removed reviews are excluded from public listings and aggregates.

Review APIs: `POST /api/v1/reviews`, `GET /api/v1/reviews/me`, `GET/PATCH/DELETE /api/v1/reviews/{review_id}`, response actions, and `/api/v1/admin/reviews/{review_id}/hide|publish|remove`.

---

## Court Pricing Engine (Milestone 5, Phase 1)

### Overview & Base Pricing
- **Base Price Fallback**: When a court has no active pricing rules or overrides, the fallback rate is `Court.price_per_hour`.
- **Proportional Calculation**: Bookings with fractional hours (e.g., 90 minutes = 1.5 hours) are calculated proportionally (`hourly_rate * duration_minutes / 60`).
- **KWD Precision**: All monetary totals and hourly rates are quantized to 3 decimal places using `ROUND_HALF_UP` (`Decimal("0.001")`).

### Rule Types
1. `fixed_hourly_price`: Replaces the current hourly rate during the matching interval (e.g. 15.000 KWD).
2. `percentage_adjustment`: Adjusts the hourly rate by a percentage (e.g. `+20.0` for +20% surge, `-10.0` for 10% discount).
3. `fixed_hourly_adjustment`: Adds or subtracts a fixed amount per hour (e.g. `+2.500` KWD or `-1.000` KWD).
- **Floor at Zero**: A calculated hourly rate can never become negative (floored at `0.000 KWD`).

### Rule Priority & Application Order
- Matching rules are sorted deterministically by:
  1. `priority` (ascending)
  2. `created_at` (ascending)
  3. `id` (ascending)
- **Precedence**: Date overrides use default `priority = 100` while recurring rules use default `priority = 0`. Lower numerical priority values are applied first (e.g. base price -> recurring fixed price at priority 10 -> holiday percentage increase at priority 100).

### Overnight Pricing & Multi-Segment Calculations
- **Overnight Time Ranges**: Supported for time ranges where `starts_at >= ends_at` (e.g., Thursday `22:00` to `02:00`). Thursday's rule applies continuously through Friday 02:00.
- **Interval Splitting**: Bookings spanning multiple rate intervals (e.g. 17:30 to 19:30 crossing an 18:00 peak boundary) or crossing midnight are split into sub-segments and calculated independently.

### Historical Price Snapshots
- When a booking is created, the backend calculates and stores:
  - `total_price` (Authoritative historical total)
  - `base_price_per_hour` (Court base price at calculation time)
  - `currency` (`KWD`)
  - `pricing_breakdown` (Detailed JSON breakdown of all sub-segments and applied rules)
  - `pricing_calculated_at` (UTC timestamp)
- **Immutable History**: Subsequent changes to court base prices or pricing rules do not affect historical booking records. Client-supplied total prices are ignored.

### Price Quote Endpoint (`POST /api/v1/courts/{court_id}/price-quote`)
- **Public & Informational**: Computes server-calculated price breakdown and informational availability status (`available: true/false`).
- **Important Note**: *A price quote is informational and does NOT reserve the court slot.*

### Pricing Management Endpoints (`/api/v1/courts/{court_id}/pricing`)
- `GET /rules`: List recurring pricing rules.
- `POST /rules`: Create recurring pricing rule (Admin or Court Owner, 201 Created).
- `GET /rules/{rule_id}`: Read single rule.
- `PATCH /rules/{rule_id}`: Update recurring pricing rule (Admin or Court Owner).
- `DELETE /rules/{rule_id}`: Delete recurring pricing rule (Admin or Court Owner, 204 No Content).
- `GET /date-overrides`: List date-specific overrides (optional `start_date` & `end_date` filters).
- `POST /date-overrides`: Create date override (Admin or Court Owner, 201 Created).
- `GET /date-overrides/{override_id}`: Read single override.
- `PATCH /date-overrides/{override_id}`: Update date override (Admin or Court Owner).
- `DELETE /date-overrides/{override_id}`: Delete date override (Admin or Court Owner, 204 No Content).

### Example Requests

#### Create Evening Peak Recurring Rule
`POST /api/v1/courts/1/pricing/rules`
```json
{
  "name": "Evening Peak",
  "rule_type": "fixed_hourly_price",
  "starts_at": "18:00:00",
  "ends_at": "22:00:00",
  "value": 15.0,
  "priority": 10
}
```

#### Create National Day Holiday Override
`POST /api/v1/courts/1/pricing/date-overrides`
```json
{
  "name": "National Day Holiday",
  "local_date": "2026-08-15",
  "override_type": "percentage_adjustment",
  "value": 25.0,
  "priority": 100
}
```

#### Request Price Quote
`POST /api/v1/courts/1/price-quote`
```json
{
  "start_time": "2026-08-15T17:30:00Z",
  "end_time": "2026-08-15T19:30:00Z"
}
```

---

## Court Availability Engine (Milestone 4, Phase 1)

### Core Concepts & Default Behavior
- **Default Backward Compatibility**: Existing courts without configured working hours are treated as open **24 hours / 7 days**.
- **Default Rule Settings**: Minimum booking 30 minutes, maximum booking 360 minutes (6 hours), interval 30 minutes, buffer 0 minutes, maximum advance booking 30 days, minimum advance booking 0 minutes, timezone `Asia/Kuwait`.

### Working Hours & Overnight Operating Rules
- Weekday conventions: `0=Monday`, `1=Tuesday`, `2=Wednesday`, `3=Thursday`, `4=Friday`, `5=Saturday`, `6=Sunday`.
- **Overnight Working Hours**: Supported when `opens_at >= closes_at` (e.g. Friday `18:00:00` to `02:00:00`). A booking on Friday evening or Saturday before 02:00 is allowed.

### Exception Closures
- Closure types: `maintenance`, `holiday`, `private_event`, `emergency`, `manual`.
- Bookings overlapping a closure are rejected (`HTTP 400 Bad Request`).

### Buffer Time & Alignment
- **Buffer Expansion**: When `buffer_minutes` is configured (e.g. 15 mins), an active booking `[10:00, 11:00]` blocks `[09:45, 11:15]`.
- Overlapping booking attempts return `HTTP 409 Conflict`.
- Bookings starting at exactly `11:15` (when interval aligns) are permitted.

### Timezone Normalization
- Storage: All database datetimes are stored in UTC.
- Evaluation: Working hours and slot generation evaluate local court date using the configured court IANA timezone (`Asia/Kuwait`).

---

## Booking System (Milestone 3)

### Booking Lifecycle Statuses
- `pending`: Initial status upon user booking creation. Blocks slot availability.
- `confirmed`: Admin or court owner confirmed the reservation. Blocks slot availability.
- `cancelled`: User, court owner, or admin cancelled the booking. Does NOT block slot availability.
- `completed`: Court reservation was fulfilled. Does NOT block slot availability.
- `rejected`: Court owner or admin rejected the booking. Does NOT block slot availability.

### Allowed Status Transitions Matrix
- `pending` -> `confirmed`, `rejected`, `cancelled`
- `confirmed` -> `completed`, `cancelled`
- Terminal states (`cancelled`, `completed`, `rejected`) cannot transition to any other status.
