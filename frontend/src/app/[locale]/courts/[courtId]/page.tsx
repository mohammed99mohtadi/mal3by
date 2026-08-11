import Image from "next/image";
import Link from "next/link";
import { Availability } from "@/components/availability";
import { Alert } from "@/components/ui/alert";
import { StatusBadge } from "@/components/ui/status-badge";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import { bookingUx,formatMoney } from "@/lib/booking-ux";
import { copy,type Locale } from "@/lib/copy";
import { ApiError,type RatingSummary } from "@/lib/types";

export default async function CourtDetail({params}:{params:Promise<{locale:string;courtId:string}>}) {
  const {locale,courtId}=await params,l=(locale==="en"?"en":"ar")as Locale,text=copy[l],ux=bookingUx[l],ar=l==="ar";
  let court;try{court=await api.court(courtId)}catch(error){return <section className="page-wrap py-8"><Link className="focus-ring text-sm font-bold text-[var(--brand)]" href={`/${l}/courts`}>{text.back}</Link><h1 className="mt-5 text-3xl font-black">{text.courtDetails}</h1><Alert tone="danger" message={error instanceof ApiError&&error.status===404?text.courtNotFound:ux.serviceError} className="mt-6"/></section>}
  let rating:RatingSummary|undefined;try{rating=await api.summary(courtId)}catch{/* Optional review data must not block booking. */}
  const name=court[ar?"name_ar":"name_en"],description=court[ar?"description_ar":"description_en"];
  return <section className="venue-detail page-wrap pb-28 pt-4 sm:pt-7">
    <Link className="discovery-icon-link focus-ring" href={`/${l}/courts`} aria-label={text.back}>←</Link>
    <div className="venue-detail-grid mt-4">
      <article className="min-w-0 space-y-4">
        <div className="venue-hero">{court.image_url?<Image src={court.image_url} alt="" fill sizes="(max-width:1024px) 100vw,65vw" className="object-cover" unoptimized/>:<div className="venue-image-fallback" aria-label={ar?"صورة الملعب غير متاحة":"Court image unavailable"}><span aria-hidden>⌂</span><small>{ar?"الصورة غير متاحة":"Image unavailable"}</small></div>}<span className="venue-photo-count" aria-hidden>{court.image_url?"1/1":"0/0"}</span></div>
        <Surface padding="lg"><div className="flex flex-wrap items-center justify-between gap-3"><StatusBadge status={court.is_active?"success":"danger"}>{court.is_active?text.courtOpen:text.courtUnavailable}</StatusBadge>{rating&&rating.total_reviews>0&&<p className="text-sm font-bold"><span aria-hidden className="text-[var(--warning)]">★</span> <bdi>{rating.average_rating} ({rating.total_reviews})</bdi></p>}</div><h1 className="mt-4 break-words text-3xl font-black" dir="auto">{name}</h1><p className="mt-2 text-sm text-[var(--text-muted)]" dir="auto">{court.sport?.[ar?"name_ar":"name_en"]} · {court.area}</p>
          <dl className="venue-meta"><div><dt>{ux.location}</dt><dd dir="auto">{court.area}{court.address?` · ${court.address}`:""}</dd></div><div><dt>{ar?"السعة":"Capacity"}</dt><dd><bdi>{court.capacity}</bdi> {ar?"لاعب":"players"}</dd></div><div><dt>{ux.priceFrom}</dt><dd><bdi>{formatMoney(l,court.price_per_hour,court.currency)}</bdi> {ux.perHour}</dd></div></dl>
          {description?<section className="mt-6 border-t border-[var(--border-strong)] pt-5" aria-labelledby="court-description"><h2 id="court-description" className="text-lg font-black">{ar?"عن الملعب":"About this court"}</h2><p className="mt-2 break-words leading-7 text-[var(--text-secondary)]" dir="auto">{description}</p></section>:<p className="mt-6 border-t border-[var(--border-strong)] pt-5 text-sm text-[var(--text-muted)]">{ar?"لا تتوفر تفاصيل إضافية لهذا الملعب حالياً.":"No additional venue details are available yet."}</p>}
        </Surface>
      </article>
      <aside className="min-w-0 h-fit lg:sticky lg:top-24"><Surface padding="md"><h2 className="text-xl font-black">{text.courtAvailability}</h2><p className="mt-2 text-sm text-[var(--text-muted)]">{text.courtAvailabilityDescription}</p><Availability courtId={courtId} locale={l} inactive={!court.is_active}/></Surface></aside>
    </div>
  </section>;
}
