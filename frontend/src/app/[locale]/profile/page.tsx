import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { api } from "@/lib/api";
import { ApiError, type User } from "@/lib/types";
import { PageHeader } from "@/components/ui/page-header";
import { ProfileError } from "@/components/profile-error";
import { ProfileCard } from "@/components/profile-card";
import { copy, type Locale } from "@/lib/copy";

export default async function Profile({ params }: { params: Promise<{ locale: string }> }) {
  const { locale } = await params; const safe = (locale === "en" ? "en" : "ar") as Locale; const t = copy[safe]; const token = (await cookies()).get("mal3by_session")?.value;
  if (!token) redirect(`/${safe}/login?returnTo=${encodeURIComponent(`/${safe}/profile`)}`);
  let user: User; try { user = await api.me(token); } catch (error) { if (error instanceof ApiError && error.status === 401) redirect(`/${safe}/login?returnTo=${encodeURIComponent(`/${safe}/profile`)}`); return <section className="page-wrap max-w-3xl"><ProfileError locale={safe} /></section>; }
  return <section className="page-wrap max-w-3xl py-8 sm:py-12"><PageHeader eyebrow={t.profileEyebrow} title={t.profileTitle} description={t.profileDescription} />
    <ProfileCard locale={safe} user={user} />
  </section>;
}
