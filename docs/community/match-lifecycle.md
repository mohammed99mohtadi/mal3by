# Lifecycles

`draft -> open -> full -> open` on approved withdrawal; `open|full -> cancelled`; `open|full -> completed` only after end time and result submission. Completed is immutable except admin correction. Cancel emits roster notifications.

Join status: `pending -> approved|rejected|withdrawn|expired`. Approval atomically inserts/updates approved participant and checks capacity. Host is inserted as approved at creation, never requests normally. Unique constraints and a locked match row prevent oversubscription.
