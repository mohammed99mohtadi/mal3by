import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { CourtDiscoveryHero } from "./court-discovery-hero";
import { CourtMap } from "./court-map";
import { HomeDashboard } from "./home/home-dashboard";
import type { Court } from "@/lib/types";

const court={id:3,sport_id:1,name_en:"Real Court",name_ar:"ملعب حقيقي",area:"Salmiya",address:"Block 5",latitude:null,longitude:null,price_per_hour:"10.000",currency:"KWD",capacity:10,image_url:null,is_active:true,sport:{name_en:"Football",name_ar:"كرة القدم",slug:"football"}} as Court;

describe("Batch 02 discovery entry", () => {
  it("offers accessible search and map entry points", () => {
    render(<CourtDiscoveryHero locale="en" count={3} />);
    expect(screen.getByRole("search")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /map/i })).toHaveAttribute("href", "/en/courts/map");
  });
  it("provides an accessible list fallback when real coordinates are missing",()=>{render(<CourtMap courts={[court]} locale="en"/>);expect(screen.getByText("No verified locations available")).toBeInTheDocument();expect(screen.getByRole("link",{name:"Browse courts"})).toHaveAttribute("href","/en/courts")});
  it("renders honest home data and empty booking state",()=>{render(<HomeDashboard locale="en" courts={[court]} upcoming={[]}/>);expect(screen.getByRole("heading",{level:1,name:"Welcome to MAL3ABY"})).toBeInTheDocument();expect(screen.getByRole("search")).toBeInTheDocument();expect(screen.getByText("No upcoming bookings")).toBeInTheDocument();expect(screen.getByRole("link",{name:/View court: Real Court/})).toBeInTheDocument()});
});
