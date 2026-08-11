import Link from "next/link";
import { BrandLogo } from "@/components/brand-logo";
import { copy, type Locale } from "@/lib/copy";

export function SiteFooter({locale,isLoggedIn}:{locale:Locale;isLoggedIn:boolean}) {
  const t=copy[locale], ar=locale==="ar";
  const linkClass="focus-ring inline-flex min-h-11 items-center rounded-[var(--radius-sm)] text-sm font-semibold text-[var(--text-secondary)] transition hover:text-[var(--brand)]";
  const links=[
    [t.courts,`/${locale}/courts`],
    [ar?"المباريات":"Matches",`/${locale}/matches`],
    [ar?"المجتمع":"Community",`/${locale}/community`],
    ...(isLoggedIn?[[t.bookings,`/${locale}/bookings`],[ar?"الملف الشخصي":"Profile",`/${locale}/profile`]]:[[ar?"تسجيل الدخول":"Sign in",`/${locale}/login`]]),
  ];
  return <footer aria-label={t.footerLabel} className="relative mt-auto overflow-hidden border-t border-[var(--border-strong)] bg-[linear-gradient(180deg,var(--surface-1),#0b1013)]"><div className="page-wrap py-12 sm:py-16"><div className="grid gap-10 border-b border-[var(--border-subtle)] pb-10 md:grid-cols-[1.4fr_.7fr_.9fr]"><div><BrandLogo locale={locale}/><p className="mt-4 max-w-md text-sm leading-7 text-[var(--text-muted)]">{t.footerSummary}</p><p className="mt-4 inline-flex rounded-full border border-[var(--brand)]/20 bg-[var(--brand)]/5 px-3 py-1.5 text-xs font-bold text-[var(--brand)]">{t.footerTagline}</p></div><nav aria-label={ar?"استكشف":"Explore"}><h2 className="mb-3 text-sm font-black uppercase tracking-wide">{ar?"استكشف":"Explore"}</h2><div className="grid">{links.map(([label,href])=><Link key={href} className={linkClass} href={href}>{label}</Link>)}</div></nav><nav aria-label={ar?"الدعم والسياسات":"Support and policies"}><h2 className="mb-3 text-sm font-black uppercase tracking-wide">{ar?"الدعم والسياسات":"Support & policies"}</h2><div className="grid">{[[ar?"الخصوصية":"Privacy","privacy"],[ar?"الشروط":"Terms","terms"],[ar?"المساعدة":"Help","help"]].map(([label,path])=><Link key={path} className={linkClass} href={`/${locale}/${path}`}>{label}</Link>)}</div></nav></div><div className="flex flex-col gap-5 pt-7 sm:flex-row sm:items-center sm:justify-between"><p className="text-helper">© {new Date().getUTCFullYear()} {t.footerCopyright}</p></div></div></footer>;
}
