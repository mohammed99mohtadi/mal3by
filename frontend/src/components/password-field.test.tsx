import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { PasswordField } from "./password-field";

describe("PasswordField", () => {
  it("announces Caps Lock without exposing value", () => { render(<PasswordField locale="en" label="Password" name="password" />); const event = new KeyboardEvent("keydown", { key: "A", bubbles: true }); Object.defineProperty(event, "getModifierState", { value: (key: string) => key === "CapsLock" }); fireEvent(screen.getByLabelText("Password"), event); expect(screen.getByRole("status")).toHaveTextContent("Caps Lock is on."); });
  it("keeps localized accessible toggle", () => { render(<PasswordField locale="ar" label="كلمة المرور" />); expect(screen.getByLabelText("إظهار كلمة المرور")).toBeInTheDocument(); });
});
