import Link from "next/link";
import { CourtMap } from "@/components/court-map";
import { CourtDiscoveryError } from "@/components/court-discovery-error";
import { api } from "@/lib/api";
import type { Locale } from "@/lib/copy";

export default async function MapPage({params,searchParams}:{params:Promise<{locale:string}>;searchParams:Promise<{selected?:string}>}) {
  const {locale}=await params,l=(locale==="en"?"en":"ar")as Locale,ar=l==="ar",{selected}=await searchParams;
  let courts;try{courts=await api.courts(new URLSearchParams({is_active:"true",limit:"100"}))}catch{return <section className="page-wrap py-8"><CourtDiscoveryError locale={l} kind="network"/></section>}
  return <section className="discovery-map-page">
    <header className="discovery-map-header"><Link className="discovery-icon-link focus-ring" href={`/${l}/courts`} aria-label={ar?"العودة إلى الاستكشاف":"Back to discover"}>←</Link><div><p className="eyebrow">{ar?"استكشاف":"Discover"}</p><h1 className="text-xl font-black">{ar?"الملاعب على الخريطة":"Courts map"}</h1></div><Link className="discovery-icon-link focus-ring" href={`/${l}/courts`} aria-label={ar?"بحث وفلاتر":"Search and filters"}>⌕</Link></header>
    <CourtMap courts={courts} locale={l} selectedId={selected}/>
  </section>;
}
