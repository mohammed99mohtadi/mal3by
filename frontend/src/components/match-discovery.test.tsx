import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { parseMatchFilters } from "@/lib/match-discovery";
import type { Match } from "@/lib/types";
import { MatchCard } from "./match-card";
import { MatchDiscoveryError } from "./match-discovery-error";
import { MatchDiscoveryFilters } from "./match-discovery-filters";
import { MatchPagination } from "./match-pagination";

const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));

const match = {
  id: 7, title: "Real Match", description: null, sport_type: "football",
  visibility: "public", join_policy: "approval_required", status: "open",
  skill_level: "intermediate", min_players: 2, max_players: 10,
  start_time: "2030-01-01T10:00:00Z", end_time: "2030-01-01T11:00:00Z",
  created_at: "2029-01-01T00:00:00Z", creator: { id: 2, full_name: "Mona" },
  court: { id: 3, name_en: "Real Court", name_ar: "ملعب حقيقي", area: "Salmiya" },
  approved_participant_count: 4, available_spots: 6, has_joined: false,
  current_user_participant_status: null, can_manage: false, booking_id: 4,
} as Match;

describe("CM1 components", () => {
  it("renders real card data, localized status, capacity, positions, and detail link", () => {
    const positioned = { ...match, position_requirements: [{ position_code: "goalkeeper", required_count: 1 }] };
    render(<MatchCard locale="en" match={positioned} />);
    expect(screen.getByText("Real Match")).toBeInTheDocument();
    expect(screen.getByText(/4\/10/)).toBeInTheDocument();
    expect(screen.getByText(/Goalkeeper/)).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "View Match: Real Match" })).toHaveAttribute("href", "/en/matches/7");
    expect(screen.queryByRole("button", { name: /join/i })).toBeNull();
  });

  it("hides optional positions and localizes closed state", () => {
    render(<MatchCard locale="ar" match={{ ...match, status: "completed" }} />);
    expect(screen.getByText("منتهية")).toBeInTheDocument();
    expect(screen.queryByLabelText("المراكز المطلوبة")).toBeNull();
  });

  it("opens accessible mobile filter drawer", () => {
    render(<MatchDiscoveryFilters locale="en" filters={parseMatchFilters({ sport: "football" })} />);
    fireEvent.click(screen.getByRole("button", { name: /Open filters/ }));
    const drawer = screen.getByRole("dialog", { name: "Filters" });
    expect(within(drawer).getByLabelText("Search loaded results")).toBeInTheDocument();
  });

  it("renders active filter chip and reset links", () => {
    render(<MatchDiscoveryFilters locale="en" filters={parseMatchFilters({ sport: "football", status: "open" })} />);
    expect(screen.getByLabelText("Remove football").getAttribute("href")).not.toContain("sport=");
    expect(screen.getAllByRole("link", { name: "Reset filters" })[0]).toHaveAttribute("href", "/en/matches");
  });

  it("preserves filters across pagination and disables boundaries", () => {
    const { rerender } = render(<MatchPagination locale="en" filters={parseMatchFilters({ sport: "football" })} hasNext />);
    expect(screen.getByText("Previous")).toHaveAttribute("aria-disabled", "true");
    expect(screen.getByRole("link", { name: "Next" }).getAttribute("href")).toContain("sport=football");
    rerender(<MatchPagination locale="en" filters={parseMatchFilters({ page: "2" })} hasNext={false} />);
    expect(screen.getByRole("link", { name: "Previous" })).toBeInTheDocument();
    expect(screen.getByText("Next")).toHaveAttribute("aria-disabled", "true");
  });

  it("shows safe retryable alert", () => {
    render(<MatchDiscoveryError locale="en" kind="service" />);
    fireEvent.click(screen.getByRole("button", { name: "Retry" }));
    expect(refresh).toHaveBeenCalled();
    expect(screen.getByRole("alert")).not.toHaveTextContent(/sql|traceback/i);
  });
});
