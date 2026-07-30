import { cookies } from "next/headers";
import { api } from "@/lib/api";
import { type Locale } from "@/lib/copy";
import type { Court } from "@/lib/types";
import { HeroSection } from "@/components/home/hero-section";
import { FeaturedCourtsSection } from "@/components/home/featured-courts-section";
import { HowItWorksSection } from "@/components/home/how-it-works-section";
import { WhyMal3bySection } from "@/components/home/why-mal3by-section";
import { FinalCtaSection } from "@/components/home/final-cta-section";

export default async function Home({
  params,
}: {
  params: Promise<{ locale: string }>;
}) {
  const { locale } = await params;
  const l = (locale === "en" ? "en" : "ar") as Locale;

  const cookieStore = await cookies();
  const isLoggedIn = Boolean(cookieStore.get("mal3by_session"));

  let courts: Court[] = [];
  let courtsError = false;
  try {
    courts = (await api.courts()).slice(0, 3);
  } catch {
    courtsError = true;
  }

  return (
    <>
      <HeroSection locale={l} isLoggedIn={isLoggedIn} />
      <FeaturedCourtsSection locale={l} courts={courts} error={courtsError} />
      <HowItWorksSection locale={l} />
      <WhyMal3bySection locale={l} />
      <FinalCtaSection locale={l} />
    </>
  );
}
