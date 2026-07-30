import Link from "next/link";
import { copy, type Locale } from "@/lib/copy";

interface FinalCtaSectionProps {
  locale: string;
}

export function FinalCtaSection({ locale }: FinalCtaSectionProps) {
  const l = locale as Locale;
  const t = copy[l];

  return (
    <section
      aria-labelledby="cta-heading"
      className="border-t border-[var(--border-strong)] bg-[var(--surface-1)]"
    >
      <div className="page-wrap py-14 sm:py-20 flex flex-col items-center text-center gap-5">
        <h2
          id="cta-heading"
          className="text-2xl sm:text-4xl font-black"
        >
          {t.finalCtaTitle}
        </h2>
        <p className="max-w-md text-[var(--text-muted)] text-base">
          {t.finalCtaDesc}
        </p>
        <Link
          href={`/${l}/courts`}
          className="brand-button inline-flex items-center gap-2 px-8 py-3.5 text-sm font-bold rounded-[var(--radius-md)] focus-ring"
        >
          {t.finalCtaButton}
          <svg className="size-4 rtl:rotate-180" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M9 5l7 7-7 7" />
          </svg>
        </Link>
      </div>
    </section>
  );
}
