import { fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { MyJoinRequests } from "./my-join-requests";
import type { MatchJoinRequest } from "@/lib/types";

const requests=["pending","approved","rejected","withdrawn","expired"].map((status,index)=>({id:index+1,match_id:10+index,user_id:4,status,requested_position_code:index===0?"goalkeeper":null,reviewed_at:index?"2030-01-02T00:00:00Z":null,created_at:"2030-01-01T00:00:00Z",updated_at:"2030-01-01T00:00:00Z"})) as MatchJoinRequest[];
describe("CM2 MyJoinRequests",()=>{
  beforeEach(()=>{vi.restoreAllMocks();vi.unstubAllGlobals()});
  it("localizes all statuses, real links, and pending-only withdraw",()=>{
    render(<MyJoinRequests locale="en" initialRequests={requests} titles={{10:"Real Match"}}/>);
    for(const label of ["Pending approval","Approved","Rejected","Withdrawn","Expired"])expect(screen.getByText(label)).toBeInTheDocument();
    expect(screen.getAllByRole("link",{name:"View match"})[0]).toHaveAttribute("href","/en/matches/10");
    expect(screen.getAllByRole("button",{name:"Withdraw request"})).toHaveLength(1);
    expect(screen.getByText("Goalkeeper")).toBeInTheDocument();
  });
  it("confirms withdrawal and changes state only after server success",async()=>{
    let resolve!:(value:unknown)=>void;vi.stubGlobal("fetch",vi.fn(()=>new Promise(done=>{resolve=done})));
    render(<MyJoinRequests locale="en" initialRequests={[requests[0]]} titles={{10:"Real Match"}}/>);
    fireEvent.click(screen.getByRole("button",{name:"Withdraw request"}));fireEvent.click(within(screen.getByRole("dialog")).getByRole("button",{name:"Confirm"}));
    expect(screen.getByText("Pending approval")).toBeInTheDocument();resolve({ok:true,json:async()=>({...requests[0],status:"withdrawn"})});
    await screen.findByText("Withdrawn");expect(screen.queryByRole("button",{name:"Withdraw request"})).toBeNull();
  });
  it("keeps pending action after safe failure",async()=>{
    vi.stubGlobal("fetch",vi.fn().mockResolvedValue({ok:false,json:async()=>({detail:"private"})}));render(<MyJoinRequests locale="en" initialRequests={[requests[0]]} titles={{}}/>);
    fireEvent.click(screen.getByRole("button",{name:"Withdraw request"}));fireEvent.click(within(screen.getByRole("dialog")).getByRole("button",{name:"Confirm"}));
    await waitFor(()=>expect(screen.getByRole("alert")).toHaveTextContent("Could not complete this action"));expect(screen.queryByText("private")).toBeNull();expect(screen.getByText("Pending approval")).toBeInTheDocument();
  });
  it("renders localized empty state",()=>{render(<MyJoinRequests locale="ar" initialRequests={[]} titles={{}}/>);expect(screen.getByText("لا توجد طلبات انضمام بعد.")).toBeInTheDocument()});
});
