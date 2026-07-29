import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { api } from "@/lib/api";
import type { User } from "@/lib/types";

export default async function Profile({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params;
  const token = (await cookies()).get("mal3by_session")?.value;
  if (!token) redirect(`/${locale}/login`);
  let user: User;
  try { user = await api.me(token); } catch { redirect(`/${locale}/login`); }
  return <section className="mx-auto max-w-xl p-8"><h1 className="text-3xl font-black">{user.full_name}</h1><p className="mt-3">{user.email}</p><p className="text-sm text-emerald-950/65">{user.role}</p></section>;
}
