"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { courtDiscoveryCopy } from "@/lib/court-discovery";
import type { Locale } from "@/lib/copy";
export function CourtDiscoveryError({locale,kind}:{locale:Locale;kind:"network"|"invalid"|"service"|"unauthorized"}){const t=courtDiscoveryCopy[locale],router=useRouter();return <div><h1 className="text-3xl font-black">{t.errorTitle}</h1><Alert className="mt-4" tone="danger" message={t[kind]}/><div className="mt-5 flex flex-col gap-2 sm:flex-row"><Button onClick={()=>router.refresh()}>{t.retry}</Button><Link className="focus-ring flex min-h-11 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border-strong)] px-4 font-bold" href={`/${locale}`}>{t.home}</Link></div></div>}
