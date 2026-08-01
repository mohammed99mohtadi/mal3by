import Link from "next/link";
import { BrandLogo } from "@/components/brand-logo";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { copy, type Locale } from "@/lib/copy";

export function SiteFooter({ locale, isLoggedIn }: { locale: Locale; isLoggedIn: boolean }) {
  const t = copy[locale];
  return <footer aria-label={t.footerLabel} className="mt-auto border-t border-[var(--border-strong)] bg-[var(--surface-1)]">
    <div className="page-wrap grid gap-8 py-10 sm:grid-cols-[1fr_auto] sm:items-start">
      <div><BrandLogo locale={locale} /><p className="text-body-sm mt-3 max-w-md text-[var(--text-muted)]">{t.footerSummary}</p></div>
      <div className="flex flex-wrap items-center gap-x-5 gap-y-3 text-sm font-semibold"><Link className="focus-ring hover:text-[var(--brand)]" href={`/${locale}/courts`}>{t.courts}</Link>{isLoggedIn && <Link className="focus-ring hover:text-[var(--brand)]" href={`/${locale}/bookings`}>{t.bookings}</Link>}<LocaleSwitcher locale={locale} compact /></div>
      <p className="text-helper sm:col-span-2">© {new Date().getUTCFullYear()} {t.footerCopyright}</p>
    </div>
  </footer>;
}
