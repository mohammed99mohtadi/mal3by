# C1 courts discovery

- Public source: `GET /api/v1/courts` with backend-supported `search`, `area`, `min_price`, `max_price`, `is_active`, `skip`, and `limit` parameters.
- Diagnosed local failure: no `frontend/.env.local` exists, so server fetch uses `http://127.0.0.1:8000/api/v1`; that endpoint was unreachable during diagnosis. Backend route and response contract exist and do not require authentication. Deployment must provide a reachable `NEXT_PUBLIC_API_BASE_URL` and running backend.
- Reads have an eight-second timeout and validate successful court arrays before rendering. UI never exposes internal URLs or backend error bodies.
- Pagination uses `limit + 1` for truthful previous/next controls. Backend provides no total count, so UI labels current-page results and never fabricates global totals.
- Court responses include real price, currency, sport, area, active state, and optional image. They do not include ratings, distance, facilities, or availability summaries; discovery cards omit those fields.
- Image URLs are backend-owned arbitrary URLs. `next/image` uses responsive sizing with `unoptimized` to avoid inventing a production host allowlist.
