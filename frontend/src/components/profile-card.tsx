import Link from "next/link";
import { BidiText } from "@/components/ui/bidi";
import { Button } from "@/components/ui/button";
import { Surface } from "@/components/ui/surface";
import { copy, type Locale } from "@/lib/copy";
import type { User } from "@/lib/types";

export function ProfileCard({ locale, user }: { locale: Locale; user: User }) {
  const t = copy[locale]; const roles: Record<string,string> = { player: t.rolePlayer, owner: t.roleOwner, admin: t.roleAdmin };
  return <Surface className="mt-7" padding="lg"><div className="flex flex-col gap-5 sm:flex-row sm:items-center"><div aria-hidden className="grid size-20 shrink-0 place-items-center rounded-full bg-[var(--brand)] text-3xl font-black text-[var(--brand-foreground)]">{user.full_name.trim().slice(0,1).toUpperCase()}</div><div className="min-w-0"><h2 className="text-section-title bidi-auto" dir="auto">{user.full_name}</h2><p className="mt-1 text-[var(--text-muted)]"><BidiText kind="email" value={user.email} /></p></div></div>
    <dl className="mt-8 grid gap-5 border-t border-[var(--border-strong)] pt-6 sm:grid-cols-2"><div><dt className="text-label text-[var(--text-muted)]">{t.accountRole}</dt><dd className="mt-1 font-bold">{roles[user.role] ?? t.rolePlayer}</dd></div><div><dt className="text-label text-[var(--text-muted)]">{t.accountStatus}</dt><dd className="mt-1 font-bold">{user.is_active ? t.accountActive : t.accountInactive}</dd></div>{user.phone_number && <div><dt className="text-label text-[var(--text-muted)]">{t.phoneLabel}</dt><dd className="mt-1"><BidiText kind="phone" value={user.phone_number} /></dd></div>}{user.created_at && <div><dt className="text-label text-[var(--text-muted)]">{t.memberSince}</dt><dd className="mt-1"><time dateTime={user.created_at}>{new Intl.DateTimeFormat(locale,{dateStyle:"long"}).format(new Date(user.created_at))}</time></dd></div>}</dl>
    <div className="mt-8 flex flex-col gap-3 sm:flex-row"><Link className="focus-ring inline-flex min-h-11 items-center justify-center rounded-[var(--radius-md)] bg-[var(--brand)] px-4 font-bold text-[var(--brand-foreground)]" href={`/${locale}/bookings`}>{t.bookings}</Link><form action={`/api/auth/logout?locale=${locale}`} method="post"><Button type="submit" variant="outline" fullWidth>{t.logout}</Button></form></div>
  </Surface>;
}
