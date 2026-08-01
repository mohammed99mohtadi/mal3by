# Monitoring and Logging Plan

Status at audit: no application structured logging, request IDs, metrics, security audit stream, or production error-monitoring integration was found. Alembic logging alone is not operational coverage. This plan adds no dependency by itself.

## Principles

- Emit structured JSON in production; human-readable logs may remain local-only.
- Generate/accept a validated request ID at the edge and return it in responses.
- Use stable event names/error codes, not message parsing.
- Log identifiers needed for correlation: request ID, route template, method, status, duration, actor/user ID when authenticated, court/booking/match/request IDs, deployment version.
- Redact by default. Never log passwords, JWTs, cookies, authorization headers, invite codes, payment secrets, webhook signatures, database URLs, raw request bodies, or full email/phone values.
- Keep security/audit events append-only and access-controlled; application debug logs are not an audit trail.

## Required events

| Domain | Events / safe fields |
|---|---|
| HTTP | request completed/failed; route template, status, latency, response size, request ID |
| Authentication | login success/failure, registration outcome, inactive-user rejection, role change; pseudonymous account/IP key, never credential |
| Booking | hold attempted/created/conflicted/expired, confirm attempted/succeeded/rejected, cancel, completion, refund; booking/court/actor IDs, old/new status, safe reason code |
| Payment | intent/event received, signature valid/invalid, amount/currency match, duplicate event, reconciliation mismatch; provider object IDs only if policy permits |
| Match | private access denied, join-code failure, join request/decision, cancellation; IDs and actor, no invite code |
| Authorization | denied action with route, object type/ID and actor; avoid confirming private object existence in response |
| Background jobs | job start/end/failure/retry/dead-letter; event/job ID and attempt |
| Migration/deploy | release, expected/current Alembic head, start/end/failure |

## Metrics and service levels

- HTTP request rate, error rate and latency by route template/status; never label by raw URL or user ID.
- 5xx rate and exception fingerprint.
- Booking hold attempts, successes, 409 conflicts, validation failures, active holds, expirations and confirmation/cancellation failures.
- Overlap-invariant violations: target zero; alert immediately.
- Availability latency and query count; initial p95 target < 300 ms on agreed production-shaped dataset.
- Authentication failures and throttled requests.
- Payment intent/webhook success, signature failures, amount mismatch, duplicate events, time-to-confirm, refund failures, reconciliation backlog.
- Outbox pending age, retry count, dead-letter count, delivery latency.
- Database connection saturation, transaction latency, deadlocks, lock waits, slow queries, storage and replication/PITR lag.
- Backup age/success and last successful restore-drill age.

## Alerts

| Alert | Initial trigger | Response |
|---|---|---|
| API 5xx | >2% for 5 minutes or sharp baseline deviation | Page on-call; inspect release/request IDs |
| Booking failures | Conflict/failure rate above expected baseline for 10 minutes | Check DB locks, overlap invariant, availability latency |
| Double-book invariant | Any committed invariant violation or constraint unexpectedly disabled | Page immediately; consider pausing booking writes |
| Payment mismatch | Any amount/currency/signature mismatch | Page payment owner; do not confirm booking |
| Payment processing | Failure >1% for 5 minutes or reconciliation backlog beyond SLA | Page before customer impact grows |
| Slow DB/query | p95 threshold breached 15 minutes, lock wait/deadlock spike | Inspect query plans/transactions |
| Backup | Failed/missed backup or backup age beyond RPO | Page database operator |
| Readiness | Consecutive failures in two regions/probes | Roll back/fail over per runbook |
| Security abuse | Login/join-code/hold throttling spike | Investigate source and tune controls |

Thresholds must be tuned from real baseline data and traffic; avoid alerting on user IDs or other high-cardinality labels.

## Error monitoring and traces

- Integrate Sentry or an equivalent approved service only after privacy, region, sampling, retention, and source-map review.
- Capture unhandled exceptions with release/environment/request ID and scrub request headers, cookies, bodies, PII, invite codes, and payment data before transmission.
- Upload frontend source maps privately; do not expose them in public assets.
- Trace booking hold, availability, payment webhook, outbox, and database spans with sampling. Force sampling for errors and rare critical state transitions without capturing payloads.
- Separate liveness from readiness. Readiness should perform a bounded safe DB check and report only status, not connection details.

## Audit log

Persist security/business audit records for role changes, owner/admin booking changes, refunds, court deletion/deactivation, match moderation, and backup/restore actions. Include actor, action, target type/ID, old/new safe state, timestamp, request ID and source channel. Use explicit reason codes. Restrict access, define retention, and make tampering detectable. Do not store secret values or unnecessary PII.

## Rollout

1. Define event dictionary, redaction tests, ownership, retention, and request-ID propagation.
2. Add structured backend logs and safe frontend/proxy error correlation.
3. Add booking/auth metrics and database dashboards.
4. Add error monitoring with scrub tests.
5. Add payment/outbox metrics before those features launch.
6. Configure alerts, exercise them in staging, and record runbooks/escalation paths.
7. Review monthly for missing fields, secret leakage, high cardinality, cost, and alert quality.

## Acceptance checklist

- [ ] Request ID crosses edge, frontend proxy, backend, job, and response.
- [ ] Automated tests prove redaction of tokens, cookies, passwords, invite codes, PII, DB URLs, and payment secrets.
- [ ] Booking transitions and authorization denials emit stable events.
- [ ] Dashboards cover API, booking, database, background jobs, payments, and backups.
- [ ] 5xx, overlap, payment mismatch, slow-query, readiness, and backup alerts have owners/runbooks.
- [ ] A staging exercise proves alert receipt and request-to-database correlation.
- [ ] Retention/access/privacy rules are approved.
