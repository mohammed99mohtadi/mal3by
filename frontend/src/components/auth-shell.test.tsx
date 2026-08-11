import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { AuthShell } from "./auth-shell";

describe("AuthShell", () => {
  it("renders one English page heading, the official brand asset, and real reciprocal link", () => { render(<AuthShell locale="en" mode="login"><div>Form</div></AuthShell>); expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1); expect(screen.getByRole("heading", { name: "Log in" })).toBeInTheDocument(); expect(screen.getByRole("img", { name: "MAL3ABY" })).toHaveAttribute("src", expect.stringContaining("mal3aby-logo")); expect(screen.getByRole("link", { name: "MAL3ABY" })).toHaveAttribute("href", "/en"); expect(screen.getByRole("link", { name: "Create account" })).toHaveAttribute("href", "/en/register"); });
  it("does not expose language selection on login", () => { render(<AuthShell locale="en" mode="login"><div>Form</div></AuthShell>); expect(screen.queryByRole("link", { name: /arabic|english|العربية/i })).toBeNull(); });
  it("renders complete Arabic registration copy", () => { render(<AuthShell locale="ar" mode="register"><div>النموذج</div></AuthShell>); expect(screen.getByRole("heading", { name: "إنشاء حساب" })).toBeInTheDocument(); expect(screen.getByRole("link", { name: "تسجيل الدخول" })).toHaveAttribute("href", "/ar/login"); });
  it("contains no fake testimonial, count, rating, or security badge", () => { render(<AuthShell locale="en" mode="login"><div>Form</div></AuthShell>); expect(screen.queryByText(/testimonial|users|rating|secure badge/i)).toBeNull(); });
});
