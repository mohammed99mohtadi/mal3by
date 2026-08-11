import Link from "next/link";
import { CourtCard } from "@/components/court-card";
import { CourtDiscoveryError } from "@/components/court-discovery-error";
import { CourtDiscoveryFilters } from "@/components/court-discovery-filters";
import { CourtDiscoveryHero } from "@/components/court-discovery-hero";
import { CourtPagination } from "@/components/court-pagination";
import { EmptyState } from "@/components/ui/empty-state";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import { COURT_PAGE_SIZE,courtBackendQuery,courtDiscoveryCopy,courtPublicQuery,parseCourtFilters } from "@/lib/court-discovery";
import type { Locale } from "@/lib/copy";
import { ApiError } from "@/lib/types";

export default async function Courts({params,searchParams}:{params:Promise<{locale:string}>;searchParams:Promise<Record<string,string|string[]|undefined>>}) {
  const {locale}=await params,l=(locale==="en"?"en":"ar")as Locale,t=courtDiscoveryCopy[l],filters=parseCourtFilters(await searchParams);
  let loaded;try{loaded=await api.courts(courtBackendQuery(filters))}catch(error){const kind=error instanceof ApiError&&error.status===502?"invalid":error instanceof ApiError&&error.status===401?"unauthorized":error instanceof ApiError&&error.status>=500?"service":"network";return <section className="page-wrap py-8 sm:py-12"><CourtDiscoveryError locale={l} kind={kind}/></section>}
  const hasNext=loaded.length>COURT_PAGE_SIZE,courts=loaded.slice(0,COURT_PAGE_SIZE),hasFilters=Boolean(filters.search||filters.area||filters.min||filters.max||filters.active||filters.sportId);
  const sports=[...new Map(courts.flatMap(c=>c.sport?[[c.sport_id,c.sport]]:[])).entries()];
  return <section className="discovery-page page-wrap pb-28 pt-5 sm:pt-8">
    <CourtDiscoveryHero locale={l} count={courts.length} query={filters.search}/>
    <nav className="sport-chip-row" aria-label={l==="ar"?"تصفية حسب الرياضة":"Filter by sport"}>
      <Link className={!filters.sportId?"is-active":""} href={`/${l}/courts`}>{l==="ar"?"الكل":"All"}</Link>
      {sports.map(([id,sport])=><Link key={id} className={filters.sportId===String(id)?"is-active":""} href={`/${l}/courts?${courtPublicQuery({...filters,sportId:String(id),page:1})}`}>{sport[l==="ar"?"name_ar":"name_en"]}</Link>)}
    </nav>
    <div className="mt-5 grid min-w-0 gap-5 lg:grid-cols-[17rem_minmax(0,1fr)]"><CourtDiscoveryFilters locale={l} filters={filters}/><main className="min-w-0 lg:col-start-2">{courts.length?<div className="discovery-results">{courts.map(court=><CourtCard key={court.id} court={court} locale={l}/>)}</div>:<Surface className="border-dashed py-8"><EmptyState title={hasFilters?t.none:t.empty} description={hasFilters?t.noneText:t.emptyText}/>{hasFilters&&<div className="flex justify-center pb-2"><Link className="button-link" href={`/${l}/courts`}>{t.reset}</Link></div>}</Surface>}<CourtPagination locale={l} filters={filters} hasNext={hasNext}/></main></div>
  </section>;
}
