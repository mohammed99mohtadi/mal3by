import { cookies } from "next/headers";
import { api } from "@/lib/api";
import { type Locale } from "@/lib/copy";
import type { Court } from "@/lib/types";
import { HeroSection } from "@/components/home/hero-section";
import { FeaturedCourtsSection } from "@/components/home/featured-courts-section";
import { HowItWorksSection } from "@/components/home/how-it-works-section";
import { FinalCtaSection } from "@/components/home/final-cta-section";
import { ProductSections } from "@/components/home/product-sections";

export default async function Home({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const l = (locale === "en" ? "en" : "ar") as Locale;

  const cookieStore = await cookies();
  const token = cookieStore.get("mal3by_session")?.value;
  const isLoggedIn = Boolean(token);

  let courts: Court[] = [];
  let courtsError = false;
  let isOwner = false;
  if (token) {
    try {
      const user = await api.me(token);
      isOwner = user.role === "owner" || user.role === "admin";
    } catch {
      // Keep the public homepage available if an expired session cannot resolve.
    }
  }
  try {
    courts = await api.courts(new URLSearchParams({ is_active: "true", limit: "20" }));
  } catch {
    courtsError = true;
  }

  return (
    <>
      <HeroSection locale={l} isLoggedIn={isLoggedIn} />
      <FeaturedCourtsSection locale={l} courts={courts.slice(0, 3)} error={courtsError} />
      <HowItWorksSection locale={l} />
      <ProductSections locale={l} courts={courts} isLoggedIn={isLoggedIn} isOwner={isOwner} />
      <FinalCtaSection locale={l} />
    </>
  );
}
