import Link from "next/link";
import { CourtCard } from "@/components/court-card";
import { CourtDiscoveryError } from "@/components/court-discovery-error";
import { CourtDiscoveryFilters } from "@/components/court-discovery-filters";
import { CourtPagination } from "@/components/court-pagination";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import { COURT_PAGE_SIZE, courtBackendQuery, courtDiscoveryCopy, parseCourtFilters } from "@/lib/court-discovery";
import type { Locale } from "@/lib/copy";
import { ApiError } from "@/lib/types";

export default async function Courts({params,searchParams}:{params:Promise<{locale:string}>;searchParams:Promise<Record<string,string|string[]|undefined>>}){const{locale}=await params,l=(locale==="en"?"en":"ar")as Locale,t=courtDiscoveryCopy[l],filters=parseCourtFilters(await searchParams);let loaded;try{loaded=await api.courts(courtBackendQuery(filters))}catch(error){const kind=error instanceof ApiError&&error.status===502?"invalid":error instanceof ApiError&&error.status===401?"unauthorized":error instanceof ApiError&&error.status>=500?"service":"network";return <section className="page-wrap max-w-2xl"><CourtDiscoveryError locale={l} kind={kind}/></section>}const hasNext=loaded.length>COURT_PAGE_SIZE,courts=loaded.slice(0,COURT_PAGE_SIZE),hasFilters=Boolean(filters.search||filters.area||filters.min||filters.max||filters.active);return <section className="page-wrap pb-24"><PageHeader eyebrow={t.eyebrow} title={t.title} description={t.description}/><div className="mt-7 grid min-w-0 gap-5 lg:grid-cols-[17rem_minmax(0,1fr)]"><CourtDiscoveryFilters locale={l} filters={filters}/><main className="min-w-0 lg:col-start-2"><p className="mb-4 text-sm font-bold" role="status" aria-live="polite">{t.results(courts.length)}</p>{courts.length?<div className="grid min-w-0 gap-4 xl:grid-cols-2">{courts.map(court=><CourtCard key={court.id} court={court} locale={l}/>)}</div>:<Surface><EmptyState title={hasFilters?t.none:t.empty} description={hasFilters?t.noneText:t.emptyText}/>{hasFilters&&<div className="flex justify-center pb-6"><Link className="focus-ring min-h-11 rounded-[var(--radius-md)] border border-[var(--border-strong)] px-4 py-3 font-bold" href={`/${l}/courts`}>{t.reset}</Link></div>}</Surface>}<CourtPagination locale={l} filters={filters} hasNext={hasNext}/></main></div></section>}
