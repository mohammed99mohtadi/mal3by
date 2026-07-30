import { copy, type Locale } from "@/lib/copy";

interface HowItWorksSectionProps {
  locale: string;
}

export function HowItWorksSection({ locale }: HowItWorksSectionProps) {
  const l = locale as Locale;
  const t = copy[l];

  const steps = [
    {
      number: "01",
      title: t.howStep1Title,
      desc: t.howStep1Desc,
      icon: (
        <svg className="size-7 text-[var(--brand)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
        </svg>
      ),
    },
    {
      number: "02",
      title: t.howStep2Title,
      desc: t.howStep2Desc,
      icon: (
        <svg className="size-7 text-[var(--brand)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
        </svg>
      ),
    },
    {
      number: "03",
      title: t.howStep3Title,
      desc: t.howStep3Desc,
      icon: (
        <svg className="size-7 text-[var(--brand)]" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
  ];

  return (
    <section
      aria-labelledby="how-heading"
      className="border-y border-[var(--border-strong)] bg-[var(--surface-1)]"
    >
      <div className="page-wrap py-12 sm:py-16">
        <h2
          id="how-heading"
          className="text-2xl sm:text-3xl font-black text-center mb-10"
        >
          {t.howTitle}
        </h2>
        <div className="grid gap-5 sm:grid-cols-3">
          {steps.map((step) => (
            <div
              key={step.number}
              className="flex flex-col gap-4 rounded-[var(--radius-lg)] border border-[var(--border-strong)] bg-[var(--surface-2)] p-5"
            >
              <div className="flex items-center gap-3">
                <span className="text-xs font-black text-[var(--brand)] tracking-widest opacity-60">
                  {step.number}
                </span>
                {step.icon}
              </div>
              <div>
                <p className="font-bold text-[var(--text-primary)]">{step.title}</p>
                <p className="mt-1.5 text-sm text-[var(--text-muted)] leading-relaxed">{step.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
