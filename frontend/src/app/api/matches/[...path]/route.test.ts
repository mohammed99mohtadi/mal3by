import { beforeEach, describe, expect, it, vi } from "vitest";
import { POST } from "./route";
vi.mock("next/headers",()=>({cookies:async()=>({get:()=>({value:"session"})})}));
describe("CM2 match proxy",()=>{
  beforeEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals()});
  it("forwards only position_code for join requests",async()=>{
    const fetch=vi.fn().mockResolvedValue(new Response(JSON.stringify({id:1}),{status:201,headers:{"Content-Type":"application/json"}}));vi.stubGlobal("fetch",fetch);
    const request=new Request("http://local/api/matches/42/join-requests",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({position_code:" goalkeeper ",user_id:999})});
    const result=await POST(request,{params:Promise.resolve({path:["42","join-requests"]})});expect(result.status).toBe(201);
    const [url,options]=fetch.mock.calls[0] as [string,RequestInit];expect(url).toMatch(/\/matches\/42\/join-requests$/);expect(options.body).toBe(JSON.stringify({position_code:"goalkeeper"}));
  });
  it("rejects unsupported operations without backend call",async()=>{const fetch=vi.fn();vi.stubGlobal("fetch",fetch);const result=await POST(new Request("http://local",{method:"POST"}),{params:Promise.resolve({path:["42","delete"]})});expect(result.status).toBe(404);expect(fetch).not.toHaveBeenCalled()});
});
