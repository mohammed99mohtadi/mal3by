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
        <div className="flex w-full flex-col justify-center gap-3 sm:w-auto sm:flex-row"><Link href={`/${l}/courts`} className="button-link px-8">{t.finalCtaButton}</Link><Link href={`/${l}/matches`} className="button-link button-link-secondary px-8">{l==="ar"?"استكشف المباريات":"Explore matches"}</Link></div>
      </div>
    </section>
  );
}
