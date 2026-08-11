---
name: mal3aby-backend
description: Implement and review MAL3ABY's FastAPI, Pydantic, and SQLAlchemy backend using its router-service-model/schema architecture. Use for API endpoints, authentication, authorization, validation, errors, transactions, domain services, or backend tests.
---

# MAL3ABY Backend

- Register versioned routers through `app/api/v1/router.py`; keep handlers thin: dependencies, transport validation, service call, response model.
- Put business rules and transactions in `app/services`. The repositories package is empty; do not invent a repository layer for one change or move logic into handlers.
- Use Pydantic for API boundaries and SQLAlchemy models for persistence. Inspect matching models, schemas, services, endpoints, migrations, and tests before changing contracts.
- Keep bcrypt/JWT primitives in `core/security.py` and bearer resolution/role dependencies in `api/dependencies.py`.
- Reuse current-user, owner, admin, and court-owner dependencies rather than duplicating authorization.
- Public registration always creates active `PLAYER` with `is_admin=False`; never accept public role escalation.
- Keep secrets, password hashes, and internal errors out of responses/logs. Current default secret and non-revocable JWTs are debt, not patterns.
- Validate shape with Pydantic and cross-record invariants in services plus database constraints.
- Return intentional status codes and safe stable errors; preserve authorization/not-found/conflict distinctions.
- Make multi-write operations atomic; commit after invariants, rollback failures, and refresh returned records as needed.
- Preserve existing ownership, lifecycle, availability, pricing, and match rules. Avoid unrelated refactors.
- Write a failing pytest before behavior changes; cover success, validation, authn/authz, ownership, conflicts, rollback, and field exposure.
- Pair with database, booking, testing, and explicit security skills as applicable.
