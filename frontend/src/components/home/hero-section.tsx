import Link from "next/link";
import { copy, type Locale } from "@/lib/copy";

interface HeroSectionProps {
  locale: string;
  isLoggedIn: boolean;
}

export function HeroSection({ locale, isLoggedIn }: HeroSectionProps) {
  const l = locale as Locale;
  const t = copy[l];

  const steps = [
    { icon: "🏟", label: t.howStep1Title },
    { icon: "📅", label: t.howStep2Title },
    { icon: "✓", label: t.howStep3Title },
  ];

  return (
    <section
      aria-labelledby="hero-heading"
      className="relative overflow-hidden border-b border-[var(--border-strong)]"
      style={{
        background:
          "radial-gradient(ellipse 80% 60% at 60% -20%, rgba(124,252,0,0.07) 0%, transparent 60%), linear-gradient(160deg, #080b0e 0%, #0a1a0f 100%)",
      }}
    >
      <div className="page-wrap py-14 sm:py-20 lg:py-28">
        <p className="eyebrow">{t.heroEyebrow}</p>
        <h1
          id="hero-heading"
          className="mt-4 max-w-3xl text-4xl font-black leading-tight tracking-tight sm:text-5xl lg:text-6xl"
        >
          {t.heroHeadline}
        </h1>
        <p className="mt-5 max-w-xl text-[var(--text-muted)] text-base sm:text-lg leading-relaxed">
          {t.heroSubline}
        </p>

        {/* CTAs */}
        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href={`/${l}/courts`}
            className="brand-button inline-flex items-center gap-2 px-6 py-3 text-sm font-bold rounded-[var(--radius-md)] focus-ring"
          >
            <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            {t.heroCta}
          </Link>

          {isLoggedIn ? (
            <Link
              href={`/${l}/bookings`}
              className="inline-flex items-center gap-2 px-6 py-3 text-sm font-bold rounded-[var(--radius-md)] border border-[var(--border-strong)] text-[var(--text-primary)] hover:border-[var(--brand)]/50 hover:bg-[var(--surface-2)] transition-colors focus-ring"
            >
              {t.heroCtaSecondary}
            </Link>
          ) : (
            <Link
              href={`/${l}/login`}
              className="inline-flex items-center gap-2 px-6 py-3 text-sm font-bold rounded-[var(--radius-md)] border border-[var(--border-strong)] text-[var(--text-secondary)] hover:border-[var(--brand)]/50 hover:text-[var(--text-primary)] transition-colors focus-ring"
            >
              {t.heroCtaLogin}
            </Link>
          )}
        </div>

        {/* Compact step highlights */}
        <div className="mt-12 flex flex-wrap gap-4">
          {steps.map((step, i) => (
            <div
              key={i}
              className="flex items-center gap-2 px-3 py-2 rounded-[var(--radius-md)] bg-[var(--surface-2)] border border-[var(--border-subtle)] text-xs font-semibold text-[var(--text-secondary)]"
            >
              <span aria-hidden="true" className="text-base">{step.icon}</span>
              {step.label}
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
