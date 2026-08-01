import { CourtCard } from "@/components/court-card";
import { Alert } from "@/components/ui/alert";
import { EmptyState } from "@/components/ui/empty-state";
import { PageHeader } from "@/components/ui/page-header";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import { bookingUx } from "@/lib/booking-ux";
import { copy,type Locale } from "@/lib/copy";
export default async function Courts({params}:{params:Promise<{locale:string}>}){const{locale}=await params,l=(locale==="en"?"en":"ar")as Locale,text=copy[l],ux=bookingUx[l];let courts;try{courts=await api.courts();}catch{return <section className="page-wrap"><PageHeader title={text.courts} description={text.courtExploreDescription}/><Alert tone="danger" message={text.courtLoadError} className="mt-6"/></section>}return <section className="page-wrap"><PageHeader eyebrow={text.courtExplore} title={text.courts} description={text.courtExploreDescription}/><p className="mt-4 text-sm font-semibold" role="status">{ux.resultCount(courts.length)}</p>{courts.length===0?<Surface className="mt-6"><EmptyState title={text.courtEmptyTitle} description={text.courtEmptyDescription}/></Surface>:<div className="mt-7 grid min-w-0 gap-4 sm:grid-cols-2 lg:grid-cols-3">{courts.map(court=><CourtCard key={court.id} court={court} locale={l}/>)}</div>}</section>}
