"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { copy, type Locale } from "@/lib/copy";
import { localeHref } from "@/lib/navigation";

export function LocaleSwitcher({ locale, compact = false }: { locale: Locale; compact?: boolean }) {
  const pathname = usePathname() || `/${locale}`; const searchParams = useSearchParams(); const target: Locale = locale === "ar" ? "en" : "ar"; const t = copy[locale];
  return <Link href={localeHref(pathname, target, searchParams)} replace hrefLang={target} lang={target} aria-label={t.switchLang} className="focus-ring inline-flex min-h-11 items-center gap-2 rounded-[var(--radius-md)] border border-[var(--border-strong)] bg-[var(--surface-2)] px-3 text-xs font-bold text-[var(--text-secondary)] transition-colors hover:border-[var(--brand)] hover:text-[var(--brand)]"><span aria-hidden>{target.toUpperCase()}</span>{!compact && <span className="hidden xl:inline">{t.switchLangShort}</span>}</Link>;
}
