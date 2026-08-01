import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { HeaderNav } from "./header-nav";
import { BottomNavItems } from "./bottom-nav-items";
import { LocaleSwitcher } from "./locale-switcher";
import { SiteFooter } from "./site-footer";
import { UserMenu } from "./user-menu";

const route = vi.hoisted(() => ({ pathname: "/en", query: new URLSearchParams() }));
vi.mock("next/navigation", () => ({ usePathname: () => route.pathname, useSearchParams: () => route.query }));

describe("F2 navigation and layout", () => {
  beforeEach(() => { route.pathname = "/en"; route.query = new URLSearchParams(); });

  it("renders anonymous desktop navigation with Login and Register", () => {
    render(<HeaderNav locale="en" isLoggedIn={false} />);
    expect(screen.getByRole("link", { name: "Log in" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Create account" })).toBeInTheDocument();
    expect(screen.queryByLabelText("Open account menu")).toBeNull();
  });

  it("renders authenticated desktop navigation and user menu", () => {
    render(<HeaderNav locale="en" isLoggedIn userName="Mona" />);
    expect(screen.getByRole("link", { name: "Bookings" })).toBeInTheDocument();
    expect(screen.getByLabelText("Open account menu")).toHaveTextContent("M");
    expect(screen.queryByRole("link", { name: "Create account" })).toBeNull();
  });

  it("does not expose unsupported Matches or Owner destinations", () => {
    render(<HeaderNav locale="en" isLoggedIn userName="Owner" />);
    expect(screen.queryByRole("link", { name: /matches|community|owner/i })).toBeNull();
  });

  it("marks dynamic court route active", () => {
    route.pathname = "/en/courts/123"; render(<HeaderNav locale="en" isLoggedIn={false} />);
    expect(screen.getByRole("link", { name: "Courts" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "Home" })).not.toHaveAttribute("aria-current");
  });

  it("marks dynamic booking route active", () => {
    route.pathname = "/en/bookings/44/confirm"; render(<BottomNavItems locale="en" isLoggedIn />);
    expect(screen.getByRole("link", { name: "Bookings" })).toHaveAttribute("aria-current", "page");
  });

  it("renders natural Arabic labels and RTL mobile order", () => {
    route.pathname = "/ar"; render(<BottomNavItems locale="ar" isLoggedIn={false} />);
    expect(screen.getByRole("navigation", { name: "التنقل عبر الجوال" })).toHaveAttribute("dir", "rtl");
    expect(screen.getByRole("link", { name: "الرئيسية" })).toHaveAttribute("aria-current", "page");
    expect(screen.getByRole("link", { name: "الملاعب" })).toBeInTheDocument();
  });

  it("preserves dynamic path and allowlisted booking query", () => {
    route.pathname = "/ar/bookings/new"; route.query = new URLSearchParams({ courtId: "8", start: "2030-01-01T10:00:00Z", end: "2030-01-01T11:00:00Z" });
    render(<LocaleSwitcher locale="ar" />);
    expect(screen.getByRole("link", { name: "تغيير إلى الإنجليزية" }).getAttribute("href")).toContain("/en/bookings/new?courtId=8");
  });

  it("drops unsafe and unrelated query data", () => {
    route.pathname = "/ar/login"; route.query = new URLSearchParams({ returnTo: "https://evil.test", token: "secret" });
    render(<LocaleSwitcher locale="ar" />);
    expect(screen.getByRole("link", { name: "تغيير إلى الإنجليزية" })).toHaveAttribute("href", "/en/login");
  });

  it("user menu closes with Escape and returns focus", () => {
    render(<UserMenu locale="en" name="Mona" />); const trigger = screen.getByLabelText("Open account menu");
    fireEvent.click(trigger); expect(screen.getByRole("menu")).toBeInTheDocument(); fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("menu")).toBeNull(); expect(trigger).toHaveFocus();
  });

  it("user menu provides real logout action", () => {
    render(<UserMenu locale="en" name="Mona" />); fireEvent.click(screen.getByLabelText("Open account menu"));
    expect(screen.getByRole("menuitem", { name: "Log out" }).closest("form")).toHaveAttribute("action", "/api/auth/logout?locale=en");
  });

  it("footer exposes only supported localized links", () => {
    render(<SiteFooter locale="en" isLoggedIn />);
    expect(screen.getByRole("contentinfo", { name: "Site footer" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Courts" })).toHaveAttribute("href", "/en/courts");
    expect(screen.getByRole("link", { name: "My Bookings" })).toHaveAttribute("href", "/en/bookings");
    expect(screen.queryByRole("link", { name: /privacy|terms|social/i })).toBeNull();
  });
});
