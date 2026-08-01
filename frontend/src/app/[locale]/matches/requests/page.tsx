import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { MyJoinRequests } from "@/components/my-join-requests";
import { RouteRetryError } from "@/components/route-retry-error";
import { PageHeader } from "@/components/ui/page-header";
import { api } from "@/lib/api";
import type { Locale } from "@/lib/copy";
import { matchCommunityCopy } from "@/lib/match-community";
import type { MatchJoinRequest } from "@/lib/types";

export default async function Requests({params}:{params:Promise<{locale:string}>}){
  const {locale}=await params,l=(locale==="en"?"en":"ar")as Locale,t=matchCommunityCopy[l],token=(await cookies()).get("mal3by_session")?.value;
  if(!token)redirect(`/${l}/login?returnTo=/${l}/matches/requests`);
  let requests:MatchJoinRequest[]|null=null,titles:Record<number,string>={};
  try{requests=await api.myMatchRequests(token);const unique=[...new Set(requests.map(item=>item.match_id))],pairs=await Promise.all(unique.map(async id=>{try{return[id,(await api.match(token,String(id))).title]as const}catch{return[id,""]as const}}));titles=Object.fromEntries(pairs)}catch{}
  if(!requests)return <section className="page-wrap"><PageHeader title={t.myRequests}/><div className="mt-6"><RouteRetryError locale={l} message={t.loadError}/></div></section>;
  return <section className="page-wrap pb-24"><PageHeader eyebrow={t.pendingRequests} title={t.myRequests} description={t.myRequestsText}/><div className="mt-7"><MyJoinRequests locale={l} initialRequests={requests} titles={titles}/></div></section>;
}
