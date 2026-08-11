import Link from "next/link";
import { AuthBrand } from "@/components/auth-brand";
import { AuthAction } from "@/components/auth-action";
import { BrandLogo } from "@/components/brand-logo";
import { Surface } from "@/components/ui/surface";
import { copy, type Locale } from "@/lib/copy";

export function AuthShell({ locale, mode, children }: { locale: Locale; mode: "login" | "register"; children: React.ReactNode }) {
  const t = copy[locale];
  if (mode === "login") return <section className="auth-entry" aria-labelledby="login-title">
    <div className="auth-entry-glow" aria-hidden="true" />
    <div className="auth-entry-content reveal-in">
      <div className="auth-entry-topbar">
        <AuthBrand locale={locale} />
      </div>
      <div className="auth-login-card">
        <div className="auth-welcome">
          <p className="eyebrow">{t.authEyebrow}</p>
          <h1 id="login-title" className="auth-title">{t.loginTitle}</h1>
          <p>{t.loginDescription}</p>
        </div>
        {children}
        <div className="auth-register-entry">
          <span>{t.noAccount}</span>
          <AuthAction href={`/${locale}/register`}>{t.register}</AuthAction>
        </div>
      </div>
      <p className="auth-privacy-note">{t.authPrivacyNote}</p>
    </div>
  </section>;
  return <section className="page-wrap grid min-h-[calc(100dvh-var(--header-height)-10rem)] items-center gap-8 py-8 lg:grid-cols-[minmax(0,.9fr)_minmax(24rem,1.1fr)] lg:py-12">
    <aside className="hidden min-h-[34rem] flex-col justify-between overflow-hidden rounded-[var(--radius-xl)] border border-[var(--border-strong)] bg-[radial-gradient(circle_at_top,var(--surface-elevated),var(--surface-1)_65%)] p-8 lg:flex" aria-label={t.authBenefitsLabel}>
      <BrandLogo locale={locale} /><div><p className="eyebrow">{t.authEyebrow}</p><p className="text-display mt-4 max-w-lg">{t.registerPanelTitle}</p><p className="text-body mt-4 max-w-md text-[var(--text-muted)]">{t.authPanelDescription}</p><ul className="mt-8 space-y-3 text-sm text-[var(--text-secondary)]">{[t.authBenefitCourts,t.authBenefitSlots,t.authBenefitBookings].map((item)=><li key={item} className="flex gap-2"><span aria-hidden className="text-[var(--brand)]">✓</span>{item}</li>)}</ul></div>
    </aside>
    <div className="mx-auto w-full max-w-lg"><div className="mb-6 lg:hidden"><BrandLogo locale={locale} /></div><Surface padding="lg" variant="elevated"><p className="eyebrow">{t.authEyebrow}</p><h1 className="text-page-title mt-2">{t.registerTitle}</h1><p className="text-body-sm mt-2 text-[var(--text-muted)]">{t.registerDescription}</p>{children}<p className="mt-6 text-center text-sm text-[var(--text-muted)]">{t.haveAccount} <Link className="focus-ring rounded-sm font-bold text-[var(--brand)]" href={`/${locale}/login`}>{t.login}</Link></p></Surface></div>
  </section>;
}
