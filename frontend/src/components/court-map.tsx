import Link from "next/link";
import { EmptyState } from "@/components/ui/empty-state";
import { Surface } from "@/components/ui/surface";
import { formatMoney } from "@/lib/booking-ux";
import type { Locale } from "@/lib/copy";
import type { Court } from "@/lib/types";

export function CourtMap({courts,locale,selectedId}:{courts:Court[];locale:Locale;selectedId?:string}) {
  const ar=locale==="ar",mapped=courts.filter(c=>Number.isFinite(c.latitude)&&Number.isFinite(c.longitude));
  const selected=mapped.find(c=>String(c.id)===selectedId)??mapped[0];
  const latitudes=mapped.map(c=>c.latitude as number),longitudes=mapped.map(c=>c.longitude as number);
  const bounds={minLat:Math.min(...latitudes),maxLat:Math.max(...latitudes),minLng:Math.min(...longitudes),maxLng:Math.max(...longitudes)};
  const position=(court:Court)=>({left:`${12+76*(((court.longitude as number)-bounds.minLng)/(bounds.maxLng-bounds.minLng||1))}%`,top:`${12+68*(1-((court.latitude as number)-bounds.minLat)/(bounds.maxLat-bounds.minLat||1))}%`});
  return <div className="court-map-layout">
    <div className="court-map-canvas" aria-hidden="true">
      <div className="court-map-grid"/>
      {mapped.map(court=><Link tabIndex={-1} key={court.id} style={position(court)} className={`court-map-marker ${court.id===selected?.id?"is-selected":""}`} href={`/${locale}/courts/map?selected=${court.id}`}><bdi>{formatMoney(locale,court.price_per_hour,court.currency)}</bdi></Link>)}
    </div>
    <div className="court-map-summary">
      {mapped.length===0?<Surface className="border-dashed"><EmptyState title={ar?"لا تتوفر مواقع موثوقة":"No verified locations available"} description={ar?"الملاعب الحالية لا تحتوي على إحداثيات. يمكنك استعراضها في القائمة دون استخدام الخريطة.":"Current courts do not include coordinates. Browse them in the accessible list instead."}/><div className="pb-5 text-center"><Link className="button-link" href={`/${locale}/courts`}>{ar?"عرض الملاعب":"Browse courts"}</Link></div></Surface>:selected&&<Surface as="article" className="p-4"><p className="text-xs font-bold text-[var(--brand)]">{selected.sport?.[ar?"name_ar":"name_en"]}</p><h2 className="mt-2 text-xl font-black" dir="auto">{selected[ar?"name_ar":"name_en"]}</h2><p className="mt-1 text-sm text-[var(--text-muted)]" dir="auto">{selected.area}</p><div className="mt-4 flex items-center justify-between gap-3"><strong><bdi>{formatMoney(locale,selected.price_per_hour,selected.currency)}</bdi></strong><Link className="button-link" href={`/${locale}/courts/${selected.id}`}>{ar?"عرض التفاصيل":"View details"}</Link></div></Surface>}
      <section className="sr-only" aria-labelledby="map-alternative"><h2 id="map-alternative">{ar?"قائمة الملاعب على الخريطة":"Courts shown on map"}</h2><ul>{mapped.map(c=><li key={c.id}><Link href={`/${locale}/courts/${c.id}`}>{c[ar?"name_ar":"name_en"]} — {c.area}</Link></li>)}</ul></section>
    </div>
  </div>;
}
