import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { Alert } from "@/components/ui/alert";
import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import { bookingLabel, bookingTone } from "@/lib/booking";
import { copy, type Locale } from "@/lib/copy";

export default async function Success({ params }: { params: Promise<{ locale: string; bookingId: string }> }) {
  const { locale, bookingId } = await params; const l = (locale === "en" ? "en" : "ar") as Locale; const text = copy[l]; const token = (await cookies()).get("mal3by_session")?.value;
  if (!token) redirect(`/${l}/login`);
  let booking; try { booking = await api.booking(token, bookingId); } catch { return <section className="page-wrap max-w-xl"><h1 className="text-3xl font-black">{text.bookingSuccessTitle}</h1><Alert tone="danger" message={text.bookingNotFound} className="mt-6" /></section>; }
  return <section className="page-wrap max-w-xl"><Surface className="text-center" padding="lg"><StatusBadge status={bookingTone(booking.status)}>{bookingLabel(l, booking.status)}</StatusBadge><h1 className="mt-5 text-3xl font-black">{text.bookingSuccessTitle}</h1><p className="mt-3 text-[var(--text-muted)]">{text.bookingReference} #{booking.id}</p><p className="mt-5 font-bold">{booking.court?.[l === "ar" ? "name_ar" : "name_en"] ?? `${text.bookingCourt} #${booking.court_id}`}</p><p className="mt-2 text-sm">{new Date(booking.start_time).toLocaleString(l)}</p><div className="mt-8 flex flex-wrap justify-center gap-3"><Link className="focus-ring rounded-[var(--radius-md)] bg-[var(--brand)] px-4 py-2.5 font-bold text-[var(--brand-foreground)]" href={`/${l}/bookings/${booking.id}`}>{text.bookingView}</Link><Link className="focus-ring rounded-[var(--radius-md)] border border-[var(--border-strong)] px-4 py-2.5 font-bold" href={`/${l}/bookings`}>{text.bookingMyBookings}</Link><Link className="focus-ring rounded-[var(--radius-md)] border border-[var(--border-strong)] px-4 py-2.5 font-bold" href={`/${l}/courts`}>{text.courts}</Link></div></Surface></section>;
}
