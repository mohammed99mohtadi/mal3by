"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { FieldLabel } from "@/components/ui/field-label";
import { Spinner } from "@/components/ui/spinner";
import { copy, type Locale } from "@/lib/copy";

type Slot = { start_time: string; end_time: string; available?: boolean };

export function Availability({ courtId, locale, inactive = false }: { courtId: string; locale: Locale; inactive?: boolean }) {
  const router = useRouter();
  const text = copy[locale];
  const [date, setDate] = useState(new Date().toISOString().slice(0, 10));
  const [slots, setSlots] = useState<Slot[] | null>(null);
  const [selected, setSelected] = useState<Slot | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  async function load() {
    setLoading(true); setError(false); setSelected(null); setSlots(null);
    try {
      const response = await fetch(`/api/courts/${courtId}/slots?date=${encodeURIComponent(date)}`);
      if (!response.ok) throw new Error("slots");
      const data = await response.json() as { slots?: Slot[] };
      setSlots(data.slots ?? []);
    } catch { setError(true); } finally { setLoading(false); }
  }

  function continueBooking() {
    if (!selected || selected.available === false) return;
    router.push(`/${locale}/bookings/new?${new URLSearchParams({ courtId, start: selected.start_time, end: selected.end_time })}`);
  }

  if (inactive) return <Alert tone="warning" message={text.courtInactive} className="mt-5" />;

  return <section className="mt-5" aria-label={text.courtAvailability}>
    <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
      <div className="flex-1"><FieldLabel htmlFor={`availability-date-${courtId}`}>{text.date}</FieldLabel><input id={`availability-date-${courtId}`} className="min-h-[44px] w-full rounded-[var(--radius-md)] border border-[var(--border-strong)] bg-[var(--surface-1)] px-3 focus-ring" type="date" value={date} onChange={(event) => setDate(event.target.value)} /></div>
      <Button type="button" onClick={load} disabled={loading}>{text.checkAvailability}</Button>
    </div>
    {loading && <div className="mt-4"><Spinner label={text.availabilityLoading} /></div>}
    {error && <div className="mt-4 space-y-3"><Alert tone="danger" message={text.availabilityError} /><Button type="button" variant="outline" onClick={load}>{text.retry}</Button></div>}
    {slots === null && !loading && !error && <p role="status" className="mt-4 text-sm text-[var(--text-muted)]">{text.availabilityPrompt}</p>}
    {slots && !loading && <div className="mt-4"><div className="grid grid-cols-2 gap-2" role="group" aria-label={text.courtAvailability}>{slots.length ? slots.map((slot) => { const unavailable = slot.available === false; const active = selected?.start_time === slot.start_time; return <button key={slot.start_time} type="button" disabled={unavailable} aria-pressed={active} onClick={() => setSelected(slot)} className="min-h-[44px] rounded-[var(--radius-md)] border border-[var(--border-strong)] px-3 py-2 text-sm font-semibold focus-ring aria-pressed:border-[var(--brand)] aria-pressed:bg-[var(--brand)]/10 disabled:cursor-not-allowed disabled:opacity-50">{new Date(slot.start_time).toLocaleTimeString(locale, { hour: "2-digit", minute: "2-digit" })}{unavailable ? ` — ${text.courtUnavailable}` : ""}</button>; }) : <p className="col-span-2 text-sm text-[var(--text-muted)]">{text.availabilityEmpty}</p>}</div><Button type="button" fullWidth className="mt-4" disabled={!selected || selected.available === false} onClick={continueBooking}>{text.courtBook}</Button></div>}
  </section>;
}
