import Link from "next/link";
import { CourtCard } from "@/components/court-card";
import { CourtDiscoveryError } from "@/components/court-discovery-error";
import { CourtDiscoveryFilters } from "@/components/court-discovery-filters";
import { CourtDiscoveryHero } from "@/components/court-discovery-hero";
import { CourtPagination } from "@/components/court-pagination";
import { EmptyState } from "@/components/ui/empty-state";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import { COURT_PAGE_SIZE, courtBackendQuery, courtDiscoveryCopy, parseCourtFilters } from "@/lib/court-discovery";
import type { Locale } from "@/lib/copy";
import { ApiError } from "@/lib/types";

export default async function Courts({params,searchParams}:{params:Promise<{locale:string}>;searchParams:Promise<Record<string,string|string[]|undefined>>}){const{locale}=await params,l=(locale==="en"?"en":"ar")as Locale,t=courtDiscoveryCopy[l],filters=parseCourtFilters(await searchParams);let loaded;try{loaded=await api.courts(courtBackendQuery(filters))}catch(error){const kind=error instanceof ApiError&&error.status===502?"invalid":error instanceof ApiError&&error.status===401?"unauthorized":error instanceof ApiError&&error.status>=500?"service":"network";return <section className="page-wrap py-8 sm:py-12"><CourtDiscoveryError locale={l} kind={kind}/></section>}const hasNext=loaded.length>COURT_PAGE_SIZE,courts=loaded.slice(0,COURT_PAGE_SIZE),hasFilters=Boolean(filters.search||filters.area||filters.min||filters.max||filters.active);return <section className="page-wrap pb-28 pt-5 sm:pt-8"><CourtDiscoveryHero locale={l} count={courts.length}/><div className="mt-8 grid min-w-0 gap-6 lg:grid-cols-[18rem_minmax(0,1fr)] lg:gap-8"><CourtDiscoveryFilters locale={l} filters={filters}/><main className="min-w-0 lg:col-start-2">{courts.length?<div className="grid min-w-0 gap-5 xl:grid-cols-2">{courts.map((court,index)=><div key={court.id} className="reveal-in" style={{animationDelay:`${Math.min(index,5)*45}ms`}}><CourtCard court={court} locale={l}/></div>)}</div>:<Surface className="border-dashed py-8 sm:py-12"><EmptyState title={hasFilters?t.none:t.empty} description={hasFilters?t.noneText:t.emptyText}/>{hasFilters&&<div className="flex justify-center pb-2"><Link className="button-link" href={`/${l}/courts`}>{t.reset}</Link></div>}</Surface>}<CourtPagination locale={l} filters={filters} hasNext={hasNext}/></main></div></section>}
