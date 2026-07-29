import type { Metadata } from "next";
import "../globals.css";
import { Header } from "@/components/header";
export const metadata:Metadata={title:"Mal3by | Sports courts",description:"Discover sports courts in Kuwait"};
export default async function LocaleLayout({children,params}:{children:React.ReactNode;params:Promise<{locale:string}>}){const {locale}=await params;const safe=locale==="en"?"en":"ar";return <html lang={safe} dir={safe==="ar"?"rtl":"ltr"}><body><Header locale={safe}/><main>{children}</main><footer className="border-t border-emerald-950/10 p-8 text-center text-sm text-emerald-950/70">Mal3by · Kuwait sports booking</footer></body></html>}
