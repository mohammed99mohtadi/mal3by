import Link from "next/link";
import { Availability } from "@/components/availability";
import { Alert } from "@/components/ui/alert";
import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import { copy, type Locale } from "@/lib/copy";

export default async function CourtDetail({ params }: { params: Promise<{ locale: string; courtId: string }> }) {
  const { locale, courtId } = await params; const l = (locale === "en" ? "en" : "ar") as Locale; const text = copy[l];
  let court;
  try { court = await api.court(courtId); } catch { return <section className="page-wrap"><Link className="focus-ring text-sm font-bold text-[var(--brand)]" href={`/${l}/courts`}>{text.back}</Link><h1 className="mt-5 text-3xl font-black">{text.courtDetails}</h1><Alert tone="danger" message={text.courtNotFound} className="mt-6" /></section>; }
  return <section className="page-wrap"><Link className="focus-ring text-sm font-bold text-[var(--brand)]" href={`/${l}/courts`}>{text.back}</Link><div className="mt-5 grid gap-7 lg:grid-cols-[1.4fr_.6fr]"><Surface as="article" padding="lg"><div className="flex flex-wrap items-center justify-between gap-3"><StatusBadge status={court.is_active ? "success" : "danger"}>{court.is_active ? text.courtOpen : text.courtUnavailable}</StatusBadge>{court.sport && <span className="text-sm text-[var(--text-muted)]">{court.sport[l === "ar" ? "name_ar" : "name_en"]}</span>}</div><h1 className="mt-5 text-3xl font-black">{court[l === "ar" ? "name_ar" : "name_en"]}</h1><p className="mt-3 text-[var(--text-muted)]">{court.area}{court.address ? ` · ${court.address}` : ""}</p>{court[l === "ar" ? "description_ar" : "description_en"] && <p className="mt-6 leading-7 text-[var(--text-secondary)]">{court[l === "ar" ? "description_ar" : "description_en"]}</p>}</Surface><aside className="h-fit lg:sticky lg:top-24"><Surface padding="md"><h2 className="text-xl font-black">{text.courtAvailability}</h2><p className="mt-2 text-sm text-[var(--text-muted)]">{text.courtAvailabilityDescription}</p><Availability courtId={courtId} locale={l} inactive={!court.is_active} /></Surface></aside></div></section>;
}
