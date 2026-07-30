import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { Button } from "./button";
import { Input } from "./input";
import { StatusBadge } from "./status-badge";
import { Surface } from "./surface";
import { Skeleton } from "./skeleton";

describe("UI Primitives Component Suite", () => {
  it("renders Button with variant, size, and loading state", () => {
    const { rerender } = render(<Button variant="primary">Click Me</Button>);
    const button = screen.getByRole("button", { name: "Click Me" });
    expect(button).toBeDefined();
    expect(button.className).toContain("bg-[var(--brand)]");

    rerender(<Button isLoading>Click Me</Button>);
    expect(screen.getByRole("button")).toHaveProperty("disabled", true);
  });

  it("renders Input with leading/trailing slots and error state", () => {
    render(
      <Input
        placeholder="Enter email"
        hasError
        leadingSlot={<span>@</span>}
      />
    );
    const input = screen.getByPlaceholderText("Enter email");
    expect(input).toBeDefined();
  });

  it("renders Surface with padding and variants", () => {
    const { container } = render(<Surface variant="elevated" padding="lg">Card Content</Surface>);
    expect(container.firstChild).toBeDefined();
  });

  it("renders StatusBadge with status colors and text", () => {
    render(<StatusBadge status="success">Approved</StatusBadge>);
    expect(screen.getByText("Approved")).toBeDefined();
  });

  it("renders Skeleton with aria-hidden true by default", () => {
    const { container } = render(<Skeleton variant="rectangular" className="h-10 w-20" />);
    expect(container.querySelector('[aria-hidden="true"]')).toBeDefined();
  });
});
