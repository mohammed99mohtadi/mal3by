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

### Booking Rules & Overlap Logic
1. **Server-Side Pricing**: `total_price` is strictly computed on server (`Decimal(hours) * court.price_per_hour`). Client price parameters are ignored.
2. **Timezone Enforcement**: All booking start and end datetimes must be timezone-aware UTC datetimes.
3. **Duration Constraints**: Booking duration must be at least 30 minutes and no longer than 6 hours.
4. **Future Start**: Bookings cannot start in the past.
5. **Slot Overlap Prevention**: Active bookings (`pending` or `confirmed`) for the same court cannot overlap. Overlap is detected when:
   `existing.start_time < requested.end_time AND existing.end_time > requested.start_time`.
   Conflicting requests return `HTTP 409 Conflict`.
6. **Adjacent Bookings**: Bookings starting exactly when a prior booking ends are permitted.

### Example Booking Requests

#### Create Booking
`POST /api/v1/bookings`
```json
{
  "court_id": 1,
  "start_time": "2026-08-20T10:00:00Z",
  "end_time": "2026-08-20T12:00:00Z"
}
```

#### Check Court Availability
`GET /api/v1/bookings/availability/1?start_time=2026-08-20T10:00:00Z&end_time=2026-08-20T12:00:00Z`

#### User Cancel Booking
`POST /api/v1/bookings/1/cancel`
```json
{
  "cancellation_reason": "Weather conflict"
}
```

#### Admin/Owner Update Status
`PATCH /api/v1/bookings/1/status`
```json
{
  "status": "confirmed"
}
```

## API Endpoints Overview

- **Auth**: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`
- **Users**: `GET /api/v1/users/me`
- **Sports**: `POST /api/v1/sports` (Admin), `GET /api/v1/sports`, `GET /api/v1/sports/{id}`
- **Courts**: `POST /api/v1/courts` (Owner/Admin), `GET /api/v1/courts`, `GET /api/v1/courts/{id}`, `PATCH /api/v1/courts/{id}`, `DELETE /api/v1/courts/{id}`
- **Admin**: `PATCH /api/v1/admin/users/{user_id}/role` (Admin only)
- **Bookings**: `POST /api/v1/bookings`, `GET /api/v1/bookings/me`, `GET /api/v1/bookings/availability/{court_id}`, `GET /api/v1/bookings/{id}`, `POST /api/v1/bookings/{id}/cancel`, `PATCH /api/v1/bookings/{id}/status`
