"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Surface } from "@/components/ui/surface";
import { copy, type Locale } from "@/lib/copy";
import type { Booking } from "@/lib/types";

export function BookingConfirm({ locale, booking }: { locale: Locale; booking: Booking }) {
  const router = useRouter(); const text = copy[locale]; const [busy, setBusy] = useState(false); const [failed, setFailed] = useState(false);
  async function confirm() { setBusy(true); setFailed(false); try { const response = await fetch(`/api/bookings/${booking.id}/confirm-payment`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" }); if (!response.ok) throw new Error("confirm"); router.push(`/${locale}/bookings/${booking.id}/success`); } catch { setFailed(true); } finally { setBusy(false); } }
  return <Surface as="section" className="mt-6 space-y-4" padding="md"><Alert tone="warning" message={text.bookingHoldNotice} />{booking.hold_expires_at && <p className="text-sm text-[var(--text-secondary)]">{text.bookingHoldExpires}: {new Date(booking.hold_expires_at).toLocaleString(locale)}</p>}{failed && <Alert tone="danger" message={text.bookingConfirmError} />}<Button type="button" fullWidth isLoading={busy} disabled={booking.status !== "pending_payment"} onClick={confirm}>{busy ? text.bookingConfirming : text.bookingConfirmAction}</Button></Surface>;
}
