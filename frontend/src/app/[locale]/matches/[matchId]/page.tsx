import Link from "next/link";
import { cookies } from "next/headers";
import { Alert } from "@/components/ui/alert";
import { Surface } from "@/components/ui/surface";
import { MatchExperience } from "@/components/match-experience";
import { RouteRetryError } from "@/components/route-retry-error";
import { api } from "@/lib/api";
import { copy, type Locale } from "@/lib/copy";
import { matchCommunityCopy } from "@/lib/match-community";
import { ApiError, type Match, type MatchJoinRequest, type MatchParticipant } from "@/lib/types";

export default async function MatchPage({ params }: { params: Promise<{ locale: string; matchId: string }> }) {
  const { locale, matchId } = await params;
  const language = (locale === "en" ? "en" : "ar") as Locale;
  const text = copy[language];
  const community = matchCommunityCopy[language];
  const token = (await cookies()).get("mal3by_session")?.value;

  if (!token) {
    return <MatchFailure locale={language} message={text.matchUnauthorized} login />;
  }

  let match: Match | null = null;
  let currentRequest: MatchJoinRequest | null = null;
  let pendingRequests: MatchJoinRequest[] = [];
  let participants: MatchParticipant[] = [];
  let failureMessage: string | null = null;
  let showLogin = false;
  let showRetry = false;
  try {
    if (!/^\d+$/.test(matchId)) throw new ApiError(404, "Not found");
    const loadedMatch = await api.match(token, matchId);
    match = loadedMatch;
    if (loadedMatch.can_manage) {
      [pendingRequests, participants] = await Promise.all([api.matchRequests(token, matchId), api.matchParticipants(token, matchId)]);
    } else if (loadedMatch.join_policy === "approval_required") {
      const requests = await api.myMatchRequests(token).catch(() => []);
      currentRequest = requests.filter((item) => item.match_id === loadedMatch.id).sort((a, b) => b.id - a.id)[0] ?? null;
    }
  } catch (error) {
    const status = error instanceof ApiError ? error.status : 500;
    failureMessage = status === 401 ? community.unauthorized : status === 403 || status === 404 ? community.notFound : community.loadError;
    showLogin = status === 401;
    showRetry = status >= 500;
  }
  if (failureMessage) return <MatchFailure locale={language} message={failureMessage} login={showLogin} retry={showRetry} />;
  if (!match) return <MatchFailure locale={language} message={text.matchLoadError} />;
  return (
    <section className="page-wrap">
      <Link className="focus-ring text-sm font-bold text-[var(--brand)]" href={`/${language}/matches`}>{community.back}</Link>
      <div className="mt-5">
        <MatchExperience locale={language} initialMatch={match} initialRequest={currentRequest} initialPendingRequests={pendingRequests} initialParticipants={participants} />
      </div>
    </section>
  );
}

export function MatchFailure({ locale, message, login = false, retry = false }: { locale: Locale; message: string; login?: boolean; retry?: boolean }) {
  const text = copy[locale];
  return (
    <section className="page-wrap max-w-2xl">
      <Surface padding="lg">
        {retry ? <RouteRetryError locale={locale} message={message} /> : <Alert tone="danger" message={message} />}
        <div className="mt-5 flex flex-wrap gap-3">
          {login ? <Link className="focus-ring inline-flex min-h-11 items-center rounded-[var(--radius-md)] bg-[var(--brand)] px-4 font-bold text-[var(--brand-foreground)]" href={`/${locale}/login`}>{text.matchLogin}</Link> : null}
          <Link className="focus-ring inline-flex min-h-11 items-center rounded-[var(--radius-md)] border border-[var(--border-strong)] px-4 font-bold" href={`/${locale}/matches`}>{matchCommunityCopy[locale].back}</Link>
        </div>
      </Surface>
    </section>
  );
}
