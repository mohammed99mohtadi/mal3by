"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
export function LocaleSwitcher({ locale }: { locale: string }) { const path = usePathname(); const other = locale === "ar" ? "en" : "ar"; const rest = path.replace(/^\/(ar|en)/, "") || "/"; return <Link className="focus-ring" href={`/${other}${rest}`}>{other.toUpperCase()}</Link>; }
