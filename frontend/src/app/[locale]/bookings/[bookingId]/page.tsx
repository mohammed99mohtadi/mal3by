import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Alert } from "@/components/ui/alert";
import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import { bookingLabel, bookingTone } from "@/lib/booking";
import { copy, type Locale } from "@/lib/copy";

export default async function BookingDetail({ params }: { params: Promise<{ locale: string; bookingId: string }> }) {
  const { locale, bookingId } = await params; const l = (locale === "en" ? "en" : "ar") as Locale; const text = copy[l]; const token = (await cookies()).get("mal3by_session")?.value;
  if (!token) redirect(`/${l}/login?returnTo=/${l}/bookings/${bookingId}`);
  let booking; try { booking = await api.booking(token, bookingId); } catch { return <section className="page-wrap max-w-3xl"><h1 className="text-3xl font-black">{text.bookingDetailsTitle}</h1><Alert tone="danger" message={text.bookingNotFound} className="mt-6" /></section>; }
  return <section className="page-wrap max-w-3xl"><Link className="focus-ring text-sm font-bold text-[var(--brand)]" href={`/${l}/bookings`}>{text.bookingMyBookings}</Link><Surface className="mt-5"><div className="flex flex-wrap items-center justify-between gap-3"><h1 className="text-3xl font-black">{text.bookingDetailsTitle}</h1><StatusBadge status={bookingTone(booking.status)}>{bookingLabel(l, booking.status)}</StatusBadge></div><dl className="mt-7 grid gap-5 border-t border-[var(--border)] pt-6 sm:grid-cols-2"><div><dt className="text-sm text-[var(--text-muted)]">{text.bookingReference}</dt><dd className="mt-1 font-bold">#{booking.id}</dd></div><div><dt className="text-sm text-[var(--text-muted)]">{text.bookingCourt}</dt><dd className="mt-1 font-bold">{booking.court?.[l === "ar" ? "name_ar" : "name_en"] ?? `${text.bookingCourt} #${booking.court_id}`}</dd></div><div><dt className="text-sm text-[var(--text-muted)]">{text.bookingTime}</dt><dd className="mt-1">{new Date(booking.start_time).toLocaleString(l)} – {new Date(booking.end_time).toLocaleTimeString(l)}</dd></div>{booking.total_price && <div><dt className="text-sm text-[var(--text-muted)]">{text.bookingAmount}</dt><dd className="mt-1 font-bold">{booking.total_price} {booking.currency}</dd></div>}{booking.hold_expires_at && <div><dt className="text-sm text-[var(--text-muted)]">{text.bookingHoldExpires}</dt><dd className="mt-1">{new Date(booking.hold_expires_at).toLocaleString(l)}</dd></div>}</dl></Surface></section>;
}
