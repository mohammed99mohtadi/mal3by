import Link from "next/link";
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { MatchCard } from "@/components/match-card";
import { RouteRetryError } from "@/components/route-retry-error";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import type { Locale } from "@/lib/copy";
import { isUpcoming, matchCommunityCopy } from "@/lib/match-community";
import type { Match, MatchJoinRequest } from "@/lib/types";

export default async function MyMatches({params}:{params:Promise<{locale:string}>}){
  const {locale}=await params,l=(locale==="en"?"en":"ar")as Locale,t=matchCommunityCopy[l],token=(await cookies()).get("mal3by_session")?.value;
  if(!token)redirect(`/${l}/login?returnTo=/${l}/matches/me`);
  let created:Match[]|null=null,joined:Match[]|null=null,requests:MatchJoinRequest[]|null=null;
  try{[created,joined,requests]=await Promise.all([api.myCreatedMatches(token),api.myJoinedMatches(token),api.myMatchRequests(token)])}catch{}
  if(!created||!joined||!requests)return <section className="page-wrap"><PageHeader title={t.myMatches}/><div className="mt-6"><RouteRetryError locale={l} message={t.loadError}/></div></section>;
  const all=[...new Map([...created,...joined].map(item=>[item.id,item])).values()];
  const summary=[{label:t.upcoming,count:all.filter(isUpcoming).length},{label:t.completed,count:all.filter(item=>item.status==="completed").length},{label:t.cancelled,count:all.filter(item=>item.status==="cancelled").length},{label:t.pendingRequests,count:requests.filter(item=>item.status==="pending").length}];
  const groups=[{id:"created",label:t.created,items:created},{id:"joined",label:t.joinedGroup,items:joined}];
  return <section className="page-wrap pb-24"><PageHeader eyebrow={t.details} title={t.myMatches} description={t.myMatchesText} actions={<Link className="focus-ring flex min-h-11 items-center rounded-[var(--radius-md)] border border-[var(--border-strong)] px-4 font-bold" href={`/${l}/matches/requests`}>{t.myRequests}</Link>}/><dl className="mt-7 grid grid-cols-2 gap-3 lg:grid-cols-4">{summary.map(item=><Surface key={item.label} as="div"><dt className="text-sm text-[var(--text-muted)]">{item.label}</dt><dd className="mt-2 text-2xl font-black"><bdi>{item.count}</bdi></dd></Surface>)}</dl><div className="mt-8 space-y-10">{groups.map(group=><section key={group.id} aria-labelledby={group.id}><h2 id={group.id} className="text-xl font-black">{group.label} <bdi>({group.items.length})</bdi></h2>{group.items.length?<div className="mt-4 grid gap-4">{group.items.map(match=><MatchCard key={match.id} match={match} locale={l}/>)}</div>:<Surface className="mt-4"><EmptyState size="compact" title={t.noGroup}/></Surface>}</section>)}</div></section>;
}
