import { useState } from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { BidiText } from "./bidi";
import { Button } from "./button";
import { Dialog } from "./dialog";
import { EmptyState } from "./empty-state";
import { ErrorState } from "./error-state";
import { IconButton } from "./icon-button";
import { Input } from "./input";
import { MobileActionBar } from "./mobile-action-bar";
import { SkipLink } from "./skip-link";

describe("F1 design-system foundation", () => {
  it("keeps button content width while loading and disables action", () => {
    render(<Button isLoading>Save booking</Button>);
    const button = screen.getByRole("button", { name: /save booking/i });
    expect(button).toBeDisabled();
    expect(button).toHaveAttribute("aria-busy", "true");
    expect(button.querySelector(".invisible")).toBeTruthy();
  });

  it("requires an accessible IconButton label", () => {
    render(<IconButton label="Close"><span aria-hidden>×</span></IconButton>);
    expect(screen.getByRole("button", { name: "Close" })).toBeInTheDocument();
  });

  it("associates Input label, hint, and error", () => {
    render(<Input label="Email" hint="Work email" error="Invalid email" />);
    const input = screen.getByLabelText("Email");
    expect(input).toHaveAttribute("aria-invalid", "true");
    expect(input.getAttribute("aria-describedby")).toContain("-error");
    expect(screen.getByRole("alert")).toHaveTextContent("Invalid email");
  });

  it("closes Dialog with Escape and returns focus", () => {
    function Harness() { const [open, setOpen] = useState(false); return <><button onClick={() => setOpen(true)}>Open</button><Dialog open={open} onClose={() => setOpen(false)} title="Confirm"><button>Confirm</button></Dialog></>; }
    render(<Harness />);
    const trigger = screen.getByRole("button", { name: "Open" });
    trigger.focus(); fireEvent.click(trigger);
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    expect(trigger).toHaveFocus();
  });

  it("traps tab focus inside Dialog", () => {
    render(<Dialog open onClose={vi.fn()} title="Actions"><button>First</button><button>Last</button></Dialog>);
    const first = screen.getByRole("button", { name: "First" }); const last = screen.getByRole("button", { name: "Last" });
    last.focus(); fireEvent.keyDown(document, { key: "Tab" }); expect(first).toHaveFocus();
  });

  it("provides localized skip-link target", () => {
    render(<><SkipLink locale="ar" /><main id="main-content" /></>);
    expect(screen.getByRole("link", { name: "انتقل إلى المحتوى" })).toHaveAttribute("href", "#main-content");
    expect(document.querySelector("#main-content")).toBeTruthy();
  });

  it("isolates machine-readable bidi values", () => {
    const { container } = render(<BidiText kind="email" value="player@example.com" />);
    expect(container.querySelector("bdi")).toHaveAttribute("dir", "ltr");
    expect(container.querySelector("bdi")).toHaveClass("bidi-isolate", "bidi-value");
  });

  it("lets mixed names choose direction", () => {
    const { container } = render(<BidiText value="ملعب Arena" />);
    expect(container.querySelector("bdi")).toHaveAttribute("dir", "auto");
  });

  it("gives EmptyState a named semantic region", () => {
    render(<EmptyState title="No bookings" description="Book a court first." />);
    expect(screen.getByRole("region", { name: "No bookings" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 2 })).toHaveTextContent("No bookings");
  });

  it("uses safe localized ErrorState semantics", () => {
    render(<ErrorState locale="ar" kind="offline" />);
    expect(screen.getByRole("alert")).toHaveTextContent("لا يوجد اتصال");
  });

  it("renders MobileActionBar actions", () => {
    render(<MobileActionBar><Button>Continue</Button></MobileActionBar>);
    expect(screen.getByRole("button", { name: "Continue" })).toBeInTheDocument();
  });
});
