import Link from "next/link";
import { copy, type Locale } from "@/lib/copy";
import type { Court } from "@/lib/types";
import { EmptyState } from "@/components/ui/empty-state";

interface FeaturedCourtsSectionProps {
  locale: string;
  courts: Court[];
  error?: boolean;
}

export function FeaturedCourtsSection({
  locale,
  courts,
  error,
}: FeaturedCourtsSectionProps) {
  const l = locale as Locale;
  const t = copy[l];
  const isAr = l === "ar";

  return (
    <section aria-labelledby="featured-heading" className="page-wrap py-12 sm:py-16">
      <div className="flex items-end justify-between gap-4 mb-8">
        <div>
          <p className="eyebrow">{t.featuredEyebrow}</p>
          <h2 id="featured-heading" className="mt-2 text-2xl sm:text-3xl font-black">
            {t.featuredTitle}
          </h2>
        </div>
        <Link
          href={`/${l}/courts`}
          className="shrink-0 text-sm font-bold text-[var(--brand)] hover:text-[var(--brand-hover)] transition-colors focus-ring"
        >
          {t.featuredViewAll}
        </Link>
      </div>

      {error ? (
        <div className="rounded-[var(--radius-lg)] border border-[var(--danger)]/30 bg-[var(--danger)]/5 px-5 py-4 text-sm text-[var(--danger)]">
          {t.featuredError}
        </div>
      ) : courts.length === 0 ? (
        <EmptyState
          title={t.featuredEmpty}
          description={t.featuredEmptyDesc}
          size="compact"
          icon={
            <svg className="size-12 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          }
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {courts.map((court) => (
            <Link
              key={court.id}
              href={`/${l}/courts/${court.id}`}
              className="group flex flex-col rounded-[var(--radius-lg)] border border-[var(--border-strong)] bg-[var(--surface-1)] p-5 transition-all duration-150 hover:border-[var(--brand)]/40 hover:bg-[var(--surface-2)] hover:-translate-y-0.5 focus-ring"
            >
              <p className="text-xs font-bold text-[var(--brand)] uppercase tracking-wide">
                {court.sport?.[isAr ? "name_ar" : "name_en"] ?? (isAr ? "رياضة" : "Sport")}
              </p>
              <h3 className="mt-2 text-lg font-bold text-[var(--text-primary)] leading-snug">
                {isAr ? court.name_ar : court.name_en}
              </h3>
              <p className="mt-1 text-sm text-[var(--text-muted)]">{court.area}</p>
              <div className="mt-4 pt-4 border-t border-[var(--border-subtle)] flex items-center justify-between">
                <span className="font-bold text-[var(--text-primary)]">
                  {court.price_per_hour}
                  <span className="text-xs font-normal text-[var(--text-muted)] ms-1">{t.priceUnit}</span>
                </span>
                <svg
                  className="size-4 text-[var(--text-muted)] group-hover:text-[var(--brand)] transition-colors rtl:rotate-180"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 5l7 7-7 7" />
                </svg>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
