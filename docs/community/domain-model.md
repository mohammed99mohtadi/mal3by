# Domain Model

Extend existing `Match`/`MatchParticipant`; do not create parallel `CommunityMatch` tables. Add `PlayerProfile(user_id unique, display_name, primary_sport_id nullable, skill_level, area, bio, avatar_url, is_public, timestamps)`, `MatchPositionRequirement(match_id, position, required_count check >0)`, `Team`, `TeamMember`, `MatchResult`, `PlayerRating`, and `Notification`.

Use integer IDs to match existing models. All child tables use FKs, timestamps, unique `(match_id,user_id)` participants and `(match_id,rater_id,rated_user_id)` ratings. No cascade from user/booking to historical matches; archive/soft-delete teams and profiles only where required. Index public match discovery `(visibility,status,scheduled_at)`, participant lookup `(user_id,status)`, notifications `(user_id,read_at,created_at)`.
