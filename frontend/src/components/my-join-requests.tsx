"use client";
import { useRef, useState } from "react";
import Link from "next/link";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Dialog } from "@/components/ui/dialog";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import { matchCommunityCopy, positionLabel, requestLabel, requestTone } from "@/lib/match-community";
import type { Locale } from "@/lib/copy";
import type { MatchJoinRequest } from "@/lib/types";

export function MyJoinRequests({locale,initialRequests,titles}:{locale:Locale;initialRequests:MatchJoinRequest[];titles:Record<number,string>}){
  const t=matchCommunityCopy[locale],[requests,setRequests]=useState(initialRequests),[selected,setSelected]=useState<MatchJoinRequest|null>(null),[busy,setBusy]=useState(false),[error,setError]=useState(false),confirmRef=useRef<HTMLButtonElement>(null),date=new Intl.DateTimeFormat(locale,{dateStyle:"medium",timeStyle:"short"});
  async function withdraw(){if(!selected||busy)return;setBusy(true);setError(false);try{const response=await fetch(`/api/matches/${selected.match_id}/join-requests/${selected.id}/withdraw`,{method:"POST"});const data=await response.json().catch(()=>null);if(!response.ok)throw new Error();setRequests(current=>current.map(item=>item.id===selected.id?data:item));setSelected(null)}catch{setError(true)}finally{setBusy(false)}}
  return <>{error&&<Alert className="mb-4" tone="danger" message={t.actionError}/>}<div role="status" aria-live="polite" className="sr-only">{busy?t.loading:""}</div>{requests.length?<ul className="grid gap-4">{requests.map(item=><li key={item.id}><Surface as="article"><div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between"><div className="min-w-0"><h2 className="break-words text-lg font-black" dir="auto">{titles[item.match_id]??`${t.unknownMatch} #${item.match_id}`}</h2><dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">{item.requested_position_code&&<div><dt className="text-[var(--text-muted)]">{t.position}</dt><dd>{positionLabel(locale,item.requested_position_code)}</dd></div>}<div><dt className="text-[var(--text-muted)]">{t.createdAt}</dt><dd><time dateTime={item.created_at}>{date.format(new Date(item.created_at))}</time></dd></div>{item.reviewed_at&&<div><dt className="text-[var(--text-muted)]">{t.reviewedAt}</dt><dd><time dateTime={item.reviewed_at}>{date.format(new Date(item.reviewed_at))}</time></dd></div>}</dl></div><StatusBadge status={requestTone(item.status)}>{requestLabel(locale,item.status)}</StatusBadge></div><div className="mt-4 flex flex-col gap-2 border-t border-[var(--border)] pt-4 sm:flex-row"><Link className="focus-ring flex min-h-11 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border-strong)] px-4 font-bold" href={`/${locale}/matches/${item.match_id}`}>{t.viewMatch}</Link>{item.status==="pending"&&<Button variant="outline" disabled={busy} onClick={()=>setSelected(item)}>{t.withdraw}</Button>}</div></Surface></li>)}</ul>:<Surface><EmptyState title={t.noMyRequests}/></Surface>}<Dialog open={selected!==null} onClose={()=>!busy&&setSelected(null)} title={t.confirmWithdraw} initialFocusRef={confirmRef}><div className="flex justify-end gap-2"><Button variant="outline" disabled={busy} onClick={()=>setSelected(null)}>{t.cancel}</Button><Button ref={confirmRef} isLoading={busy} disabled={busy} onClick={withdraw}>{t.confirm}</Button></div></Dialog></>
}
