# ADR 0002: Capacity Approval

Status: accepted. Approval locks the match row, checks approved count, writes participant/request state and refreshes status in one transaction. Alternatives optimistic client counts or separate capacity cache were rejected. Consequence: predictable 409 on final-slot races.
