import Link from "next/link";
import { Alert } from "@/components/ui/alert";
import { EmptyState } from "@/components/ui/empty-state";
import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import { copy, type Locale } from "@/lib/copy";

export default async function Courts({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params; const l = (locale === "en" ? "en" : "ar") as Locale; const text = copy[l];
  let courts;
  try { courts = await api.courts(); } catch { return <section className="page-wrap"><h1 className="text-3xl font-black">{text.courts}</h1><Alert tone="danger" message={text.courtLoadError} className="mt-6" /></section>; }
  return <section className="page-wrap"><p className="eyebrow">{text.courtExplore}</p><h1 className="mt-2 text-3xl font-black">{text.courts}</h1><p className="mt-3 text-[var(--text-muted)]">{text.courtExploreDescription}</p>{courts.length === 0 ? <Surface className="mt-6"><EmptyState title={text.courtEmptyTitle} description={text.courtEmptyDescription} /></Surface> : <div className="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{courts.map((court) => <Link key={court.id} href={`/${l}/courts/${court.id}`} className="focus-ring rounded-[var(--radius-lg)]"><Surface as="article" variant="interactive" className="h-full" padding="md"><div className="flex items-center justify-between gap-3"><StatusBadge status={court.is_active ? "success" : "danger"} size="sm">{court.is_active ? text.courtOpen : text.courtUnavailable}</StatusBadge>{court.sport && <span className="text-xs text-[var(--text-muted)]">{court.sport[l === "ar" ? "name_ar" : "name_en"]}</span>}</div><h2 className="mt-6 text-xl font-black">{court[l === "ar" ? "name_ar" : "name_en"]}</h2><p className="mt-2 text-sm text-[var(--text-muted)]">{court.area}</p><span className="mt-6 inline-block text-sm font-bold text-[var(--brand)]">{text.courtView}</span></Surface></Link>)}</div>}</section>;
}
