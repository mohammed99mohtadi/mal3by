---
name: mal3aby-database
description: Design, migrate, and review MAL3ABY persistence with SQLAlchemy, Alembic, PostgreSQL production semantics, and SQLite development compatibility. Use for models, constraints, indexes, relationships, migrations, transactions, concurrency, data integrity, or schema evolution.
---

# MAL3ABY Database

- Treat PostgreSQL as production authority and Supabase PostgreSQL as planned hosting; SQLite is a development/test convenience.
- Do not assume SQLite matches PostgreSQL timezone, numeric, locking, constraint, transaction, or concurrency behavior.
- Inspect relevant models, all related Alembic revisions, service transactions, and database-specific tests first.
- Use SQLAlchemy 2 typed mappings and the central declarative `Base`.
- Encode durable invariants with nullability, unique/check constraints, foreign keys, deletion policy, and query-driven indexes.
- Define relationship cardinality, cascade, and historical retention deliberately; avoid destructive cascades for operational/financial history without approved policy.
- Persist aware UTC instants; convert schedules through the configured court timezone, normally `Asia/Kuwait`.
- Store KWD money as `Decimal`/`Numeric(10, 3)`, never float booking totals.
- Create one focused Alembic revision with correct ancestry; review upgrade and downgrade manually.
- Phase backfills/nullability for populated tables and plan recovery for irreversible changes.
- Guard PostgreSQL-only DDL explicitly. The active-booking overlap exclusion constraint is the repository example.
- Verify Alembic current/heads, upgrade, and safe downgrade/re-upgrade when migrations change.
- Keep transactions in services, roll back failures, and use locks/database constraints for races; application pre-checks alone are insufficient.
- Test booking concurrency against PostgreSQL when overlap, hold, availability, or lifecycle persistence changes.
