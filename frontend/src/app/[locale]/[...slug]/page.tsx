import { cookies } from "next/headers";
import { notFound, redirect } from "next/navigation";
import { DashboardShell } from "@/components/dashboard-shell";
import { LegalPageLayout } from "@/components/legal-page-layout";
import { LocaleSwitcher } from "@/components/locale-switcher";
import Link from "next/link";
import { ComingSoonState, DataTableShell, FeatureStatusBanner, MetricEmptyState, PaymentStatusCard, ProductPageHeader } from "@/components/product-foundation";
import { Alert } from "@/components/ui/alert";
import { Surface } from "@/components/ui/surface";
import { api } from "@/lib/api";
import type { Locale } from "@/lib/copy";
import { findProductRoute } from "@/lib/product-routes";
import { stateCopy } from "@/lib/state-copy";
import type { OwnerDashboard } from "@/lib/types";

export default async function ProductFoundation({ params }: { params: Promise<{ locale: string; slug: string[] }> }) {
  const { locale, slug } = await params; const l=(locale==="en"?"en":"ar") as Locale, path=`/${slug.join("/")}`, route=findProductRoute(path);
  if (!route || route.classification === "DEFERRED") notFound();
  const token=(await cookies()).get("mal3by_session")?.value;
  if(route.auth&&!token) redirect(`/${l}/login?returnTo=${encodeURIComponent(`/${l}${path}`)}`);
  let user;
  if(token&&route.role){try{user=await api.me(token)}catch{redirect(`/${l}/login?returnTo=${encodeURIComponent(`/${l}${path}`)}`)}}
  if(route.role==="owner"&&user?.role!=="owner"&&user?.role!=="admin"&&!user?.is_admin)return <section className="page-wrap"><Alert tone="danger" message={stateCopy[l].forbidden.description}/></section>;
  if(route.role==="admin"&&user?.role!=="admin"&&!user?.is_admin)return <section className="page-wrap"><Alert tone="danger" message={stateCopy[l].forbidden.description}/></section>;
  if(route.area==="legal"&&(path==="/privacy"||path==="/terms"))return <LegalPageLayout locale={l} title={route.title[l]}/>;
  let ownerData:OwnerDashboard|null=null, ownerFailed=false;
  if(path==="/owner"){try{ownerData=await api.ownerDashboard(token!)}catch{ownerFailed=true}}
  let content:React.ReactNode=<ComingSoonState route={route} locale={l}/>;
  if(path==="/owner")content=ownerFailed?<Alert tone="danger" message={l==="ar"?"تعذر تحميل ملخص المالك.":"Could not load owner summary."}/>:ownerData&&<div className="grid gap-4 sm:grid-cols-3">{[[l==="ar"?"إجمالي الملاعب":"Total courts",ownerData.total_courts],[l==="ar"?"الملاعب النشطة":"Active courts",ownerData.active_courts],[l==="ar"?"غير النشطة":"Inactive courts",ownerData.inactive_courts]].map(([label,value])=><Surface key={String(label)}><p className="text-sm text-[var(--text-muted)]">{label}</p><p className="mt-2 text-3xl font-black"><bdi>{value}</bdi></p></Surface>)}</div>;
  else if(route.area==="owner"||route.area==="admin")content=route.classification==="SHELL"?<MetricEmptyState locale={l}/>:<DataTableShell locale={l} title={route.title[l]}/>;
  else if(route.area==="payments")content=<PaymentStatusCard locale={l}/>;
  else if(path==="/settings")content=<Surface><h2 className="text-xl font-black">{l==="ar"?"اللغة":"Language"}</h2><div className="mt-4"><LocaleSwitcher locale={l}/></div><Link className="focus-ring mt-6 inline-block font-bold text-[var(--brand)]" href={`/${l}/settings/security`}>{l==="ar"?"إعدادات الأمان":"Security settings"}</Link></Surface>;
  const page=<><FeatureStatusBanner classification={route.classification} locale={l}/><ProductPageHeader title={route.title[l]} description={route.description[l]}/><div className="mt-7">{content}</div></>;
  return route.area==="owner"||route.area==="admin"?<DashboardShell locale={l} kind={route.area} current={`/${l}${path}`}>{page}</DashboardShell>:<section className="page-wrap">{page}</section>;
}
