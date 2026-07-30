import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";
import { HeaderNav } from "./header-nav";
import { BottomNavItems } from "./bottom-nav-items";
import { LocaleSwitcher } from "./locale-switcher";

vi.mock("next/navigation", () => ({
  usePathname: () => "/ar/courts/123",
}));

describe("Navigation Components Suite", () => {
  it("renders HeaderNav with active route indicator aria-current='page'", () => {
    render(<HeaderNav locale="ar" isLoggedIn={true} />);
    const activeLink = screen.getByRole("link", { name: "الملاعب" });
    expect(activeLink.getAttribute("aria-current")).toBe("page");
  });

  it("authenticated mobile navigation includes Profile and excludes Login", () => {
    render(<BottomNavItems locale="ar" isLoggedIn={true} />);
    expect(screen.getByRole("link", { name: "حسابي" })).toBeDefined();
    expect(screen.queryByRole("link", { name: "الدخول" })).toBeNull();
  });

  it("unauthenticated mobile navigation includes Login and excludes Profile", () => {
    render(<BottomNavItems locale="ar" isLoggedIn={false} />);
    expect(screen.getByRole("link", { name: "الدخول" })).toBeDefined();
    expect(screen.queryByRole("link", { name: "حسابي" })).toBeNull();
  });

  it("nested route /ar/courts/123 activates Courts and NOT Home", () => {
    render(<BottomNavItems locale="ar" isLoggedIn={true} />);
    const homeLink = screen.getByRole("link", { name: "الرئيسية" });
    const courtsLink = screen.getByRole("link", { name: "الملاعب" });
    expect(homeLink.getAttribute("aria-current")).toBeNull();
    expect(courtsLink.getAttribute("aria-current")).toBe("page");
  });

  it("renders LocaleSwitcher with target language label and preserves path", () => {
    render(<LocaleSwitcher locale="ar" />);
    const link = screen.getByRole("link", { name: "تغيير إلى الإنجليزية" });
    expect(link).toBeDefined();
    expect(link.getAttribute("href")).toBe("/en/courts/123");
  });
});
