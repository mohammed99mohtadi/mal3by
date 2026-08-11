"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BrandLogo } from "@/components/brand-logo";
import { UserMenu } from "@/components/user-menu";
import { copy, type Locale } from "@/lib/copy";
import { activeSection } from "@/lib/navigation";

export interface HeaderNavProps { locale: Locale; isLoggedIn: boolean; userName?: string; role?: string; isAdmin?: boolean; }

export function HeaderNav({ locale, isLoggedIn, userName, role, isAdmin }: HeaderNavProps) {
  const pathname = usePathname() || `/${locale}`;
  const active = activeSection(pathname);
  const t = copy[locale];
  const linkClass = (current: boolean) => `focus-ring rounded-[var(--radius-sm)] px-3 py-2 transition-colors ${current ? "bg-[var(--brand)]/10 font-bold text-[var(--brand)]" : "text-[var(--text-secondary)] hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)]"}`;

  return <header className="sticky top-0 z-30 border-b border-[var(--border-strong)] bg-[var(--bg-app)]/90 backdrop-blur-md">
    <nav aria-label={t.mainNavigation} className="page-wrap flex min-h-[var(--header-height)] items-center justify-between gap-3 py-2">
      <BrandLogo locale={locale} />
      <div className="hidden items-center gap-1 lg:flex">
        <Link href={`/${locale}`} aria-current={active === "home" ? "page" : undefined} className={linkClass(active === "home")}>{t.navHome}</Link>
        <Link href={`/${locale}/courts`} aria-current={active === "courts" ? "page" : undefined} className={linkClass(active === "courts")}>{t.navCourts}</Link>
        {isLoggedIn && <Link href={`/${locale}/bookings`} aria-current={active === "bookings" ? "page" : undefined} className={linkClass(active === "bookings")}>{t.navBookings}</Link>}
        <Link href={`/${locale}/community`} aria-current={active === "matches" ? "page" : undefined} className={linkClass(active === "matches")}>{locale === "ar" ? "المجتمع" : "Community"}</Link>
      </div>
      <div className="flex items-center gap-2">
        {isLoggedIn ? <UserMenu locale={locale} name={userName} role={role} isAdmin={isAdmin} /> : <div className="hidden items-center gap-2 lg:flex">
          <Link className={linkClass(active === "auth")} href={`/${locale}/login`}>{t.login}</Link>
          <Link className="focus-ring inline-flex min-h-11 items-center rounded-[var(--radius-md)] bg-[var(--brand)] px-4 text-sm font-bold text-[var(--brand-foreground)]" href={`/${locale}/register`}>{t.register}</Link>
        </div>}
      </div>
    </nav>
  </header>;
}
