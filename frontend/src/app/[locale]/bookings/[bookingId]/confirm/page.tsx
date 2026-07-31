import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { BookingConfirm } from "@/components/booking-confirm";
import { Alert } from "@/components/ui/alert";
import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import { bookingLabel, bookingTone } from "@/lib/booking";
import { copy, type Locale } from "@/lib/copy";

export default async function Confirm({ params }: { params: Promise<{ locale: string; bookingId: string }> }) {
  const { locale, bookingId } = await params; const l = (locale === "en" ? "en" : "ar") as Locale; const text = copy[l]; const token = (await cookies()).get("mal3by_session")?.value;
  if (!token) redirect(`/${l}/login?returnTo=/${l}/bookings/${bookingId}/confirm`);
  let booking; try { booking = await api.booking(token, bookingId); } catch { return <section className="page-wrap max-w-xl"><h1 className="text-3xl font-black">{text.bookingConfirmTitle}</h1><Alert tone="danger" message={text.bookingNotFound} className="mt-6" /></section>; }
  return <section className="page-wrap max-w-xl"><p className="eyebrow">{text.bookingSteps}</p><Surface className="mt-4"><h1 className="text-3xl font-black">{text.bookingConfirmTitle}</h1><p className="mt-3 text-[var(--text-muted)]">{booking.court?.[l === "ar" ? "name_ar" : "name_en"] ?? `${text.bookingCourt} #${booking.court_id}`}</p><p className="mt-2 text-sm">{new Date(booking.start_time).toLocaleString(l)}</p><div className="mt-5"><StatusBadge status={bookingTone(booking.status)}>{bookingLabel(l, booking.status)}</StatusBadge></div>{booking.total_price && <p className="mt-4 font-bold">{text.bookingAmount}: {booking.total_price} {booking.currency}</p>}<BookingConfirm locale={l} booking={booking} /></Surface></section>;
}
