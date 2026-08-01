import { beforeEach, describe, expect, it, vi } from "vitest";
import Login from "./login/page";
import Register from "./register/page";
import Profile from "./profile/page";

const state = vi.hoisted(() => ({ token: undefined as string | undefined, redirect: vi.fn(), me: vi.fn() }));
vi.mock("next/headers", () => ({ cookies: async () => ({ get: () => state.token ? { value: state.token } : undefined }) }));
vi.mock("next/navigation", () => ({ redirect: (path: string) => { state.redirect(path); throw new Error(`REDIRECT:${path}`); } }));
vi.mock("@/lib/api", () => ({ api: { me: (...args: unknown[]) => state.me(...args) } }));

describe("authenticated route guards", () => {
  beforeEach(() => { state.token = undefined; state.redirect.mockReset(); state.me.mockReset(); });
  it("redirects authenticated login to safe local return path", async () => { state.token = "session"; await expect(Login({ params: Promise.resolve({ locale: "en" }), searchParams: Promise.resolve({ returnTo: "/en/bookings/4" }) })).rejects.toThrow("REDIRECT:/en/bookings/4"); });
  it("rejects unsafe authenticated login return path", async () => { state.token = "session"; await expect(Login({ params: Promise.resolve({ locale: "en" }), searchParams: Promise.resolve({ returnTo: "https://evil.test" }) })).rejects.toThrow("REDIRECT:/en/profile"); });
  it("redirects authenticated registration to localized profile", async () => { state.token = "session"; await expect(Register({ params: Promise.resolve({ locale: "ar" }) })).rejects.toThrow("REDIRECT:/ar/profile"); });
  it("redirects anonymous profile with localized safe return path", async () => { await expect(Profile({ params: Promise.resolve({ locale: "en" }) })).rejects.toThrow("REDIRECT:/en/login?returnTo=%2Fen%2Fprofile"); expect(state.me).not.toHaveBeenCalled(); });
});
