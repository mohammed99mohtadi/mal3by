# Kuwait venue verification — P1

Verified on 2026-08-11. These are research records, not bookable inventory. The current `courts` table requires an internal owner, positive hourly price, and positive capacity; a record is not seeded until those required values are supported by a source and the venue authorizes onboarding.

| Venue/court | Source | Verified fields | Still missing for safe seed |
|---|---|---|---|
| The Padel Club — Mahboula indoor courts | [Official price notice](https://www.thepadelclub.com/NewsItem.aspx?id=7eabbf518c8c293eb694f8db97130ea2&return_url=%2Findex.aspx) | Mahboula; indoor padel; 15 KWD per 90 minutes; fixed/regular booking; high ceiling | Exact court names/count, address, coordinates, capacity confirmation, current-price confirmation, onboarding owner |
| The Padel Club — Mahboula outdoor courts | [Official news archive](https://www.thepadelclub.com/News.aspx) | Mahboula; four outdoor padel courts; booking through official app/site | Public price, exact address, coordinates, capacity confirmation, onboarding owner |
| The Padel Club — Bibi Complex courts | [Official news archive](https://www.thepadelclub.com/News.aspx) | Bibi Complex; at least two padel courts; discounted bookings of 20 KWD before 4pm (booking duration not stated) | Area/address, coordinates, hourly price, capacity confirmation, onboarding owner |
| The Padel Club — Space Arena Court 3 | [Official news archive](https://www.thepadelclub.com/News.aspx) | Space Arena; Court 3; private indoor padel; 90-minute bookings; high ceiling; PRO TURF | Area/address, coordinates, public price, capacity confirmation, onboarding owner |
| Kuwait Tennis Federation complex | [Official contact page](https://www.tenniskuwait.com.kw/en/contact) | Sheikh Jaber Al Abdullah Al Jaber Al Sabah International Tennis Complex; Zahra Block 7; phone/WhatsApp +965 22223800 | Public court price, individual court identity, capacity, coordinates, onboarding owner |

## Shared official contact and booking information

- The Padel Club official site publishes booking through its website/app and `+965 22270144`: [official site](https://thepadelclub.com/).
- No venue photograph was copied. Until venue-provided reusable photography is available, the product uses an explicitly labelled MAL3ABY fallback state.
- No coordinates were imported because an authoritative, exact coordinate pair was not confirmed for each court.
- The Mahboula 15 KWD/90-minute price was not converted into `price_per_hour`: doing so would change the source’s booking-unit meaning and could present stale pricing as live inventory.

