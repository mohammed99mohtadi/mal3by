import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { AuthForm } from "@/components/auth-form";
import { AuthShell } from "@/components/auth-shell";
import type { Locale } from "@/lib/copy";

export default async function Register({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params; const safe = (locale === "en" ? "en" : "ar") as Locale;
  if ((await cookies()).get("mal3by_session")) redirect(`/${safe}/profile`);
  return <AuthShell locale={safe} mode="register"><AuthForm locale={safe} mode="register" /></AuthShell>;
}
