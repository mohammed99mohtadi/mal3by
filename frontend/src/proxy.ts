import { NextResponse, type NextRequest } from "next/server";

export function proxy(request: NextRequest) {
  const path = request.nextUrl.pathname;
  if (path === "/") { const url = request.nextUrl.clone(); url.pathname = "/ar"; return NextResponse.redirect(url); }
  if (!/^\/(ar|en)(\/|$)/.test(path)) { const url = request.nextUrl.clone(); url.pathname = `/ar${path}`; return NextResponse.redirect(url); }
  return NextResponse.next();
}

export const config = { matcher: ["/((?!api|_next|favicon.ico).*)"] };
