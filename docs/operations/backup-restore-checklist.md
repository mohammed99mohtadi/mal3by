# Backup and Restore Checklist

Status at audit: repository evidence does not prove automated PostgreSQL backups, retention, RPO/RTO, pre-migration snapshots, or test restores. Complete and attach evidence before accepting real payments. Do not place credentials, connection strings, encryption keys, or customer data in this document.

## Ownership and objectives

- [ ] Name primary and backup database operators.
- [ ] Approve an RPO (starting proposal: ≤ 15 minutes for paid-booking data).
- [ ] Approve an RTO (starting proposal: ≤ 4 hours).
- [ ] Define incident commander, communications owner, and payment-reconciliation owner.
- [ ] Record database engine/version, region, high-availability mode, and hosting backup capability.

## Backup configuration

- [ ] Enable automated encrypted PostgreSQL backups.
- [ ] Enable point-in-time recovery/WAL retention where supported.
- [ ] Set documented retention tiers (starting proposal: 7 daily, 4 weekly, 12 monthly, subject to legal/privacy review).
- [ ] Store copies in a separate failure domain/account where practical.
- [ ] Verify encryption at rest/in transit and tightly scoped restore permissions.
- [ ] Alert on missed, failed, unusually small, or overdue backups.
- [ ] Inventory non-database state needed for recovery; store configuration references, not secrets.
- [ ] Define deletion/privacy handling for retained backups.

## Before every production migration

- [ ] Confirm current deployed Alembic revision and expected single target head.
- [ ] Review upgrade and downgrade for locks, table rewrites, backfills, enum/default/constraint behavior, and data loss.
- [ ] Run migration against a recent sanitized production-shaped restore in staging.
- [ ] Run duplicate/null/value preflight queries required by new constraints.
- [ ] Confirm a recent successful backup and PITR coverage immediately before deployment.
- [ ] Identify the exact recovery timestamp and release identifier.
- [ ] Agree rollback decision point. Prefer forward fix; downgrade only when explicitly data-safe.
- [ ] Pause risky writers or use an expand/contract rollout when required.
- [ ] Record approver and evidence links outside this repository.

## Restore drill

- [ ] Provision an isolated non-production target with network access restricted.
- [ ] Restore the selected full backup and replay logs to the chosen recovery point.
- [ ] Never overwrite production during a drill.
- [ ] Validate database version/extensions, row counts, constraints, indexes, owners, time zones, and Alembic revision.
- [ ] Run integrity checks for users, courts, bookings, matches, participants, join requests, reviews, price snapshots, and future payment records.
- [ ] Verify no active overlapping bookings after the concurrency invariant exists.
- [ ] Start the application against the isolated restore using non-production secrets.
- [ ] Run smoke tests: health/readiness, login, booking read, availability, private match access, owner/admin authorization.
- [ ] Measure recovery point achieved and elapsed recovery time against RPO/RTO.
- [ ] Reconcile sampled payment-provider records against restored payment/booking state once payments exist.
- [ ] Destroy or sanitize the isolated restore according to data policy.
- [ ] Document failures, owner, due date, and rerun result.

## Incident restore sequence

1. Declare incident and stop unsafe writes if continued writes worsen loss.
2. Preserve logs, deployment identifiers, Alembic revision, and recovery timeline.
3. Select the recovery point; get two-person approval for destructive production restore/failover.
4. Restore to a new isolated database first and validate integrity.
5. Repoint only through the approved deployment process; do not expose credentials in commands or tickets.
6. Run readiness and business smoke checks.
7. Reconcile bookings, payments, refunds, and notifications created near the recovery point.
8. Communicate known data-loss window and customer remediation.
9. Monitor errors, latency, overlap conflicts, and payment mismatches.
10. Complete post-incident review and improve the runbook.

## Schedule and evidence

- [ ] Daily automated backup success review/alerting.
- [ ] Monthly restore drill until three consecutive successes; quarterly thereafter.
- [ ] Pre-payment full restore and reconciliation exercise.
- [ ] Annual retention, access, encryption, and provider-exit review.
- [ ] Keep immutable evidence: backup ID/time, restore target, operator, duration, achieved RPO/RTO, checksums/counts, test output, exceptions, and approval.

Payment launch gate: all ownership, automated backup, pre-migration, restore drill, RPO/RTO, alerting, and reconciliation items must be complete and evidenced.
