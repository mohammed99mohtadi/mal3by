import { AuthShell } from "@/components/auth-shell"; import type { Locale } from "@/lib/copy";
export default async function Splash({params}:{params:Promise<{locale:string}>}){const{locale}=await params;const safe=(locale==="en"?"en":"ar")as Locale;return <AuthShell locale={safe} mode="splash"><span/></AuthShell>}
