"use client";
import { useRef,useState } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { MobileActionBar } from "@/components/ui/mobile-action-bar";
import { canCancel } from "@/lib/booking";
import { bookingUx } from "@/lib/booking-ux";
import type { Locale } from "@/lib/copy";
import type { Booking } from "@/lib/types";
export function BookingActions({booking,locale}:{booking:Booking;locale:Locale}){const ux=bookingUx[locale],router=useRouter(),lock=useRef(false);const[busy,setBusy]=useState(false),[error,setError]=useState(false);if(!canCancel(booking.status))return null;async function cancel(){if(lock.current||!confirm(ux.cancelBooking))return;lock.current=true;setBusy(true);setError(false);try{const path=booking.status==="pending_payment"?"cancel-hold":"cancel";const response=await fetch(`/api/bookings/${booking.id}/${path}`,{method:"POST",headers:{"Content-Type":"application/json"},body:"{}"});if(!response.ok)throw new Error("cancel");router.refresh();}catch{setError(true);}finally{lock.current=false;setBusy(false);}}return <div className="mt-6 pb-16 md:pb-0">{error&&<Alert tone="danger" message={ux.cancelError}/>}<MobileActionBar><Button type="button" variant="danger" fullWidth isLoading={busy} onClick={cancel}>{busy?ux.cancelling:ux.cancelBooking}</Button></MobileActionBar></div>}
