"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { copy, type Locale } from "@/lib/copy";
import { BrandLogo } from "@/components/brand-logo";
import { LocaleSwitcher } from "@/components/locale-switcher";
import { Button } from "@/components/ui/button";

export interface HeaderNavProps {
  locale: string;
  isLoggedIn: boolean;
}

export function HeaderNav({ locale, isLoggedIn }: HeaderNavProps) {
  const pathname = usePathname() || `/${locale}`;
  const currentLocale = (locale === "en" ? "en" : "ar") as Locale;
  const t = copy[currentLocale];

  const isCourtsActive = pathname.startsWith(`/${locale}/courts`);
  const isBookingsActive = pathname.startsWith(`/${locale}/bookings`);
  const isProfileActive = pathname.startsWith(`/${locale}/profile`);

  return (
    <header className="sticky top-0 z-20 border-b border-[var(--border-strong)] bg-[var(--bg-app)]/90 backdrop-blur-md">
      <nav
        aria-label="Main navigation"
        className="page-wrap py-3 flex items-center justify-between gap-4"
      >
        <BrandLogo locale={locale} />

        <div className="hidden md:flex items-center gap-6 text-sm font-semibold">
          <Link
            href={`/${locale}/courts`}
            aria-current={isCourtsActive ? "page" : undefined}
            className={`transition-colors focus-ring ${
              isCourtsActive
                ? "text-[var(--brand)] font-bold"
                : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
            }`}
          >
            {t.courts}
          </Link>

          {isLoggedIn && (
            <Link
              href={`/${locale}/bookings`}
              aria-current={isBookingsActive ? "page" : undefined}
              className={`transition-colors focus-ring ${
                isBookingsActive
                  ? "text-[var(--brand)] font-bold"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              {t.bookings}
            </Link>
          )}

          <LocaleSwitcher locale={locale} />

          {isLoggedIn ? (
            <>
              <Link
                href={`/${locale}/profile`}
                aria-current={isProfileActive ? "page" : undefined}
                className={`transition-colors focus-ring ${
                  isProfileActive
                    ? "text-[var(--brand)] font-bold"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                }`}
              >
                {t.profile}
              </Link>
              <form action="/api/auth/logout" method="post">
                <Button type="submit" variant="ghost" size="sm">
                  {t.logout}
                </Button>
              </form>
            </>
          ) : (
            <Link href={`/${locale}/login`}>
              <Button variant="primary" size="sm" type="button">
                {t.login}
              </Button>
            </Link>
          )}
        </div>

        <div className="flex md:hidden items-center gap-2">
          <LocaleSwitcher locale={locale} />
        </div>
      </nav>
    </header>
  );
}
