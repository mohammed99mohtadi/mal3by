import Image from "next/image";
import Link from "next/link";
import logo from "../../public/brand/mal3aby-logo.png";
import type { Locale } from "@/lib/copy";

export function BrandLogo({locale,compact=false}:{locale:string;compact?:boolean}) {
  const safe=(locale==="en"?"en":"ar")as Locale;
  return <Link aria-label={safe==="ar"?"MAL3ABY - الرئيسية":"MAL3ABY home"} className="brand-logo focus-ring" href={`/${safe}`}>
    <Image src={logo} alt="MAL3ABY" width={1536} height={1024} sizes={compact?"72px":"(max-width: 1023px) 108px, 132px"} className={compact?"brand-logo-image is-compact":"brand-logo-image"} preload/>
  </Link>;
}
