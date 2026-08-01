import { describe, expect, it } from "vitest";
import { bookingGroup, durationMinutes, formatDateTime, formatMoney, statusExplanation } from "./booking-ux";
import type { Booking, BookingStatus } from "./types";
const booking=(status:BookingStatus,end="2030-01-01T11:00:00Z")=>({id:1,court_id:2,start_time:"2030-01-01T10:00:00Z",end_time:end,total_price:"25",currency:"KWD",status,created_at:"2029-01-01T00:00:00Z"})as Booking;
describe("booking UX helpers",()=>{
  it("formats Kuwait-localized date and money",()=>{expect(formatDateTime("en","2030-01-01T10:00:00Z")).toMatch(/2030/);expect(formatMoney("en","25","KWD")).toMatch(/25/)});
  it("calculates duration",()=>expect(durationMinutes("2030-01-01T10:00:00Z","2030-01-01T11:30:00Z")).toBe(90));
  it.each(["cancelled","expired","rejected","refunded"]as BookingStatus[])("groups %s as closed",status=>expect(bookingGroup(booking(status))).toBe("closed"));
  it("groups future confirmed as upcoming",()=>expect(bookingGroup(booking("confirmed"))).toBe("upcoming"));
  it("groups completed as history",()=>expect(bookingGroup(booking("completed"))).toBe("history"));
  it("localizes every known status without raw enum leakage",()=>{for(const status of["pending","pending_payment","confirmed","cancelled","expired","completed","rejected","refunded"]as BookingStatus[]){expect(statusExplanation("en",status)).not.toContain("pending_payment");expect(statusExplanation("ar",status).length).toBeGreaterThan(3)}});
});
