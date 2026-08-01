export function safeReturnPath(value: string | null, locale: "ar" | "en"): string {
  const fallback = `/${locale}/profile`;
  if (!value || /[\\\u0000-\u001f]/.test(value) || /%(2f|5c)/i.test(value)) return fallback;
  try {
    const url = new URL(value, "https://mal3by.local");
    if (url.origin !== "https://mal3by.local" || !url.pathname.startsWith(`/${locale}/`)) return fallback;
    const query = new URLSearchParams();
    if (url.pathname === `/${locale}/bookings/new`) {
      const courtId = url.searchParams.get("courtId"); const start = url.searchParams.get("start"); const end = url.searchParams.get("end");
      if (courtId && /^\d+$/.test(courtId)) query.set("courtId", courtId);
      if (start && !Number.isNaN(Date.parse(start))) query.set("start", start);
      if (end && !Number.isNaN(Date.parse(end))) query.set("end", end);
    }
    return `${url.pathname}${query.size ? `?${query}` : ""}`;
  } catch { return fallback; }
}
