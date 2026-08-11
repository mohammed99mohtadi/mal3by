import Link from "next/link";
import { courtDiscoveryCopy } from "@/lib/court-discovery";
import type { Locale } from "@/lib/copy";

export function CourtDiscoveryHero({locale,count,query=""}:{locale:Locale;count:number;query?:string}) {
  const t=courtDiscoveryCopy[locale],ar=locale==="ar";
  return <header className="discovery-heading">
    <div className="flex items-end justify-between gap-4">
      <div><p className="eyebrow">{t.eyebrow}</p><h1 className="mt-1 text-3xl font-black">{query?(ar?"نتائج البحث":"Search results"):t.title}</h1></div>
      <Link className="discovery-icon-link focus-ring" href={`/${locale}/courts/map`} aria-label={ar?"عرض الخريطة":"View map"}>⌖</Link>
    </div>
    <form role="search" action={`/${locale}/courts`} className="discovery-search mt-5">
      <label className="sr-only" htmlFor={`court-search-${locale}`}>{t.search}</label>
      <span aria-hidden="true">⌕</span><input id={`court-search-${locale}`} name="search" defaultValue={query} placeholder={ar?"ابحث عن ملعب أو منطقة…":"Search courts or areas…"} maxLength={100} autoComplete="off"/>
      <button type="submit" aria-label={ar?"بحث":"Search"}>→</button>
    </form>
    <div className="mt-4 flex items-center justify-between gap-3 text-sm"><p className="text-[var(--text-muted)]" role="status" aria-live="polite"><bdi>{t.results(count)}</bdi></p>{query&&<Link className="font-bold text-[var(--brand)]" href={`/${locale}/courts`}>{t.reset}</Link>}</div>
  </header>;
}
