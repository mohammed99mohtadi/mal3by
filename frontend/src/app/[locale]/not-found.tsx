"use client";

import { usePathname } from "next/navigation";
import { ErrorState } from "@/components/ui/error-state";
import type { Locale } from "@/lib/copy";

export default function NotFound() {
  const locale = ((usePathname() || "/ar").startsWith("/en") ? "en" : "ar") as Locale;
  return <section className="page-wrap"><ErrorState locale={locale} kind="not-found" /></section>;
}
