import { describe, expect, it, vi } from "vitest";
import { render, screen } from "@testing-library/react";

// ---- Form Primitive Tests ----
import { Select } from "./select";
import { Textarea } from "./textarea";
import { Checkbox } from "./checkbox";
import { Radio } from "./radio";
import { FieldLabel } from "./field-label";
import { FieldError } from "./field-error";
import { FormHint } from "./form-hint";

// ---- Feedback Primitive Tests ----
import { Alert } from "./alert";
import { EmptyState } from "./empty-state";
import { Spinner } from "./spinner";
import { ProgressBar } from "./progress-bar";

// ---- Homepage Component Tests ----
vi.mock("next/navigation", () => ({ usePathname: () => "/ar" }));

import { HeroSection } from "@/components/home/hero-section";
import { FeaturedCourtsSection } from "@/components/home/featured-courts-section";
import { HowItWorksSection } from "@/components/home/how-it-works-section";
import { FinalCtaSection } from "@/components/home/final-cta-section";
import type { Court } from "@/lib/types";

const mockCourt: Court = {
  id: 1,
  sport_id: 1,
  name_en: "Green Court",
  name_ar: "الملعب الأخضر",
  area: "Salmiya",
  address: "Block 1",
  price_per_hour: "12.500",
  currency: "KWD",
  capacity: 10,
  is_active: true,
  sport: { name_en: "Football", name_ar: "كرة القدم", slug: "football" },
};

describe("Form Primitives", () => {
  it("Select forwards standard props and renders options", () => {
    render(
      <Select name="sport" aria-label="Sport">
        <option value="football">Football</option>
      </Select>
    );
    const el = screen.getByRole("combobox", { name: "Sport" });
    expect(el).toBeDefined();
    expect((el as HTMLSelectElement).name).toBe("sport");
  });

  it("Textarea forwards standard props", () => {
    render(<Textarea placeholder="Write something" name="note" />);
    const el = screen.getByPlaceholderText("Write something");
    expect((el as HTMLTextAreaElement).name).toBe("note");
  });

  it("Checkbox renders label and is accessible", () => {
    render(<Checkbox label="Accept terms" />);
    expect(screen.getByText("Accept terms")).toBeDefined();
    const checkbox = screen.getByRole("checkbox");
    expect(checkbox).toBeDefined();
  });

  it("Radio renders label and is accessible", () => {
    render(<Radio name="choice" label="Option A" value="a" />);
    expect(screen.getByText("Option A")).toBeDefined();
    const radio = screen.getByRole("radio");
    expect(radio).toBeDefined();
  });

  it("FieldLabel renders required indicator when required=true", () => {
    render(<FieldLabel required htmlFor="email">Email</FieldLabel>);
    expect(screen.getByText("Email")).toBeDefined();
    expect(screen.getByText("*")).toBeDefined();
  });

  it("FieldError has role='alert' and shows message", () => {
    render(<FieldError message="This field is required" />);
    const el = screen.getByRole("alert");
    expect(el.textContent).toBe("This field is required");
  });

  it("FormHint renders helper text", () => {
    render(<FormHint>Max 100 characters</FormHint>);
    expect(screen.getByText("Max 100 characters")).toBeDefined();
  });
});

describe("Feedback Primitives", () => {
  it("Alert info renders with correct role and message", () => {
    render(<Alert tone="info" message="Informational alert" />);
    expect(screen.getByText("Informational alert")).toBeDefined();
  });

  it("Alert danger has role='alert'", () => {
    render(<Alert tone="danger" message="Something went wrong" />);
    expect(screen.getByRole("alert")).toBeDefined();
  });

  it("EmptyState renders title and description", () => {
    render(<EmptyState title="No results" description="Try again later" />);
    expect(screen.getByText("No results")).toBeDefined();
    expect(screen.getByText("Try again later")).toBeDefined();
  });

  it("Spinner standalone has role=status on wrapper and aria-hidden=true on SVG", () => {
    const { container } = render(<Spinner size="md" />);
    const wrapper = container.querySelector('[role="status"]');
    expect(wrapper).toBeDefined();
    const svg = container.querySelector("svg");
    expect(svg?.getAttribute("aria-hidden")).toBe("true");
  });

  it("Spinner with label has role=status and SVG is aria-hidden", () => {
    const { container } = render(<Spinner size="md" label="Loading courts..." />);
    const wrapper = container.querySelector('[role="status"]');
    expect(wrapper).toBeDefined();
    expect(container.querySelector("svg")?.getAttribute("aria-hidden")).toBe("true");
    expect(screen.getByText("Loading courts...")).toBeDefined();
  });

  it("ProgressBar renders with correct value semantics", () => {
    render(<ProgressBar value={65} label="Upload progress" showValue />);
    const progress = document.querySelector("progress") as HTMLProgressElement;
    expect(progress.value).toBe(65);
    expect(progress.max).toBe(100);
    expect(screen.getByText("65%")).toBeDefined();
  });

  it("ProgressBar clamps negative value to 0", () => {
    render(<ProgressBar value={-20} showValue />);
    const progress = document.querySelector("progress") as HTMLProgressElement;
    expect(progress.value).toBe(0);
    expect(screen.getByText("0%")).toBeDefined();
  });

  it("ProgressBar clamps value above 100 to 100", () => {
    render(<ProgressBar value={150} showValue />);
    const progress = document.querySelector("progress") as HTMLProgressElement;
    expect(progress.value).toBe(100);
    expect(screen.getByText("100%")).toBeDefined();
  });
});

describe("Homepage Sections (Arabic)", () => {
  it("renders Arabic hero headline", () => {
    render(<HeroSection locale="ar" isLoggedIn={false} />);
    expect(screen.getByRole("heading", { level: 1, name: "اكتشف ملعبك. اختر وقتك. والعب." })).toBeDefined();
  });

  it("renders English hero headline", () => {
    render(<HeroSection locale="en" isLoggedIn={false} />);
    expect(screen.getByRole("heading", { level: 1 })).toBeDefined();
    expect(screen.getByText("Find your court. Choose your time. Play.")).toBeDefined();
  });

  it("primary CTA links to courts route", () => {
    render(<HeroSection locale="ar" isLoggedIn={false} />);
    const ctaLink = document.querySelector('a[href="/ar/courts"]') as HTMLAnchorElement;
    expect(ctaLink.getAttribute("href")).toBe("/ar/courts");
  });

  it("authenticated hero links to matches", () => {
    render(<HeroSection locale="en" isLoggedIn={true} />);
    const link = screen.getByRole("link", { name: "Explore matches" });
    expect(link.getAttribute("href")).toBe("/en/matches");
  });

  it("unauthenticated hero shows Log in secondary CTA", () => {
    render(<HeroSection locale="en" isLoggedIn={false} />);
    const link = screen.getByRole("link", { name: "Log in" });
    expect(link.getAttribute("href")).toBe("/en/login");
  });

  it("featured courts renders real court card", () => {
    render(<FeaturedCourtsSection locale="ar" courts={[mockCourt]} />);
    expect(screen.getByText("الملعب الأخضر")).toBeDefined();
  });

  it("featured courts renders empty state when no courts", () => {
    render(<FeaturedCourtsSection locale="ar" courts={[]} />);
    expect(screen.getByText("لا توجد ملاعب مميزة حاليًا")).toBeDefined();
  });

  it("featured courts links to real court route", () => {
    render(<FeaturedCourtsSection locale="ar" courts={[mockCourt]} />);
    const link = screen.getByRole("link", { name: /الملعب الأخضر/ });
    expect(link.getAttribute("href")).toBe("/ar/courts/1");
  });

  it("HowItWorksSection renders 3 steps", () => {
    render(<HowItWorksSection locale="en" />);
    expect(screen.getByText("Find a Court")).toBeDefined();
    expect(screen.getByText("Pick a Slot")).toBeDefined();
    expect(screen.getByText("Confirm Booking")).toBeDefined();
  });

  it("FinalCTA button links to real courts route", () => {
    render(<FinalCtaSection locale="ar" />);
    const link = screen.getByRole("link", { name: /الملاعب/ });
    expect(link.getAttribute("href")).toBe("/ar/courts");
  });
});
