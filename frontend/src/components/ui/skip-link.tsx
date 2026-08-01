export function SkipLink({ locale }: { locale: string }) {
  return <a className="skip-link focus-ring" href="#main-content">{locale === "ar" ? "انتقل إلى المحتوى" : "Skip to content"}</a>;
}
