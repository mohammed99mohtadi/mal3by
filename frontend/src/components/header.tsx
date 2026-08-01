import { cookies } from "next/headers";
import { api } from "@/lib/api";
import type { Locale } from "@/lib/copy";
import { HeaderNav } from "./header-nav";

export async function Header({ locale }: { locale: Locale }) {
  const token = (await cookies()).get("mal3by_session")?.value;
  let userName: string | undefined;
  if (token) { try { userName = (await api.me(token)).full_name; } catch { /* Cookie remains server-only; privileged links stay hidden. */ } }
  return <HeaderNav locale={locale} isLoggedIn={Boolean(token)} userName={userName} />;
}
