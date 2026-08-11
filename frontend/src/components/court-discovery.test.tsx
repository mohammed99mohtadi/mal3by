import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { CourtCard } from "./court-card";
import { CourtDiscoveryFilters } from "./court-discovery-filters";
import { CourtDiscoveryError } from "./court-discovery-error";
import { CourtPagination } from "./court-pagination";
import { parseCourtFilters } from "@/lib/court-discovery";
import type { Court } from "@/lib/types";

const refresh=vi.fn();
vi.mock("next/navigation",()=>({useRouter:()=>({refresh})}));
vi.mock("next/image",()=>({default:(props:Record<string,unknown>)=><span data-testid="court-image" data-src={String(props.src)}/>}));
const court={id:2,sport_id:1,name_en:"Real Court",name_ar:"ملعب حقيقي",area:"Salmiya",address:"Street",price_per_hour:"12.5",currency:"KWD",capacity:10,image_url:null,is_active:false,sport:{name_en:"Football",name_ar:"كرة القدم",slug:"football"}} as Court;

describe("C1 court components",()=>{
  it("renders real fields, inactive state, fallback, and safe link",()=>{render(<CourtCard court={court} locale="en"/>);expect(screen.getByText("Real Court")).toBeInTheDocument();expect(screen.getByText("Unavailable")).toBeInTheDocument();expect(screen.getByLabelText("Court image unavailable")).toBeInTheDocument();expect(screen.getByRole("link",{name:"View court: Real Court"})).toHaveAttribute("href","/en/courts/2");expect(document.body).not.toHaveTextContent(/rating|distance|facilities/i)});
  it("renders supplied image and Arabic fields",()=>{render(<CourtCard court={{...court,image_url:"https://cdn.example/real.jpg"}} locale="ar"/>);expect(screen.getByText("ملعب حقيقي")).toBeInTheDocument();expect(screen.getByTestId("court-image")).toHaveAttribute("data-src","https://cdn.example/real.jpg")});
  it("opens and closes an accessible compact filter drawer and resets filters",()=>{render(<CourtDiscoveryFilters locale="en" filters={parseCourtFilters({search:"Real"})}/>);fireEvent.click(screen.getByRole("button",{name:/Open filters/}));const dialog=screen.getByRole("dialog",{name:"Filters"});expect(dialog).toHaveClass("mobile-filter-sheet");expect(within(dialog).getByLabelText("Search by court name")).toBeInTheDocument();expect(within(dialog).getByRole("button",{name:"Close filters"})).toBeInTheDocument();expect(screen.getAllByRole("link",{name:"Reset filters"})[0]).toHaveAttribute("href","/en/courts");fireEvent.click(within(dialog).getByRole("button",{name:"Close filters"}));expect(screen.queryByRole("dialog",{name:"Filters"})).not.toBeInTheDocument()});
  it("retries safe error without raw details",()=>{render(<CourtDiscoveryError locale="en" kind="invalid"/>);fireEvent.click(screen.getByRole("button",{name:"Retry"}));expect(refresh).toHaveBeenCalled();expect(screen.getByRole("alert")).not.toHaveTextContent(/stack|127\.0\.0\.1|sql/i)});
  it("preserves filters across pagination",()=>{render(<CourtPagination locale="en" filters={parseCourtFilters({search:"Real",page:"2"})} hasNext/>);expect(screen.getByRole("link",{name:"Next"}).getAttribute("href")).toContain("search=Real");expect(screen.getByRole("link",{name:"Previous"})).toBeInTheDocument()});
});
