import Image from "next/image";
import Link from "next/link";
import { StatusBadge } from "@/components/ui/status-badge";
import { formatMoney } from "@/lib/booking-ux";
import { courtDiscoveryCopy } from "@/lib/court-discovery";
import type { Locale } from "@/lib/copy";
import type { Court } from "@/lib/types";

export function CourtCard({court,locale}:{court:Court;locale:Locale}) {
  const t=courtDiscoveryCopy[locale],name=court[locale==="ar"?"name_ar":"name_en"],sport=court.sport?.[locale==="ar"?"name_ar":"name_en"];
  return <Link href={`/${locale}/courts/${encodeURIComponent(String(court.id))}`} aria-label={`${t.view}: ${name}`} className="court-result-card focus-ring group">
    <article className="contents">
      <div className="court-result-media">{court.image_url?<Image src={court.image_url} alt="" fill sizes="(max-width:639px) 120px,180px" className="object-cover transition-transform duration-300 group-hover:scale-105" unoptimized/>:<div className="court-result-fallback" aria-label={t.fallback}><span aria-hidden>⌂</span></div>}</div>
      <div className="min-w-0 py-3 pe-3"><div className="flex items-start justify-between gap-2"><div className="min-w-0"><h2 className="truncate text-base font-black" dir="auto">{name}</h2><p className="mt-1 truncate text-xs text-[var(--text-muted)]" dir="auto">{sport?`${sport} · `:""}{court.area}</p></div><StatusBadge status={court.is_active?"success":"danger"} size="sm">{court.is_active?t.active:t.inactive}</StatusBadge></div><div className="mt-4 flex items-end justify-between gap-2"><strong className="text-sm"><bdi>{formatMoney(locale,court.price_per_hour,court.currency)}</bdi><small className="ms-1 font-normal text-[var(--text-muted)]">{t.perHour}</small></strong><span className="text-xs font-black text-[var(--brand)]">{t.view}</span></div></div>
    </article>
  </Link>;
}
