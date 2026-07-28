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
pytest -v
```

## API Endpoints Overview

- **Auth**: `POST /api/v1/auth/register`, `POST /api/v1/auth/login`
- **Users**: `GET /api/v1/users/me`
- **Sports**: `POST /api/v1/sports` (Admin), `GET /api/v1/sports`, `GET /api/v1/sports/{id}`
- **Courts**: `POST /api/v1/courts` (Owner/Admin), `GET /api/v1/courts`, `GET /api/v1/courts/{id}`, `PATCH /api/v1/courts/{id}`, `DELETE /api/v1/courts/{id}`
- **Admin**: `PATCH /api/v1/admin/users/{user_id}/role` (Admin only)
