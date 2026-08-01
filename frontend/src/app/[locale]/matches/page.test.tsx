import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { matchDiscoveryCopy } from "@/lib/match-discovery";
import type { Match } from "@/lib/types";
import Loading from "./loading";
import Matches from "./page";

vi.mock("next/headers", () => ({
  cookies: async () => ({ get: () => ({ value: "test-session" }) }),
}));
vi.mock("next/navigation", () => ({
  redirect: vi.fn(),
  useRouter: () => ({ refresh: vi.fn() }),
}));
vi.mock("@/lib/api", async (importOriginal) => {
  const original = await importOriginal<typeof import("@/lib/api")>();
  return { ...original, api: { ...original.api, matches: vi.fn() } };
});

const realMatch = {
  id: 51, title: "Friday Football", description: null, sport_type: "football",
  visibility: "public", join_policy: "approval_required", status: "open",
  skill_level: "all_levels", min_players: 2, max_players: 8,
  start_time: "2030-01-04T17:00:00Z", end_time: "2030-01-04T18:00:00Z",
  created_at: "2030-01-01T09:00:00Z", creator: { id: 3, full_name: "Noura" },
  court: { id: 5, name_en: "Salmiya Court", name_ar: "ملعب السالمية", area: "Salmiya" },
  approved_participant_count: 3, available_spots: 5, has_joined: false,
  current_user_participant_status: null, can_manage: false, booking_id: 9,
} as Match;

const renderPage = async (locale: "en" | "ar", searchParams = {}) =>
  render(await Matches({ params: Promise.resolve({ locale }), searchParams: Promise.resolve(searchParams) }));

describe("match discovery page", () => {
  beforeEach(() => vi.mocked(api.matches).mockReset());

  it.each(["en", "ar"] as const)("renders %s copy and real result count", async (locale) => {
    vi.mocked(api.matches).mockResolvedValue([realMatch]);
    await renderPage(locale);
    expect(screen.getByRole("heading", { level: 1, name: matchDiscoveryCopy[locale].title })).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(matchDiscoveryCopy[locale].results(1));
    expect(screen.getByText("Friday Football")).toBeInTheDocument();
  });

  it("separates empty and filtered no-result states", async () => {
    vi.mocked(api.matches).mockResolvedValue([]);
    const { unmount } = await renderPage("en");
    expect(screen.getByText(matchDiscoveryCopy.en.empty)).toBeInTheDocument();
    unmount();
    await renderPage("en", { sport: "football" });
    expect(screen.getByText(matchDiscoveryCopy.en.noResults)).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: matchDiscoveryCopy.en.reset }).length).toBeGreaterThan(0);
  });

  it("renders route loading state without fake match content", () => {
    render(<Loading />);
    expect(screen.getByRole("status")).toHaveAccessibleName(/Loading matches/);
    expect(screen.queryByText("Friday Football")).toBeNull();
  });
});
