"use client";

import { usePathname } from "next/navigation";
import { LoadingState } from "@/components/ui/loading-state";
import { copy, type Locale } from "@/lib/copy";

export default function Loading() {
  const locale = ((usePathname() || "/ar").startsWith("/en") ? "en" : "ar") as Locale;
  return <section className="page-wrap"><LoadingState label={copy[locale].pageLoading} /></section>;
}
