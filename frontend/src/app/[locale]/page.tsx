import { cookies } from "next/headers";
import { HomeDashboard } from "@/components/home/home-dashboard";
import { api } from "@/lib/api";
import type { Locale } from "@/lib/copy";
import type { Booking,Court,User } from "@/lib/types";

export default async function Home({params}:{params:Promise<{locale:string}>}) {
  const {locale}=await params,l=(locale==="en"?"en":"ar")as Locale,token=(await cookies()).get("mal3by_session")?.value;
  let courts:Court[]=[],user:User|undefined,bookings:Booking[]=[],courtsUnavailable=false,bookingsUnavailable=false;
  const courtsWork=api.courts(new URLSearchParams({is_active:"true",limit:"20"})).then(value=>{courts=value}).catch(()=>{courtsUnavailable=true});
  const accountWork=token?Promise.all([api.me(token).then(value=>{user=value}).catch(()=>undefined),api.bookings(token).then(value=>{bookings=value}).catch(()=>{bookingsUnavailable=true})]):Promise.resolve();
  await Promise.all([courtsWork,accountWork]);
  const upcoming=bookings.filter(b=>["pending","pending_payment","confirmed"].includes(b.status)).toSorted((a,b)=>Date.parse(a.start_time)-Date.parse(b.start_time));
  return <HomeDashboard locale={l} courts={courts} userName={user?.full_name} upcoming={upcoming} courtsUnavailable={courtsUnavailable} bookingsUnavailable={bookingsUnavailable}/>;
}
