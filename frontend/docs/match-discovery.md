# CM1 match discovery contract map

- Discovery: authenticated `GET /matches`; filters: `court_id`, `sport_type`, `skill_level`, `start_date`, `end_date`, `status`, `has_available_spots`, `sort`, `skip`, `limit`.
- Detail: authenticated `GET /matches/{match_id}`. Public/private visibility and invite access remain backend-authoritative.
- Create: `POST /matches`, backed by caller-owned confirmed booking.
- Current user: `GET /matches/me/created`, `/matches/me/joined`, `/matches/me/join-requests`.
- Participation: `POST /matches/{id}/join` or `/join-requests`; withdraw and manager approve/reject endpoints already exist through allowlisted frontend mutation proxy.
- Pagination: offset/limit bare array, no total count. CM1 requests 13 rows, displays 12, and exposes only verified previous/next boundaries. No page count is fabricated.
- Discovery response: title, sport, visibility, join policy, lifecycle, skill, capacity, times, creator, court names/area, participant count, available spots, current-user participation, management permission.
- Backend limitation: public response omits court image and `MatchPositionRequirement`. CM1 renders neutral image fallback and hides position chips. UI will render real requirements if schema later supplies them; no fake positions.
- Search limitation: backend has no text search. CM1 search is explicitly labelled as applying only to currently loaded page. Backend-supported filters remain server-side.
