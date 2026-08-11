import { render,screen } from "@testing-library/react";
import { beforeEach,describe,expect,it,vi } from "vitest";
import { api } from "@/lib/api";
import CourtDetail from "./page";

vi.mock("next/navigation",()=>({useRouter:()=>({push:vi.fn()})}));
vi.mock("next/image",()=>({default:(props:Record<string,unknown>)=><span data-src={String(props.src)}/> }));
vi.mock("@/lib/api",async(importOriginal)=>{const original=await importOriginal<typeof import("@/lib/api")>();return {...original,api:{...original.api,court:vi.fn(),summary:vi.fn()}}});
const court={id:9,sport_id:1,name_en:"Verified Court",name_ar:"ملعب موثوق",description_en:null,description_ar:null,area:"Salmiya",address:"Block 5",latitude:null,longitude:null,price_per_hour:"12.000",currency:"KWD",capacity:10,image_url:null,is_active:true,sport:{name_en:"Football",name_ar:"كرة القدم",slug:"football"}};

describe("Batch 02 court details",()=>{
  beforeEach(()=>{vi.mocked(api.court).mockResolvedValue(court);vi.mocked(api.summary).mockResolvedValue({average_rating:"4.5",total_reviews:8,verified_reviews:7,rating_distribution:{one:0,two:0,three:1,four:2,five:5}})});
  it("shows only real detail and rating data with booking selection",async()=>{render(await CourtDetail({params:Promise.resolve({locale:"en",courtId:"9"})}));expect(screen.getByRole("heading",{level:1,name:"Verified Court"})).toBeInTheDocument();expect(screen.getByText(/4.5/)).toBeInTheDocument();expect(screen.getByRole("heading",{level:2,name:"Choose a time"})).toBeInTheDocument();expect(screen.queryByText(/facilities|opening hours/i)).toBeNull()});
});
