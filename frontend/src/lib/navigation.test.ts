import { describe, expect, it } from "vitest";
import { activeSection, localeHref, stripLocale } from "./navigation";

describe("navigation helpers", () => {
  it("strips locale and ignores query", () => expect(stripLocale("/ar/courts/8?date=1")).toBe("/courts/8"));
  it.each([["/en", "home"], ["/ar/courts/8", "courts"], ["/en/bookings/9", "bookings"], ["/ar/matches/3", "matches"], ["/en/profile", "profile"]])("matches %s", (path, section) => expect(activeSection(path)).toBe(section));
  it("keeps valid booking selection", () => expect(localeHref("/ar/bookings/new", "en", new URLSearchParams({ courtId: "4", start: "2030-01-01T10:00:00Z", end: "2030-01-01T11:00:00Z" }))).toContain("courtId=4"));
  it("drops unsafe redirect and invalid IDs", () => expect(localeHref("/ar/bookings/new", "en", new URLSearchParams({ returnTo: "//evil", courtId: "x" }))).toBe("/en/bookings/new"));
});
