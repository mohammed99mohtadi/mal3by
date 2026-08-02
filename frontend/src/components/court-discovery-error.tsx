"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { courtDiscoveryCopy } from "@/lib/court-discovery";
import type { Locale } from "@/lib/copy";

export function CourtDiscoveryError({locale,kind}:{locale:Locale;kind:"network"|"invalid"|"service"|"unauthorized"}){const t=courtDiscoveryCopy[locale],router=useRouter();return <div className="reveal-in relative isolate mx-auto max-w-3xl overflow-hidden rounded-[var(--radius-xl)] border border-[var(--danger)]/25 bg-[radial-gradient(circle_at_50%_0%,rgba(239,68,68,.12),transparent_42%),var(--surface-1)] px-5 py-10 text-center shadow-[var(--shadow-lg)] sm:px-10 sm:py-14" role="alert"><div className="mx-auto grid size-16 place-items-center rounded-2xl border border-[var(--danger)]/25 bg-[var(--danger)]/10 text-3xl text-[var(--danger)] shadow-[0_0_32px_rgba(239,68,68,.1)]" aria-hidden="true">!</div><p className="eyebrow mt-6">{t.eyebrow}</p><h1 className="mt-2 text-3xl font-black sm:text-4xl">{t.errorTitle}</h1><p className="mx-auto mt-4 max-w-xl text-base leading-8 text-[var(--text-secondary)]">{t[kind]}</p><div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row"><Button size="lg" onClick={()=>router.refresh()}><span aria-hidden>↻</span>{t.retry}</Button><Link className="button-link button-link-secondary" href={`/${locale}`}>{t.home}</Link></div></div>}
