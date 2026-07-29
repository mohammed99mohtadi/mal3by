import { describe, expect, it } from "vitest";
import { safeReturnPath } from "./redirect";
describe("safeReturnPath",()=>{it("allows locale-local paths",()=>{expect(safeReturnPath("/ar/courts/123","ar")).toBe("/ar/courts/123")});it("rejects external and invalid paths",()=>{for(const value of ["https://evil.example","//evil.example","javascript:alert(1)","data:text/html,test","/en/courts"])expect(safeReturnPath(value,"ar")).toBe("/ar/profile")})});
