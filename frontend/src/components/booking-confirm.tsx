"use client";
import Link from "next/link";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { MobileActionBar } from "@/components/ui/mobile-action-bar";
import { Surface } from "@/components/ui/surface";
import { bookingUx, formatDateTime } from "@/lib/booking-ux";
import { copy, type Locale } from "@/lib/copy";
import type { Booking } from "@/lib/types";

export function BookingConfirm({ locale, booking }: { locale: Locale; booking: Booking }) {
  const router=useRouter(), text=copy[locale], ux=bookingUx[locale], lock=useRef(false); const [busy,setBusy]=useState(false),[failed,setFailed]=useState(false),[now]=useState(()=>Date.now());
  const expired=booking.status==="expired" || (!!booking.hold_expires_at && Date.parse(booking.hold_expires_at)<=now);
  async function cancel(){ if(lock.current)return; lock.current=true;setBusy(true);setFailed(false);try{const response=await fetch(`/api/bookings/${booking.id}/cancel-hold`,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});if(!response.ok)throw new Error("cancel");router.push(`/${locale}/bookings/${booking.id}`);router.refresh();}catch{setFailed(true);}finally{lock.current=false;setBusy(false);}}
  return <Surface as="section" className="mt-6 space-y-4 pb-20 md:pb-6" padding="md" aria-labelledby="next-step"><h2 id="next-step" className="text-xl font-black">{ux.lifecycle}</h2><Alert tone={expired?"danger":"warning"} message={expired?ux.holdExpired:booking.status==="pending_payment"?ux.holdCreated:ux.awaiting}/>{booking.hold_expires_at&&<p className="text-sm text-[var(--text-secondary)]">{text.bookingHoldExpires}: <time dateTime={booking.hold_expires_at}>{formatDateTime(locale,booking.hold_expires_at)}</time></p>}{failed&&<Alert tone="danger" message={ux.cancelError}/>}<p className="text-sm text-[var(--text-muted)]">{ux.awaiting}</p><MobileActionBar><Link className="focus-ring flex min-h-11 flex-1 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border-strong)] px-4 font-bold" href={`/${locale}/bookings`}>{ux.backBookings}</Link>{booking.status==="pending_payment"&&!expired&&<Button className="flex-1" variant="danger" isLoading={busy} onClick={cancel}>{busy?ux.cancelling:ux.cancelHold}</Button>}</MobileActionBar></Surface>;
}
