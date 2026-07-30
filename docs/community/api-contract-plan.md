# API Contract Plan

Use `/api/v1/matches` existing resource: list (visibility/sport/area/date/status filters, cursor pagination), create, get, patch, cancel; participant join/withdraw/remove; manager pending-list/approve/reject; result submit; ratings create/list. Add `/players/{id}` and `/teams` resources later. All write endpoints authenticated, mass-assignment allowlisted, return 401/403/404/409/422 using existing `{detail}` errors. Idempotency key recommended for approvals/results.
