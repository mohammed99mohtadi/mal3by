import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { BookingForm } from "@/components/booking-form";
import { Alert } from "@/components/ui/alert";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import { copy, type Locale } from "@/lib/copy";

export default async function NewBooking({ params, searchParams }: { params: Promise<{ locale: string }>; searchParams: Promise<{ courtId?: string; start?: string; end?: string }> }) {
  const { locale } = await params; const l = (locale === "en" ? "en" : "ar") as Locale; const text = copy[l]; const { courtId, start, end } = await searchParams; const query = new URLSearchParams(); if (courtId) query.set("courtId", courtId); if (start) query.set("start", start); if (end) query.set("end", end);
  if (!(await cookies()).get("mal3by_session")) redirect(`/${l}/login?returnTo=${encodeURIComponent(`/${l}/bookings/new?${query}`)}`);
  if (!courtId || !/^\d+$/.test(courtId) || !start || !end || Number.isNaN(Date.parse(start)) || Number.isNaN(Date.parse(end)) || new Date(start) >= new Date(end)) return <section className="page-wrap max-w-xl"><Surface><p className="eyebrow">{text.bookingSteps}</p><h1 className="mt-2 text-2xl font-black">{text.bookingInvalidTitle}</h1><Alert tone="warning" message={text.bookingInvalidDescription} className="mt-5" /><Link className="focus-ring mt-6 inline-block font-bold text-[var(--brand)]" href={`/${l}/courts`}>{text.browseCourts}</Link></Surface></section>;
  let court; try { court = await api.court(courtId); } catch { return <section className="page-wrap max-w-xl"><h1 className="text-3xl font-black">{text.bookingReviewTitle}</h1><Alert tone="danger" message={text.bookingUnavailable} className="mt-6" /></section>; }
  if (!court.is_active) return <section className="page-wrap max-w-xl"><h1 className="text-3xl font-black">{text.bookingReviewTitle}</h1><Alert tone="warning" message={text.courtInactive} className="mt-6" /></section>;
  return <section className="page-wrap max-w-xl"><p className="eyebrow">{text.bookingSteps}</p><Surface className="mt-4"><h1 className="text-3xl font-black">{text.bookingReviewTitle}</h1><p className="mt-3 font-bold">{court[l === "ar" ? "name_ar" : "name_en"]}</p><p className="mt-1 text-sm text-[var(--text-muted)]">{court.sport?.[l === "ar" ? "name_ar" : "name_en"]} · {court.area}</p><p className="mt-5 text-sm text-[var(--text-muted)]">{text.bookingServerPrice}</p><div className="mt-5"><BookingForm locale={l} courtId={courtId} start={start} end={end} /></div></Surface></section>;
}
