import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { MatchCard } from "@/components/match-card";
import { MatchDiscoveryError } from "@/components/match-discovery-error";
import { MatchDiscoveryFilters } from "@/components/match-discovery-filters";
import { MatchPagination } from "@/components/match-pagination";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import type { Locale } from "@/lib/copy";
import { MATCH_PAGE_SIZE, backendMatchQuery, filterLoadedMatches, matchDiscoveryCopy, parseMatchFilters } from "@/lib/match-discovery";
import { ApiError } from "@/lib/types";

export default async function Matches({params,searchParams}:{params:Promise<{locale:string}>;searchParams:Promise<Record<string,string|string[]|undefined>>}) {
  const {locale}=await params,l=(locale==="en"?"en":"ar")as Locale,t=matchDiscoveryCopy[l],filters=parseMatchFilters(await searchParams),token=(await cookies()).get("mal3by_session")?.value;
  if(!token)redirect(`/${l}/login?returnTo=${encodeURIComponent(`/${l}/matches`)}`);
  let loaded;
  try{loaded=await api.matches(token,backendMatchQuery(filters))}catch(error){
    if(error instanceof ApiError&&error.status===401)redirect(`/${l}/login?returnTo=${encodeURIComponent(`/${l}/matches`)}`);
    const kind=error instanceof ApiError&&error.status===502?"invalid":error instanceof ApiError&&error.status>=500?"service":"network";
    return <section className="page-wrap"><PageHeader eyebrow={t.eyebrow} title={t.title} description={t.description}/><div className="mt-6"><MatchDiscoveryError locale={l} kind={kind}/></div></section>;
  }
  const hasNext=loaded.length>MATCH_PAGE_SIZE,pageMatches=loaded.slice(0,MATCH_PAGE_SIZE),matches=filterLoadedMatches(pageMatches,filters.q),hasFilters=Boolean(filters.q||filters.sport||filters.skill||filters.date||filters.status||filters.available||filters.sort!=="start_time");
  const actions=<><Link className="focus-ring flex min-h-11 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border-strong)] px-4 text-sm font-bold" href={`/${l}/matches/me`}>{t.mine}</Link><Link className="focus-ring flex min-h-11 items-center justify-center rounded-[var(--radius-md)] bg-[var(--brand)] px-4 text-sm font-bold text-[var(--brand-foreground)]" href={`/${l}/matches/new`}>{t.create}</Link></>;
  return <section className="page-wrap pb-24"><PageHeader eyebrow={t.eyebrow} title={t.title} description={t.description} actions={actions}/><div className="mt-7 grid min-w-0 gap-5 lg:grid-cols-[17rem_minmax(0,1fr)]"><MatchDiscoveryFilters locale={l} filters={filters}/><main className="min-w-0 lg:col-start-2"><p className="mb-4 text-sm font-bold" role="status" aria-live="polite">{t.results(matches.length)}</p>{matches.length?<div className="grid min-w-0 gap-4">{matches.map(match=><MatchCard key={match.id} match={match} locale={l}/>)}</div>:<Surface><EmptyState title={hasFilters?t.noResults:t.empty} description={hasFilters?t.noResultsText:t.emptyText}/><div className="flex justify-center pb-6">{hasFilters?<Link className="focus-ring min-h-11 rounded-[var(--radius-md)] border border-[var(--border-strong)] px-4 py-3 font-bold" href={`/${l}/matches`}>{t.reset}</Link>:<Link className="focus-ring min-h-11 rounded-[var(--radius-md)] bg-[var(--brand)] px-4 py-3 font-bold text-[var(--brand-foreground)]" href={`/${l}/matches/new`}>{t.create}</Link>}</div></Surface>}<MatchPagination locale={l} filters={filters} hasNext={hasNext}/></main></div></section>;
}
