"use client";
import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { FieldError } from "@/components/ui/field-error";
import { Surface } from "@/components/ui/surface";
import { bookingUx, durationMinutes, formatDateTime } from "@/lib/booking-ux";
import { copy, type Locale } from "@/lib/copy";
type Slot={start_time:string;end_time:string;available?:boolean};
export function BookingForm({locale,courtId,start,end}:{locale:Locale;courtId:string;start:string;end:string}){
 const router=useRouter(),text=copy[locale],ux=bookingUx[locale];const[error,setError]=useState(""),[busy,setBusy]=useState(false);const lock=useRef(false),errorRef=useRef<HTMLDivElement>(null);const fail=(message:string)=>{setError(message);queueMicrotask(()=>errorRef.current?.focus());};
 async function submit(event:React.FormEvent<HTMLFormElement>){event.preventDefault();if(lock.current)return;if(!(new Date(start)<new Date(end))){fail(text.bookingInvalidSlot);return;}lock.current=true;setBusy(true);setError("");try{const availability=await fetch(`/api/courts/${courtId}/slots?date=${encodeURIComponent(start.slice(0,10))}`);const data=await availability.json().catch(()=>({}));if(!availability.ok||!data.slots?.some((slot:Slot)=>slot.start_time===start&&slot.end_time===end&&slot.available!==false)){fail(text.bookingSlotUnavailable);return;}const response=await fetch("/api/bookings/hold",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({court_id:Number(courtId),start_time:start,end_time:end})});const booking=await response.json().catch(()=>null);if(!response.ok||!booking?.id){fail(response.status===409?text.bookingSlotUnavailable:text.bookingHoldError);return;}router.push(`/${locale}/bookings/${booking.id}/confirm`);}catch{fail(text.bookingHoldError);}finally{lock.current=false;setBusy(false);}}
 return <Surface className="p-0"><form onSubmit={submit} className="grid gap-4 p-4 sm:p-6"><dl className="grid gap-3 text-sm sm:grid-cols-2"><div><dt className="font-semibold text-[var(--text-secondary)]">{text.start}</dt><dd><time dateTime={start}>{formatDateTime(locale,start)}</time></dd></div><div><dt className="font-semibold text-[var(--text-secondary)]">{text.end}</dt><dd><time dateTime={end}>{formatDateTime(locale,end)}</time></dd></div><div><dt className="font-semibold text-[var(--text-secondary)]">{ux.duration}</dt><dd>{durationMinutes(start,end)} {ux.minutes}</dd></div></dl>{error&&<div ref={errorRef} tabIndex={-1}><FieldError message={error}/></div>}<Button type="submit" fullWidth isLoading={busy}>{busy?text.reserving:text.reserveSlot}</Button></form></Surface>;
}
