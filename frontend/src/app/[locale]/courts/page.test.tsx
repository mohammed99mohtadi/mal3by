import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import type { Court } from "@/lib/types";
import { courtDiscoveryCopy } from "@/lib/court-discovery";
import Loading from "./loading";
import Courts from "./page";
vi.mock("next/navigation",()=>({useRouter:()=>({refresh:vi.fn()})}));
vi.mock("next/image",()=>({default:(props:Record<string,unknown>)=><span data-src={String(props.src)}/> }));
vi.mock("@/lib/api",async(importOriginal)=>{const original=await importOriginal<typeof import("@/lib/api")>();return{...original,api:{...original.api,courts:vi.fn()}}});
const court={id:8,sport_id:1,name_en:"Real Court",name_ar:"ملعب حقيقي",area:"Salmiya",address:"Street",price_per_hour:"15",currency:"KWD",capacity:12,image_url:null,is_active:true,sport:{name_en:"Football",name_ar:"كرة القدم",slug:"football"}}as Court;
const view=async(locale:"en"|"ar",searchParams={})=>render(await Courts({params:Promise.resolve({locale}),searchParams:Promise.resolve(searchParams)}));
describe("C1 courts page",()=>{
  beforeEach(()=>vi.mocked(api.courts).mockReset());
  it.each(["en","ar"]as const)("renders %s title, real response and count",async locale=>{vi.mocked(api.courts).mockResolvedValue([court]);await view(locale);expect(screen.getByRole("heading",{level:1,name:courtDiscoveryCopy[locale].title})).toBeInTheDocument();expect(screen.getByRole("status")).toHaveTextContent(courtDiscoveryCopy[locale].results(1));expect(screen.getByText(locale==="ar"?"ملعب حقيقي":"Real Court")).toBeInTheDocument()});
  it("separates backend empty and filtered empty",async()=>{vi.mocked(api.courts).mockResolvedValue([]);const{unmount}=await view("en");expect(screen.getByText(courtDiscoveryCopy.en.empty)).toBeInTheDocument();unmount();await view("en",{search:"missing"});expect(screen.getByText(courtDiscoveryCopy.en.none)).toBeInTheDocument()});
  it("renders responsive loading without fake courts",()=>{render(<Loading/>);expect(screen.getByRole("status")).toHaveAccessibleName(/Loading courts/);expect(screen.queryByText("Real Court")).toBeNull()});
});
