import { copy, type Locale } from "@/lib/copy";

interface WhyMal3bySectionProps {
  locale: string;
}

export function WhyMal3bySection({ locale }: WhyMal3bySectionProps) {
  const l = locale as Locale;
  const t = copy[l];

  const benefits = [
    {
      title: t.whyBenefit1Title,
      desc: t.whyBenefit1Desc,
      icon: (
        <svg className="size-6 text-[var(--brand)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      ),
    },
    {
      title: t.whyBenefit2Title,
      desc: t.whyBenefit2Desc,
      icon: (
        <svg className="size-6 text-[var(--brand)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      ),
    },
    {
      title: t.whyBenefit3Title,
      desc: t.whyBenefit3Desc,
      icon: (
        <svg className="size-6 text-[var(--brand)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
        </svg>
      ),
    },
    {
      title: t.whyBenefit4Title,
      desc: t.whyBenefit4Desc,
      icon: (
        <svg className="size-6 text-[var(--brand)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M12 18h.01M8 21h8a2 2 0 002-2V5a2 2 0 00-2-2H8a2 2 0 00-2 2v14a2 2 0 002 2z" />
        </svg>
      ),
    },
  ];

  return (
    <section aria-labelledby="why-heading" className="page-wrap py-12 sm:py-16">
      <h2
        id="why-heading"
        className="text-2xl sm:text-3xl font-black text-center mb-10"
      >
        {t.whyTitle}
      </h2>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {benefits.map((b) => (
          <div
            key={b.title}
            className="flex flex-col gap-3 rounded-[var(--radius-lg)] border border-[var(--border-strong)] bg-[var(--surface-1)] p-5"
          >
            <div className="size-10 flex items-center justify-center rounded-[var(--radius-md)] bg-[var(--brand)]/10 border border-[var(--brand)]/20">
              {b.icon}
            </div>
            <div>
              <p className="font-bold text-[var(--text-primary)]">{b.title}</p>
              <p className="mt-1 text-sm text-[var(--text-muted)] leading-relaxed">{b.desc}</p>
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}
