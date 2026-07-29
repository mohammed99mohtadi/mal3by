import { describe, expect, it } from "vitest";
import { bookingLabel, canCancel } from "./booking";
describe("booking status mapping",()=>{it("does not label a hold as confirmed",()=>expect(bookingLabel.pending_payment).toBe("Reservation hold"));it("allows cancellation only for lifecycle states supported by backend",()=>{expect(canCancel("confirmed")).toBe(true);expect(canCancel("expired")).toBe(false);expect(canCancel("completed")).toBe(false)})});
