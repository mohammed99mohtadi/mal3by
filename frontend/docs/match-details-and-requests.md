# CM2 backend integration

- Detail: authenticated `GET /matches/{id}`. Private strangers receive the same 404 presentation as missing matches.
- Player mutations: `POST /join`, `/leave`, `/join-requests`, and pending-request `/withdraw` through the authenticated frontend proxy.
- Organiser reads: pending join requests and participant roster are fetched only when `can_manage` is true. Approve/reject mutations use the same proxy.
- User pages: created, joined, and join-request lists request the backend maximum page size (100). No total count or cursor is exposed, so no fake pagination is rendered.
- Position requirements exist in storage and join payload validation, but current match responses do not serialize them. UI renders/selects positions only if real response data becomes available; it never fabricates requirements or filled counts.
- Detail participants contain no names for ordinary users. Manager-only `/participants` supplies display names; UI never exposes email, phone, reviewer identity, or invite codes.
- Join-request responses contain `match_id`, not match title. My Requests resolves viewable titles through real detail calls and falls back to a localized match reference when privacy prevents access.
