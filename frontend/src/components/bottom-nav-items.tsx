"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { copy, type Locale } from "@/lib/copy";

export interface BottomNavItemsProps {
  locale: string;
  isLoggedIn: boolean;
}

export function BottomNavItems({ locale, isLoggedIn }: BottomNavItemsProps) {
  const rawPathname = usePathname() || `/${locale}`;
  // Strip query string if any
  const pathname = rawPathname.split("?")[0];
  const currentLocale = (locale === "en" ? "en" : "ar") as Locale;
  const t = copy[currentLocale];

  const isHomeActive = pathname === `/${locale}` || pathname === `/${locale}/`;
  const isCourtsActive = pathname === `/${locale}/courts` || pathname.startsWith(`/${locale}/courts/`);
  const isBookingsActive = pathname === `/${locale}/bookings` || pathname.startsWith(`/${locale}/bookings/`);
  const isProfileActive = pathname === `/${locale}/profile` || pathname.startsWith(`/${locale}/profile/`);
  const isLoginActive = pathname === `/${locale}/login` || pathname.startsWith(`/${locale}/login/`);

  const items = [
    {
      label: t.navHome,
      href: `/${locale}`,
      isActive: isHomeActive,
      icon: (
        <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 00-1-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      ),
    },
    {
      label: t.navCourts,
      href: `/${locale}/courts`,
      isActive: isCourtsActive,
      icon: (
        <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
    },
    {
      label: t.navBookings,
      href: `/${locale}/bookings`,
      isActive: isBookingsActive,
      icon: (
        <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
    },
    isLoggedIn
      ? {
          label: t.navProfile,
          href: `/${locale}/profile`,
          isActive: isProfileActive,
          icon: (
            <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          ),
        }
      : {
          label: t.navLogin,
          href: `/${locale}/login`,
          isActive: isLoginActive,
          icon: (
            <svg className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1" />
            </svg>
          ),
        },
  ];

  return (
    <nav
      aria-label="Mobile navigation"
      className="bottom-nav grid-cols-4"
    >
      {items.map((item) => (
        <Link
          key={item.label}
          href={item.href}
          aria-current={item.isActive ? "page" : undefined}
          className={`flex flex-col items-center justify-center gap-0.5 p-1 min-h-[44px] transition-colors focus-ring ${
            item.isActive
              ? "text-[var(--brand)] font-bold"
              : "text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          }`}
        >
          {item.icon}
          <span className="text-[0.65rem] truncate">{item.label}</span>
        </Link>
      ))}
    </nav>
  );
}
