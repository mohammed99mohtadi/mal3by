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

### Management API Endpoints (`/api/v1/courts/{court_id}/availability-settings`)
- `GET /rules`: Get court availability rules.
- `PUT /rules`: Create/update rules (Admin or Court Owner).
- `GET /working-hours`: Get working hours.
- `PUT /working-hours/{weekday}`: Upsert working hours for a weekday (Admin or Court Owner).
- `DELETE /working-hours/{weekday}`: Delete working hours for a weekday (Admin or Court Owner).
- `GET /closures`: Get court closures (optional `start_range` & `end_range` filters).
- `POST /closures`: Create a closure (Admin or Court Owner, 201 Created).
- `PATCH /closures/{closure_id}`: Update a closure (Admin or Court Owner).
- `DELETE /closures/{closure_id}`: Delete a closure (Admin or Court Owner, 204 No Content).

### Public Slot Generation Endpoint
- `GET /api/v1/courts/{court_id}/available-slots`
  - Query parameters: `date` (YYYY-MM-DD), `duration_minutes` (int), optional `start_time`, `end_time`.
  - Returns calculated slots with price and availability status.

### Example Requests

#### Configure Working Hours (Friday Overnight)
`PUT /api/v1/courts/1/availability-settings/working-hours/4`
```json
{
  "weekday": 4,
  "opens_at": "18:00:00",
  "closes_at": "02:00:00",
  "is_closed": false
}
```

#### Create Maintenance Closure
`POST /api/v1/courts/1/availability-settings/closures`
```json
{
  "start_time": "2026-08-10T08:00:00Z",
  "end_time": "2026-08-10T14:00:00Z",
  "reason": "Court Resurfacing",
  "closure_type": "maintenance"
}
```

#### Query Public Available Slots
`GET /api/v1/courts/1/available-slots?date=2026-08-10&duration_minutes=60`

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
