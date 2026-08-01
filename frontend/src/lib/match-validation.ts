import type { Match, MatchJoinRequest, MatchParticipant } from "@/lib/types";

const object = (value: unknown): value is Record<string, unknown> => Boolean(value) && typeof value === "object";

export function isMatch(value: unknown): value is Match {
  if (!object(value) || !object(value.court) || !object(value.creator)) return false;
  return Number.isInteger(value.id) && typeof value.title === "string" && typeof value.sport_type === "string" &&
    typeof value.start_time === "string" && typeof value.end_time === "string" && typeof value.max_players === "number" &&
    typeof value.approved_participant_count === "number" && typeof value.available_spots === "number" &&
    typeof value.court.name_en === "string" && typeof value.court.name_ar === "string" && typeof value.creator.full_name === "string";
}
export function isMatchArray(value: unknown): value is Match[] { return Array.isArray(value) && value.every(isMatch); }
export function isJoinRequest(value: unknown): value is MatchJoinRequest {
  return object(value) && Number.isInteger(value.id) && Number.isInteger(value.match_id) && Number.isInteger(value.user_id) &&
    ["pending", "approved", "rejected", "withdrawn", "expired"].includes(String(value.status)) && typeof value.created_at === "string";
}
export function isJoinRequestArray(value: unknown): value is MatchJoinRequest[] { return Array.isArray(value) && value.every(isJoinRequest); }
export function isParticipantArray(value: unknown): value is MatchParticipant[] {
  return Array.isArray(value) && value.every((item) => object(item) && Number.isInteger(item.id) && Number.isInteger(item.user_id) &&
    ["pending", "approved", "rejected", "left"].includes(String(item.status)) && typeof item.created_at === "string" &&
    (item.user_name === undefined || typeof item.user_name === "string"));
}
