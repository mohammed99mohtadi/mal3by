import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AuthForm } from "@/components/auth-form";
import { AuthShell } from "@/components/auth-shell";
import type { Locale } from "@/lib/copy";
import { safeReturnPath } from "@/lib/redirect";

export default async function Login({ params, searchParams }: { params: Promise<{ locale: string }>; searchParams: Promise<{ returnTo?: string }> }) {
  const { locale } = await params; const safe = (locale === "en" ? "en" : "ar") as Locale; const { returnTo } = await searchParams;
  if ((await cookies()).get("mal3by_session")) redirect(`/${safe}/language?returnTo=${encodeURIComponent(safeReturnPath(returnTo ?? null, safe))}`);
  return <AuthShell locale={safe} mode="login"><AuthForm locale={safe} mode="login" returnTo={returnTo} /></AuthShell>;
}
