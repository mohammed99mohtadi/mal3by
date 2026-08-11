import type { Metadata } from "next";
import "../globals.css";
import { Header } from "@/components/header";
import { BottomNavigation } from "@/components/bottom-navigation";
import { SiteFooter } from "@/components/site-footer";
import { SkipLink } from "@/components/ui/skip-link";
import { cookies } from "next/headers";
import type { Locale } from "@/lib/copy";

export const metadata: Metadata = { title: "MAL3ABY | Sports courts", description: "Discover sports courts in Kuwait" };
export default async function LocaleLayout({ children, params }: { children: React.ReactNode; params: Promise<{ locale: string }> }) {
  const { locale } = await params; const safe = (locale === "en" ? "en" : "ar") as Locale; const isLoggedIn = Boolean((await cookies()).get("mal3by_session"));
  return <html lang={safe} dir={safe === "ar" ? "rtl" : "ltr"}><body className={`${safe === "ar" ? "font-ar" : "font-en"} app-shell`}><SkipLink locale={safe} /><Header locale={safe} /><main id="main-content" tabIndex={-1} className="main-content">{children}</main><SiteFooter locale={safe} isLoggedIn={isLoggedIn} /><BottomNavigation locale={safe} /></body></html>;
}
