import { NextResponse } from "next/server";
export async function POST(req:Request){const url=new URL(req.url);const locale=url.searchParams.get("locale")==="en"?"en":"ar";const out=NextResponse.redirect(new URL(`/${locale}`,req.url),303);out.cookies.set("mal3by_session","",{httpOnly:true,path:"/",maxAge:0});return out}
