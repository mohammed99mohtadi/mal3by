"use client";

import { useEffect } from "react";
import { usePathname } from "next/navigation";
import { ErrorState } from "@/components/ui/error-state";
import { copy, type Locale } from "@/lib/copy";

export default function ErrorPage({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  const locale = ((usePathname() || "/ar").startsWith("/en") ? "en" : "ar") as Locale;
  useEffect(() => { console.error(error); }, [error]);
  return <section className="page-wrap"><ErrorState locale={locale} actionLabel={copy[locale].retry} onAction={reset} /></section>;
}
