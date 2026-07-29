export function safeReturnPath(value: string | null, locale: "ar" | "en"): string {
  if (!value || !value.startsWith(`/${locale}/`) || value.startsWith("//") || value.includes("://")) return `/${locale}/profile`;
  return value;
}
