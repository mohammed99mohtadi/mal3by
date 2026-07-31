"use client";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { FieldError } from "@/components/ui/field-error";
import { Surface } from "@/components/ui/surface";
import { copy, type Locale } from "@/lib/copy";
type Slot = { start_time: string; end_time: string; available?: boolean };
export function BookingForm({ locale, courtId, start, end }: { locale: Locale; courtId: string; start: string; end: string }) {
  const router = useRouter(); const text = copy[locale]; const [error, setError] = useState(""); const [busy, setBusy] = useState(false); const submitting = useRef(false);
  async function submit(event: React.FormEvent<HTMLFormElement>) { event.preventDefault(); if (submitting.current) return; if (!(new Date(start) < new Date(end))) { setError(text.bookingInvalidSlot); return; } submitting.current = true; setBusy(true); setError(""); try { const availability = await fetch(`/api/courts/${courtId}/slots?date=${encodeURIComponent(start.slice(0, 10))}`); const data = await availability.json().catch(() => ({})); if (!availability.ok || !data.slots?.some((slot: Slot) => slot.start_time === start && slot.end_time === end && slot.available !== false)) { setError(text.bookingSlotUnavailable); return; } const response = await fetch("/api/bookings/hold", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ court_id: Number(courtId), start_time: start, end_time: end }) }); const booking = await response.json().catch(() => null); if (!response.ok || !booking?.id) { setError(text.bookingHoldError); return; } router.push(`/${locale}/bookings/${booking.id}/confirm`); } catch { setError(text.bookingHoldError); } finally { submitting.current = false; setBusy(false); } }
  return <Surface className="p-0"><form onSubmit={submit} className="grid gap-4 p-4 sm:p-6"><dl className="grid gap-3 text-sm"><div><dt className="font-semibold text-[var(--text-secondary)]">{text.start}</dt><dd>{new Date(start).toLocaleString(locale)}</dd></div><div><dt className="font-semibold text-[var(--text-secondary)]">{text.end}</dt><dd>{new Date(end).toLocaleString(locale)}</dd></div></dl>{error && <FieldError message={error} />}<Button type="submit" fullWidth isLoading={busy}>{busy ? text.reserving : text.reserveSlot}</Button></form></Surface>;
}
