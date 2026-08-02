import { describe, expect, it } from "vitest";
import { courtBackendQuery, courtPublicQuery, parseCourtFilters } from "./court-discovery";

describe("C1 court query safety", () => {
  it("serializes only supported backend filters", () => {
    const filters = parseCourtFilters({ search: "Real", area: "Salmiya", min: "10", max: "25.5", active: "true", page: "2", admin: "yes" });
    expect(courtBackendQuery(filters).toString()).toBe("search=Real&area=Salmiya&min_price=10&max_price=25.5&is_active=true&skip=12&limit=13");
    expect(courtPublicQuery(filters)).not.toContain("admin");
  });
  it("supports a safe sport filter and discards unsafe values", () => {
    expect(parseCourtFilters({ sport_id: "7" }).sportId).toBe("7");
    expect(parseCourtFilters({ min: "-1", max: "1e9", active: "yes", page: "oops", search: ["ok", "bad"] })).toEqual({ search: "ok", area: "", min: "", max: "", active: "", sportId: "", page: 1 });
  });
  it("caps text and page inputs", () => {
    const result = parseCourtFilters({ search: "x".repeat(200), page: "999999" });
    expect(result.search).toHaveLength(100);
    expect(result.page).toBe(10000);
  });
});
