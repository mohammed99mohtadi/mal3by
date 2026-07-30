import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MatchExperience } from "@/components/match-experience";
import MatchLoading from "@/app/[locale]/matches/[matchId]/loading";
import { MatchFailure } from "@/app/[locale]/matches/[matchId]/page";
import type { Match, MatchJoinRequest } from "@/lib/types";

const baseMatch: Match = {
  id: 42,
  title: "Friday Football",
  description: "Friendly seven-a-side match.",
  sport_type: "football",
  visibility: "public",
  join_policy: "open",
  status: "open",
  skill_level: "all_levels",
  min_players: 8,
  max_players: 14,
  start_time: "2030-05-10T17:00:00Z",
  end_time: "2030-05-10T18:30:00Z",
  created_at: "2030-05-01T10:00:00Z",
  creator: { id: 1, full_name: "Mona Ali" },
  court: { id: 9, name_en: "Green Court", name_ar: "الملعب الأخضر", area: "Kuwait" },
  approved_participant_count: 7,
  available_spots: 7,
  has_joined: false,
  current_user_participant_status: null,
  can_manage: false,
  booking_id: 5,
};

const pendingRequest: MatchJoinRequest = {
  id: 70,
  match_id: 42,
  user_id: 12,
  status: "pending",
  created_at: "2030-05-01T11:00:00Z",
  updated_at: "2030-05-01T11:00:00Z",
  requester: { id: 12, full_name: "Omar Said" },
};

function response(data: unknown, ok = true) {
  return { ok, json: async () => data };
}

describe("MatchExperience", () => {
  beforeEach(() => vi.restoreAllMocks());

  it("renders match details with one heading and localized navigation-independent content", () => {
    const { container } = render(<MatchExperience locale="en" initialMatch={baseMatch} initialRequest={null} initialPendingRequests={[]} />);
    expect(screen.getByRole("heading", { level: 1, name: "Friday Football" })).toBeInTheDocument();
    expect(container.querySelectorAll("h1")).toHaveLength(1);
    expect(screen.getByText("Green Court")).toBeInTheDocument();
    expect(screen.getByText("Mona Ali")).toBeInTheDocument();
    expect(screen.getByText("Friendly seven-a-side match.")).toBeInTheDocument();
  });

  it("joins an open match and shows approved state", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({ ...baseMatch, has_joined: true, current_user_participant_status: "approved" })));
    render(<MatchExperience locale="en" initialMatch={baseMatch} initialRequest={null} initialPendingRequests={[]} />);
    fireEvent.click(screen.getByRole("button", { name: "Join match" }));
    await waitFor(() => expect(screen.getByText("You already joined this match.")).toBeInTheDocument());
    expect(fetch).toHaveBeenCalledWith("/api/matches/42/join", { method: "POST" });
  });

  it("renders pending request and withdraws it", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({ ...pendingRequest, status: "withdrawn" })));
    render(<MatchExperience locale="en" initialMatch={{ ...baseMatch, join_policy: "approval_required" }} initialRequest={pendingRequest} initialPendingRequests={[]} />);
    expect(screen.getByText("Your request is pending review.")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Withdraw request" }));
    await waitFor(() => expect(fetch).toHaveBeenCalledWith("/api/matches/42/join-requests/70/withdraw", { method: "POST" }));
  });

  it("lets organizer approve and reject pending requests after success", async () => {
    const second = { ...pendingRequest, id: 71, user_id: 13, requester: { id: 13, full_name: "Sara Noor" } };
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({ ...pendingRequest, status: "approved" })));
    render(<MatchExperience locale="en" initialMatch={{ ...baseMatch, can_manage: true }} initialRequest={null} initialPendingRequests={[pendingRequest, second]} />);
    fireEvent.click(screen.getByRole("button", { name: "Approve Omar Said" }));
    await waitFor(() => expect(screen.queryByText("Omar Said")).not.toBeInTheDocument());
    fireEvent.click(screen.getByRole("button", { name: "Reject Sara Noor" }));
    await waitFor(() => expect(screen.getByText("No pending requests")).toBeInTheDocument());
  });

  it("keeps organizer request on failure and focuses safe error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response({ detail: "raw backend error" }, false)));
    render(<MatchExperience locale="en" initialMatch={{ ...baseMatch, can_manage: true }} initialRequest={null} initialPendingRequests={[pendingRequest]} />);
    fireEvent.click(screen.getByRole("button", { name: "Approve Omar Said" }));
    await waitFor(() => expect(screen.getByRole("alert")).toHaveTextContent("Could not complete the action. Please try again."));
    expect(screen.getByText("Omar Said")).toBeInTheDocument();
    expect(screen.queryByText("raw backend error")).not.toBeInTheDocument();
  });

  it("renders Arabic labels", () => {
    render(<MatchExperience locale="ar" initialMatch={baseMatch} initialRequest={null} initialPendingRequests={[]} />);
    expect(screen.getByRole("button", { name: "انضم إلى المباراة" })).toBeInTheDocument();
    expect(screen.getByText("الملعب الأخضر")).toBeInTheDocument();
  });

  it("renders localized loading skeleton", async () => {
    render(await MatchLoading({ params: Promise.resolve({ locale: "en" }) }));
    expect(screen.getByRole("status")).toHaveTextContent("Loading match details");
  });

  it("provides localized recovery navigation for unauthorized and error states", () => {
    render(<MatchFailure locale="en" message="Log in to view match details." login />);
    expect(screen.getByRole("link", { name: "Log in" })).toHaveAttribute("href", "/en/login");
    expect(screen.getByRole("link", { name: "Back to courts" })).toHaveAttribute("href", "/en/courts");
  });
});
