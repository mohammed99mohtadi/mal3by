import Link from "next/link";
import { copy, type Locale } from "@/lib/copy";

export function BrandLogo({ locale, compact = false }: { locale: string; compact?: boolean }) {
  const safe = (locale === "en" ? "en" : "ar") as Locale; const t = copy[safe];
  return <Link aria-label={t.brandHome} className="focus-ring flex min-h-11 shrink-0 items-center gap-2 rounded-[var(--radius-sm)] font-black text-white" href={`/${safe}`}><span aria-hidden className="grid size-9 place-items-center rounded-[var(--radius-md)] bg-[var(--brand)] text-[var(--brand-foreground)] shadow-[var(--shadow-sm)]">M</span>{!compact && <span className="text-xl">Mal3by</span>}</Link>;
}
