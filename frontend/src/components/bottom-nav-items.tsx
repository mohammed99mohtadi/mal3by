"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { copy, type Locale } from "@/lib/copy";
import { activeSection, type NavSection } from "@/lib/navigation";

const icons: Record<Exclude<NavSection, null | "matches" | "auth"> | "login", React.ReactNode> = {
  home: <path d="M3 11.5 12 4l9 7.5M5.5 10v10h13V10M9 20v-6h6v6" />,
  courts: <path d="M4 5h16v14H4zM4 12h16M12 5v14M8 8h.01M16 16h.01" />,
  bookings: <path d="M6 3v3m12-3v3M4 9h16M5 5h14a1 1 0 0 1 1 1v14H4V6a1 1 0 0 1 1-1Z" />,
  profile: <path d="M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8Zm7 8a7 7 0 0 0-14 0" />,
  login: <path d="m10 17 5-5-5-5m5 5H3m12-8h5v16h-5" />,
};

export function BottomNavItems({ locale, isLoggedIn }: { locale: Locale; isLoggedIn: boolean }) {
  const active = activeSection(usePathname() || `/${locale}`); const t = copy[locale];
  const items: { section: NavSection | "login"; label: string; href: string }[] = [
    { section: "home", label: t.navHome, href: `/${locale}` },
    { section: "courts", label: t.navCourts, href: `/${locale}/courts` },
    { section: "bookings", label: t.navBookings, href: `/${locale}/bookings` },
    isLoggedIn ? { section: "profile", label: t.navProfile, href: `/${locale}/profile` } : { section: "login", label: t.navLogin, href: `/${locale}/login` },
  ];
  return <nav aria-label={t.mobileNavigation} className="bottom-nav" dir={locale === "ar" ? "rtl" : "ltr"}>{items.map((item) => {
    const current = item.section === "login" ? active === "auth" : active === item.section;
    return <Link key={item.section} href={item.href} aria-label={item.label} aria-current={current ? "page" : undefined} className={current ? "is-active" : undefined}><svg aria-hidden="true" className="size-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{icons[item.section as keyof typeof icons]}</svg><span>{item.label}</span></Link>;
  })}</nav>;
}
