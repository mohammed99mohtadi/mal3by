import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProfileCard } from "./profile-card";

const user = { id: 77, full_name: "Mona Ali", email: "mona@example.com", phone_number: null, role: "owner", is_active: true, is_admin: false, created_at: "2025-01-01T00:00:00Z" };
describe("ProfileCard", () => {
  it("renders real profile data with isolated email and localized role", () => { const { container } = render(<ProfileCard locale="ar" user={user} />); expect(screen.getByText("Mona Ali")).toBeInTheDocument(); expect(container.querySelector("bdi[dir=ltr]")).toHaveTextContent("mona@example.com"); expect(screen.getByText("مالك ملعب")).toBeInTheDocument(); });
  it("provides localized booking and logout actions", () => { render(<ProfileCard locale="en" user={user} />); expect(screen.getByRole("link", { name: "My Bookings" })).toHaveAttribute("href", "/en/bookings"); expect(screen.getByRole("button", { name: "Log out" }).closest("form")).toHaveAttribute("action", "/api/auth/logout?locale=en"); });
  it("shows no edit, token, internal ID, or unsupported statistics", () => { render(<ProfileCard locale="en" user={user} />); expect(screen.queryByRole("button", { name: /edit/i })).toBeNull(); expect(screen.queryByText(/token|77|statistics/i)).toBeNull(); });
});
