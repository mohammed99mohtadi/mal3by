import type { Locale } from "@/lib/copy";

export type NavSection = "home" | "courts" | "bookings" | "matches" | "profile" | "auth" | null;

export function stripLocale(pathname: string): string {
  const clean = pathname.split("?")[0].replace(/^\/(ar|en)(?=\/|$)/, "");
  return clean || "/";
}

export function activeSection(pathname: string): NavSection {
  const path = stripLocale(pathname);
  if (path === "/") return "home";
  if (path === "/courts" || path.startsWith("/courts/")) return "courts";
  if (path === "/bookings" || path.startsWith("/bookings/")) return "bookings";
  if (path === "/matches" || path.startsWith("/matches/")) return "matches";
  if (path === "/community" || path.startsWith("/community/")) return "matches";
  if (path === "/profile" || path.startsWith("/profile/")) return "profile";
  if (["/login", "/register"].includes(path)) return "auth";
  return null;
}

const safeQuery = {
  courtId: (value: string) => /^\d+$/.test(value),
  start: (value: string) => !Number.isNaN(Date.parse(value)),
  end: (value: string) => !Number.isNaN(Date.parse(value)),
} as const;

export function localeHref(pathname: string, targetLocale: Locale, searchParams?: Pick<URLSearchParams, "get">): string {
  const path = pathname.replace(/^\/(ar|en)(?=\/|$)/, `/${targetLocale}`);
  const next = new URLSearchParams();
  if (stripLocale(pathname) === "/bookings/new" && searchParams) {
    for (const [key, validate] of Object.entries(safeQuery)) {
      const value = searchParams.get(key);
      if (value && validate(value)) next.set(key, value);
    }
  }
  const query = next.toString();
  return query ? `${path}?${query}` : path;
}
