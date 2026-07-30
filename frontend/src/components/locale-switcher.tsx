"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { copy, type Locale } from "@/lib/copy";

export interface LocaleSwitcherProps {
  locale: string;
}

export function LocaleSwitcher({ locale }: LocaleSwitcherProps) {
  const pathname = usePathname() || `/${locale}`;
  const currentLocale = (locale === "en" ? "en" : "ar") as Locale;
  const targetLocale: Locale = currentLocale === "ar" ? "en" : "ar";

  // Replace leading /[locale] with target locale
  const targetPathname = pathname.replace(/^\/(ar|en)/, `/${targetLocale}`);
  const t = copy[currentLocale];

  return (
    <Link
      href={targetPathname}
      aria-label={t.switchLang}
      className="inline-flex items-center justify-center min-h-[38px] px-3 rounded-[var(--radius-sm)] font-bold text-xs text-[var(--text-secondary)] border border-[var(--border-subtle)] bg-[var(--surface-2)] hover:border-[var(--brand)] hover:text-[var(--brand)] transition-colors focus-ring"
    >
      {t.switchLangShort}
    </Link>
  );
}
