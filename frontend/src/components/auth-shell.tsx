import { AuthBrand } from "@/components/auth-brand";
import { AuthAction } from "@/components/auth-action";
import { copy, type Locale } from "@/lib/copy";

export function AuthShell({ locale, mode, children }: { locale: Locale; mode: "splash" | "login" | "register" | "forgot" | "language"; children: React.ReactNode }) {
  const t = copy[locale];
  if (mode === "splash") return <section className="auth-entry auth-splash" aria-labelledby="splash-title"><div className="auth-entry-glow" aria-hidden="true" /><div className="auth-splash-content reveal-in"><AuthBrand locale={locale} /><div className="auth-sport-scene" aria-hidden="true"><span>10</span></div><div><h1 id="splash-title" className="auth-splash-title">{t.splashTitle}</h1><p className="auth-splash-copy">{t.splashDescription}</p></div><AuthAction href={`/${locale}/login`}>{t.login}</AuthAction></div></section>;
  const title = mode === "login" ? t.loginTitle : mode === "register" ? t.registerTitle : mode === "forgot" ? t.forgotTitle : t.languageTitle;
  const description = mode === "login" ? t.loginDescription : mode === "register" ? t.registerDescription : mode === "forgot" ? t.forgotDescription : t.languageDescription;
  return <section className={`auth-entry auth-entry-${mode}`} aria-labelledby={`${mode}-title`}>
    <div className="auth-entry-glow" aria-hidden="true" />
    <div className="auth-entry-content reveal-in">
      <div className="auth-entry-topbar">
        <AuthBrand locale={locale} />
      </div>
      <div className="auth-login-card">
        <div className="auth-welcome">
          <h1 id={`${mode}-title`} className="auth-title">{title}</h1>
          <p>{description}</p>
        </div>
        {children}
        {mode === "login" && <div className="auth-register-entry">
          <span>{t.noAccount}</span>
          <AuthAction href={`/${locale}/register`}>{t.register}</AuthAction>
        </div>}
        {mode === "register" && <div className="auth-register-entry"><span>{t.haveAccount}</span><AuthAction href={`/${locale}/login`}>{t.login}</AuthAction></div>}
        {mode === "forgot" && <div className="auth-register-entry"><AuthAction href={`/${locale}/login`}>{t.backToLogin}</AuthAction></div>}
      </div>
      {mode !== "language" && <p className="auth-privacy-note">{t.authPrivacyNote}</p>}
    </div>
  </section>;
}
