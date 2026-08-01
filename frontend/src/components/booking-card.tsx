import Link from "next/link";
import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import { bookingLabel, bookingTone } from "@/lib/booking";
import { formatDateTime } from "@/lib/booking-ux";
import { copy, type Locale } from "@/lib/copy";
import type { Booking } from "@/lib/types";
export function BookingCard({booking,locale}:{booking:Booking;locale:Locale}){const text=copy[locale];return <Link href={`/${locale}/bookings/${booking.id}`} aria-label={`${text.bookingView} ${booking.id}`} className="focus-ring min-w-0 rounded-[var(--radius-lg)]"><Surface as="article" variant="interactive" className="h-full"><div className="flex flex-wrap items-start justify-between gap-3"><h3 className="min-w-0 break-words font-bold">{booking.court?.[locale==="ar"?"name_ar":"name_en"]??`${text.bookingCourt} #${booking.court_id}`}</h3><StatusBadge status={bookingTone(booking.status)} size="sm">{bookingLabel(locale,booking.status)}</StatusBadge></div><p className="mt-4 text-sm text-[var(--text-muted)]"><time dateTime={booking.start_time}>{formatDateTime(locale,booking.start_time)}</time></p><p className="mt-2 text-sm font-semibold">{text.bookingReference} <bdi>#{booking.id}</bdi></p></Surface></Link>}
