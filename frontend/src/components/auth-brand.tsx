import Link from "next/link";
import type { Locale } from "@/lib/copy";

export function AuthBrand({ locale }: { locale: Locale }) {
  return (
    <Link className="auth-brand focus-ring" href={`/${locale}`} aria-label="MAL3ABY">
      <span className="auth-brand-mark" aria-hidden="true">
        <span>M</span><i>3</i>
      </span>
      <span className="auth-brand-name">MAL<span>3</span>ABY</span>
      <span className="auth-brand-tagline" aria-hidden="true">BOOK <i /> PLAY <i /> ENJOY</span>
    </Link>
  );
}
