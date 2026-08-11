import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { LanguageForm } from "./language-form";
import { AuthShell } from "./auth-shell";

const push = vi.fn(); const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, refresh }) }));

describe("Batch 01 entry screens", () => {
  beforeEach(() => { push.mockReset(); refresh.mockReset(); vi.unstubAllGlobals(); });

  it("renders splash, forgot password, and language screens inside isolated auth entry", () => {
    const { rerender, container } = render(<AuthShell locale="en" mode="splash"><p>Find your court.</p></AuthShell>);
    expect(container.querySelector(".auth-entry")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Log in" })).toHaveAttribute("href", "/en/login");
    rerender(<AuthShell locale="en" mode="forgot"><p>Password recovery is not available yet.</p></AuthShell>);
    expect(screen.getByRole("heading", { name: "Forgot your password?" })).toBeInTheDocument();
    rerender(<AuthShell locale="en" mode="language"><LanguageForm locale="en" /></AuthShell>);
    expect(screen.getByRole("radiogroup", { name: "Choose your language" })).toBeInTheDocument();
  });

  it("selects English and persists it before entering the English product", async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => ({ preferred_language: "en" }) });
    vi.stubGlobal("fetch", fetchMock); render(<LanguageForm locale="ar" />);
    fireEvent.click(screen.getByRole("radio", { name: /English/ }));
    fireEvent.click(screen.getByRole("button", { name: "متابعة" }));
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith("/api/profile/language", expect.objectContaining({ body: JSON.stringify({ preferred_language: "en" }) })));
    expect(push).toHaveBeenCalledWith("/en/profile");
  });

  it("supports keyboard radio selection and announces persistence errors", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("network"))); render(<LanguageForm locale="en" />);
    const arabic = screen.getByRole("radio", { name: /العربية/ });
    arabic.focus(); fireEvent.keyDown(arabic, { key: " " }); fireEvent.click(arabic);
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not save your language");
  });
});
