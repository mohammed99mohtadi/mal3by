import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { DashboardShell } from "./dashboard-shell";
import { ComingSoonState, FeatureStatusBanner, PaymentStatusCard } from "./product-foundation";
import { LegalPageLayout } from "./legal-page-layout";
import { UserMenu } from "./user-menu";
import { findProductRoute, productRoutes, routeCounts } from "@/lib/product-routes";
vi.mock("next/navigation",()=>({usePathname:()=>"/en/owner"}));
describe("FM1 product foundation",()=>{
  it("classifies every registered route",()=>{expect(productRoutes.length).toBeGreaterThanOrEqual(40);expect(routeCounts.LIVE).toBeGreaterThan(0);expect(routeCounts.PARTIAL).toBeGreaterThan(0);expect(routeCounts.SHELL).toBeGreaterThan(0);expect(productRoutes.every(r=>Boolean(r.classification&&r.next))).toBe(true)});
  it("resolves static before dynamic route semantics",()=>{expect(findProductRoute("/matches/new")?.classification).toBe("PARTIAL");expect(findProductRoute("/teams/42")?.classification).toBe("SHELL")});
  it("renders localized classification without color-only meaning",()=>{render(<FeatureStatusBanner classification="SHELL" locale="ar"/>);expect(screen.getByRole("status")).toHaveTextContent("SHELL");expect(screen.getByText(/قريبًا/)).toBeInTheDocument()});
  it("coming soon state warns against simulated activity",()=>{render(<ComingSoonState route={findProductRoute("/teams")!} locale="en"/>);expect(screen.getByRole("heading",{name:"Teams"})).toBeInTheDocument();expect(screen.getByText(/does not display simulated data or actions/i)).toBeInTheDocument()});
  it("payment shell never claims payment success",()=>{render(<PaymentStatusCard locale="en"/>);expect(screen.getByText("No metrics available")).toBeInTheDocument();expect(screen.queryByText(/payment successful|paid/i)).toBeNull()});
  it("legal layout carries explicit review notice",()=>{render(<LegalPageLayout locale="en" title="Privacy"/>);expect(screen.getByRole("alert")).toHaveTextContent("not a final legal document")});
  it("dashboard provides responsive navigation landmarks",()=>{render(<DashboardShell locale="en" kind="owner" current="/en/owner"><h1>Owner</h1></DashboardShell>);expect(screen.getAllByRole("navigation",{name:"Dashboard navigation"}).length).toBeGreaterThan(0);expect(screen.getAllByRole("link",{name:"Overview"})[0]).toHaveAttribute("aria-current","page")});
  it("role links use true supplied authorization",()=>{const{rerender}=render(<UserMenu locale="en" name="A"/>);fireEvent.click(screen.getByLabelText("Open account menu"));expect(screen.queryByRole("menuitem",{name:"Admin dashboard"})).toBeNull();rerender(<UserMenu locale="en" name="A" role="admin"/>);expect(screen.getByRole("menuitem",{name:"Admin dashboard"})).toBeInTheDocument()});
});
