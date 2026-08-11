import Image from "next/image";
import Link from "next/link";
import mal3abyLogo from "../../public/brand/mal3aby-logo.png";
import type { Locale } from "@/lib/copy";

export function AuthBrand({ locale }: { locale: Locale }) {
  return (
    <Link className="auth-brand focus-ring" href={`/${locale}`} aria-label="MAL3ABY">
      <Image
        className="auth-brand-image"
        src={mal3abyLogo}
        alt="MAL3ABY"
        width={1536}
        height={1024}
        sizes="(max-width: 639px) 176px, 200px"
        preload
      />
    </Link>
  );
}
