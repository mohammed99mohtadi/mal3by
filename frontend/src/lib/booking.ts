import { copy, type Locale } from "@/lib/copy";
import type { BookingStatus } from "@/lib/types";

const statusCopyKey: Record<BookingStatus, keyof typeof copy.en> = { pending: "bookingPending", pending_payment: "bookingPendingPayment", confirmed: "bookingConfirmed", cancelled: "bookingCancelled", expired: "bookingExpired", completed: "bookingCompleted", rejected: "bookingRejected", refunded: "bookingRefunded" };
export const bookingLabel = (locale: Locale, status: BookingStatus) => copy[locale][statusCopyKey[status]];
export const legacyBookingLabel: Record<BookingStatus, string> = { pending: "Pending", pending_payment: "Reservation hold", confirmed: "Confirmed", cancelled: "Cancelled", expired: "Expired", completed: "Completed", rejected: "Rejected", refunded: "Refunded" };
export const canCancel = (status: BookingStatus) => ["pending", "pending_payment", "confirmed"].includes(status);
export const bookingTone = (status: BookingStatus) => ["confirmed", "completed"].includes(status) ? "success" as const : ["pending", "pending_payment"].includes(status) ? "warning" as const : ["cancelled", "expired", "rejected", "refunded"].includes(status) ? "danger" as const : "neutral" as const;
