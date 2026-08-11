import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthForm } from "./auth-form";

const push = vi.fn(); const refresh = vi.fn();
vi.mock("next/navigation", () => ({ useRouter: () => ({ push, refresh }) }));

function input(name: string) { return document.querySelector<HTMLInputElement>(`input[name="${name}"]`)!; }
function fillLogin(password = "password1") { fireEvent.change(input("email"), { target: { value: "player@example.com" } }); fireEvent.change(input("password"), { target: { value: password } }); }
function fillRegister() { fireEvent.change(input("full_name"), { target: { value: "Mona Ali" } }); fillLogin(); fireEvent.change(input("password_confirmation"), { target: { value: "password1" } }); }
function response(ok: boolean, status: number, detail?: string) { return { ok, status, json: async () => detail ? { detail } : { ok: true } }; }

describe("AuthForm V2", () => {
  beforeEach(() => { vi.unstubAllGlobals(); push.mockReset(); refresh.mockReset(); });

  it("renders supported login fields with correct autocomplete", () => {
    render(<AuthForm locale="en" mode="login" />);
    expect(screen.getByLabelText("Email")).toHaveAttribute("autocomplete", "email");
    expect(screen.getByLabelText("Password")).toHaveAttribute("autocomplete", "current-password");
    expect(input("phone_number")).toBeNull();
    expect(screen.getByRole("checkbox", { name: "Remember me" })).toBeChecked();
  });

  it("provides an honest forgot-password entry without making a request", () => {
    const fetchMock = vi.fn(); vi.stubGlobal("fetch", fetchMock); render(<AuthForm locale="en" mode="login" />);
    fireEvent.click(screen.getByRole("button", { name: "Forgot password?" }));
    expect(screen.getByRole("status")).toHaveTextContent("Password recovery is not available yet");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renders only supported registration payload fields plus local confirmation", () => {
    render(<AuthForm locale="en" mode="register" />);
    expect(screen.getByLabelText("Full name")).toHaveAttribute("autocomplete", "name");
    expect(screen.getByLabelText("Phone number")).toBeInTheDocument();
    expect(screen.getByLabelText("Confirm password")).toHaveAttribute("autocomplete", "new-password");
  });

  it("shows and hides password accessibly", () => {
    render(<AuthForm locale="en" mode="login" />); const toggle = screen.getByLabelText("Show password");
    fireEvent.click(toggle); expect(input("password")).toHaveAttribute("type", "text"); expect(screen.getByLabelText("Hide password")).toHaveAttribute("aria-pressed", "true");
  });

  it("focuses first invalid field and associates error", () => {
    render(<AuthForm locale="en" mode="login" />); fireEvent.submit(screen.getByRole("button", { name: "Log in" }).closest("form")!);
    expect(screen.getByLabelText("Email")).toHaveFocus(); expect(screen.getByLabelText("Email")).toHaveAttribute("aria-invalid", "true");
  });

  it("rejects registration password mismatch without request", () => {
    const fetchMock = vi.fn(); vi.stubGlobal("fetch", fetchMock); render(<AuthForm locale="en" mode="register" />); fillRegister(); fireEvent.change(input("password_confirmation"), { target: { value: "different1" } });
    fireEvent.submit(input("password").closest("form")!); expect(fetchMock).not.toHaveBeenCalled(); expect(screen.getByText("Passwords do not match.")).toBeInTheDocument(); expect(input("password_confirmation")).toHaveFocus();
  });

  it("blocks duplicate submission and announces loading", () => {
    const fetchMock = vi.fn(() => new Promise(() => {})); vi.stubGlobal("fetch", fetchMock); render(<AuthForm locale="en" mode="login" />); fillLogin(); const form = input("password").closest("form")!;
    fireEvent.submit(form); fireEvent.submit(form); expect(fetchMock).toHaveBeenCalledTimes(1); expect(screen.getByRole("button", { name: "Please wait..." })).toBeDisabled();
  });

  it("maps invalid credentials without raw backend text", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(false, 401, "internal auth detail"))); render(<AuthForm locale="en" mode="login" />); fillLogin(); fireEvent.submit(input("password").closest("form")!);
    expect(await screen.findByRole("alert")).toHaveTextContent("Email or password is incorrect."); expect(screen.queryByText("internal auth detail")).toBeNull();
  });

  it("maps network failure safely", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("SQL password dump"))); render(<AuthForm locale="en" mode="login" />); fillLogin(); fireEvent.submit(input("password").closest("form")!);
    expect(await screen.findByRole("alert")).toHaveTextContent("Could not reach the service"); expect(screen.queryByText(/SQL password dump/)).toBeNull();
  });

  it("maps duplicate account without enumeration detail", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(false, 400, "A user with this email address already exists."))); render(<AuthForm locale="en" mode="register" />); fillRegister(); fireEvent.submit(input("password").closest("form")!);
    expect(await screen.findByRole("alert")).toHaveTextContent("could not create an account"); expect(screen.queryByText(/already exists/i)).toBeNull();
  });

  it("never sends password confirmation", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response(true, 201)); vi.stubGlobal("fetch", fetchMock); render(<AuthForm locale="en" mode="register" />); fillRegister(); fireEvent.submit(input("password").closest("form")!);
    await waitFor(() => expect(fetchMock).toHaveBeenCalled()); const body = JSON.parse(fetchMock.mock.calls[0][1].body); expect(body.password_confirmation).toBeUndefined(); expect(Object.keys(body).sort()).toEqual(["email", "full_name", "password"]);
  });

  it("uses safe return path after login", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(true, 200))); render(<AuthForm locale="en" mode="login" returnTo="/en/bookings/4" />); fillLogin(); fireEvent.submit(input("password").closest("form")!);
    await waitFor(() => expect(push).toHaveBeenCalledWith("/en/bookings/4"));
  });

  it("sends the optional remember preference without changing credentials", async () => {
    const fetchMock = vi.fn().mockResolvedValue(response(true, 200)); vi.stubGlobal("fetch", fetchMock); render(<AuthForm locale="en" mode="login" />); fillLogin();
    fireEvent.click(screen.getByRole("checkbox", { name: "Remember me" })); fireEvent.submit(input("password").closest("form")!);
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ email: "player@example.com", password: "password1", remember_me: false });
  });

  it("rejects unsafe return path after login", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response(true, 200))); render(<AuthForm locale="en" mode="login" returnTo="https://evil.test" />); fillLogin(); fireEvent.submit(input("password").closest("form")!);
    await waitFor(() => expect(push).toHaveBeenCalledWith("/en/profile"));
  });

  it("renders natural Arabic form copy", () => {
    render(<AuthForm locale="ar" mode="login" />); expect(screen.getByLabelText("البريد الإلكتروني")).toBeInTheDocument(); expect(screen.getByRole("button", { name: "تسجيل الدخول" })).toBeInTheDocument();
  });
});
