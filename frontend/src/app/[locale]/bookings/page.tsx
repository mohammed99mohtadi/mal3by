import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Alert } from "@/components/ui/alert";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import { bookingLabel, bookingTone } from "@/lib/booking";
import { copy, type Locale } from "@/lib/copy";

export default async function Bookings({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params; const l = (locale === "en" ? "en" : "ar") as Locale; const text = copy[l]; const token = (await cookies()).get("mal3by_session")?.value;
  if (!token) redirect(`/${l}/login?returnTo=/${l}/bookings`);
  let bookings; try { bookings = await api.bookings(token); } catch { return <section className="page-wrap"><h1 className="text-3xl font-black">{text.bookingMyBookings}</h1><Alert tone="danger" message={text.bookingLoadError} className="mt-6" /></section>; }
  return <section className="page-wrap"><p className="eyebrow">{text.bookingMyBookings}</p><h1 className="mt-2 text-3xl font-black">{text.bookingMyBookings}</h1>{bookings.length === 0 ? <Surface className="mt-6"><EmptyState title={text.bookingNoBookingsTitle} description={text.bookingNoBookingsDescription} /></Surface> : <div className="mt-6 grid gap-4 md:grid-cols-2">{bookings.map((booking) => <Link key={booking.id} href={`/${l}/bookings/${booking.id}`} className="focus-ring rounded-[var(--radius-lg)]"><Surface as="article" variant="interactive"><div className="flex items-start justify-between gap-3"><strong>{booking.court?.[l === "ar" ? "name_ar" : "name_en"] ?? `${text.bookingCourt} #${booking.court_id}`}</strong><StatusBadge status={bookingTone(booking.status)} size="sm">{bookingLabel(l, booking.status)}</StatusBadge></div><p className="mt-5 text-sm text-[var(--text-muted)]">{new Date(booking.start_time).toLocaleString(l)}</p><p className="mt-2 text-sm font-semibold">{text.bookingReference} #{booking.id}</p></Surface></Link>)}</div>}</section>;
}
