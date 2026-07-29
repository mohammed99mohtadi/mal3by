import type { BookingStatus } from "@/lib/types";
export const bookingLabel: Record<BookingStatus, string> = { pending:"Pending", pending_payment:"Reservation hold", confirmed:"Confirmed", cancelled:"Cancelled", expired:"Expired", completed:"Completed", rejected:"Rejected", refunded:"Refunded" };
export const canCancel = (status: BookingStatus) => ["pending", "pending_payment", "confirmed"].includes(status);
