"use client";

import { useEffect, useRef, useState } from "react";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { EmptyState } from "@/components/ui/empty-state";
import { ProgressBar } from "@/components/ui/progress-bar";
import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import { copy, type Locale } from "@/lib/copy";
import type { Match, MatchJoinRequest } from "@/lib/types";

type Props = {
  locale: Locale;
  initialMatch: Match;
  initialRequest: MatchJoinRequest | null;
  initialPendingRequests: MatchJoinRequest[];
};

const badgeTone = {
  open: "success",
  full: "warning",
  cancelled: "danger",
  completed: "neutral",
} as const;

export function MatchExperience({ locale, initialMatch, initialRequest, initialPendingRequests }: Props) {
  const text = copy[locale];
  const [match, setMatch] = useState(initialMatch);
  const [request, setRequest] = useState(initialRequest);
  const [pendingRequests, setPendingRequests] = useState(initialPendingRequests);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState(false);
  const alertRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (error) alertRef.current?.focus();
  }, [error]);

  async function post(path: string) {
    setBusy(path);
    setError(false);
    try {
      const response = await fetch(`/api/matches/${match.id}/${path}`, { method: "POST" });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error();
      return data;
    } catch {
      setError(true);
      return null;
    } finally {
      setBusy(null);
    }
  }

  async function join() {
    if (match.join_policy === "approval_required") {
      const result = await post("join-requests");
      if (result) setRequest(result as MatchJoinRequest);
      return;
    }
    const result = await post("join");
    if (result) setMatch(result as Match);
  }

  async function withdraw() {
    if (!request) return;
    const result = await post(`join-requests/${request.id}/withdraw`);
    if (result) setRequest(result as MatchJoinRequest);
  }

  async function leave() {
    const result = await post("leave");
    if (result) setMatch(result as Match);
  }

  async function review(joinRequest: MatchJoinRequest, action: "approve" | "reject") {
    const result = await post(`join-requests/${joinRequest.id}/${action}`);
    if (result) setPendingRequests((current) => current.filter((item) => item.id !== joinRequest.id));
  }

  const statusLabel = {
    open: text.matchOpen,
    full: text.matchFull,
    cancelled: text.matchCancelled,
    completed: text.matchCompleted,
  }[match.status];
  const capacityPercent = match.max_players ? (match.approved_participant_count / match.max_players) * 100 : 0;
  const requestStatus = request?.status;
  const canJoin = match.status === "open" && match.available_spots > 0 && !match.has_joined && requestStatus !== "pending";
  const start = new Date(match.start_time);
  const end = new Date(match.end_time);
  const dateFormat = new Intl.DateTimeFormat(locale, { dateStyle: "long" });
  const timeFormat = new Intl.DateTimeFormat(locale, { hour: "numeric", minute: "2-digit" });

  return (
    <div className="grid gap-6 lg:grid-cols-[minmax(0,1.35fr)_minmax(19rem,.65fr)]">
      <div className="space-y-6">
        <Surface as="article" padding="lg">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <p className="eyebrow">{text.matchDetails}</p>
              <h1 className="mt-2 text-3xl font-black sm:text-4xl">{match.title}</h1>
            </div>
            <StatusBadge status={badgeTone[match.status]}>{statusLabel}</StatusBadge>
          </div>

          <dl className="mt-8 grid gap-5 border-t border-[var(--border-strong)] pt-6 sm:grid-cols-2">
            {[
              [text.matchSport, match.sport_type],
              [text.matchVenue, locale === "ar" ? match.court.name_ar : match.court.name_en],
              [text.matchDate, dateFormat.format(start)],
              [text.matchTime, `${timeFormat.format(start)} – ${timeFormat.format(end)}`],
              [text.matchOrganizer, match.creator.full_name],
              [text.matchCapacity, `${match.max_players} ${text.matchPlayers}`],
              [text.matchJoined, `${match.approved_participant_count} ${text.matchPlayers}`],
              [text.matchAvailable, `${match.available_spots} ${text.matchPlayers}`],
            ].map(([label, value]) => (
              <div key={label}>
                <dt className="text-sm text-[var(--text-muted)]">{label}</dt>
                <dd className="mt-1 font-bold">{value}</dd>
              </div>
            ))}
          </dl>

          <ProgressBar className="mt-7" value={capacityPercent} label={text.matchCapacity} />
          {match.description ? (
            <section className="mt-7 border-t border-[var(--border-strong)] pt-6" aria-labelledby="match-description">
              <h2 id="match-description" className="text-lg font-black">{text.matchDescription}</h2>
              <p className="mt-2 whitespace-pre-wrap leading-7 text-[var(--text-secondary)]">{match.description}</p>
            </section>
          ) : null}
        </Surface>

        {match.can_manage ? (
          <Surface as="section" padding="lg" aria-labelledby="join-requests-heading">
            <div className="flex items-center justify-between gap-3">
              <h2 id="join-requests-heading" className="text-xl font-black">{text.matchRequests}</h2>
              <StatusBadge status="warning">{pendingRequests.length}</StatusBadge>
            </div>
            {pendingRequests.length ? (
              <ul className="mt-5 divide-y divide-[var(--border-strong)]">
                {pendingRequests.map((item) => {
                  const approving = busy === `join-requests/${item.id}/approve`;
                  const rejecting = busy === `join-requests/${item.id}/reject`;
                  return (
                    <li key={item.id} className="flex flex-col gap-3 py-4 first:pt-0 last:pb-0 sm:flex-row sm:items-center sm:justify-between">
                      <p className="font-bold">{item.requester?.full_name ?? `#${item.user_id}`}</p>
                      <div className="flex gap-2">
                        <Button aria-label={`${text.matchApprove} ${item.requester?.full_name ?? item.user_id}`} isLoading={approving} disabled={busy !== null} onClick={() => review(item, "approve")}>{text.matchApprove}</Button>
                        <Button aria-label={`${text.matchReject} ${item.requester?.full_name ?? item.user_id}`} variant="danger" isLoading={rejecting} disabled={busy !== null} onClick={() => review(item, "reject")}>{text.matchReject}</Button>
                      </div>
                    </li>
                  );
                })}
              </ul>
            ) : (
              <EmptyState size="compact" title={text.matchNoRequests} description={text.matchNoRequestsDesc} />
            )}
          </Surface>
        ) : null}
      </div>

      <aside className="h-fit lg:sticky lg:top-24">
        <Surface padding="lg">
          {error ? <div ref={alertRef} tabIndex={-1}><Alert className="mb-4" tone="danger" message={text.matchActionError} /></div> : null}
          {match.can_manage ? (
            <Alert tone="info" message={text.matchOrganizerView} />
          ) : requestStatus === "pending" ? (
            <>
              <Alert tone="warning" message={text.matchRequestPending} />
              <Button className="mt-4" fullWidth variant="outline" isLoading={busy?.endsWith("/withdraw")} disabled={busy !== null} onClick={withdraw}>{busy ? text.matchWithdrawing : text.matchWithdraw}</Button>
            </>
          ) : match.current_user_participant_status === "pending" ? (
            <Alert tone="warning" message={text.matchRequestPending} />
          ) : requestStatus === "rejected" ? (
            <Alert tone="danger" message={text.matchRequestRejected} />
          ) : match.current_user_participant_status === "approved" || requestStatus === "approved" ? (
            <>
              <Alert tone="success" message={text.matchAlreadyJoined} />
              <Button className="mt-4" fullWidth variant="outline" isLoading={busy === "leave"} disabled={busy !== null} onClick={leave}>{busy ? text.matchLeaving : text.matchLeave}</Button>
            </>
          ) : canJoin ? (
            <Button fullWidth size="lg" isLoading={busy !== null} disabled={busy !== null} onClick={join}>{busy ? text.matchJoining : text.matchJoin}</Button>
          ) : (
            <Alert tone="info" message={statusLabel} />
          )}
        </Surface>
      </aside>
    </div>
  );
}
