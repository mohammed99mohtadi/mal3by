"use client";

import Link from "next/link";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Drawer } from "@/components/ui/drawer";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { matchDiscoveryCopy, publicMatchQuery, type MatchFilters } from "@/lib/match-discovery";
import type { Locale } from "@/lib/copy";

function Fields({ locale, filters, id }: { locale: Locale; filters: MatchFilters; id: string }) {
  const t = matchDiscoveryCopy[locale];
  return <div className="grid gap-4">
    <Input id={`${id}-q`} name="q" defaultValue={filters.q} label={t.search} hint={t.searchHint} maxLength={80} />
    <Input id={`${id}-sport`} name="sport" defaultValue={filters.sport} label={t.sport} maxLength={100} />
    <label className="grid gap-1.5 text-sm font-bold" htmlFor={`${id}-skill`}>
      {t.skill}
      <Select id={`${id}-skill`} name="skill" defaultValue={filters.skill} fullWidth>
        <option value="">—</option>
        {Object.entries(t.skillLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </Select>
    </label>
    <Input id={`${id}-date`} type="date" name="date" defaultValue={filters.date} label={t.date} />
    <label className="grid gap-1.5 text-sm font-bold" htmlFor={`${id}-status`}>
      {t.status}
      <Select id={`${id}-status`} name="status" defaultValue={filters.status} fullWidth>
        <option value="">—</option>
        {Object.entries(t.statusLabels).map(([value, label]) => <option key={value} value={value}>{label}</option>)}
      </Select>
    </label>
    <label className="flex min-h-11 items-center gap-3 text-sm font-bold">
      <input className="size-5 accent-[var(--brand)]" type="checkbox" name="available" value="true" defaultChecked={filters.available} />
      {t.spots}
    </label>
    <label className="grid gap-1.5 text-sm font-bold" htmlFor={`${id}-sort`}>
      {t.sort}
      <Select id={`${id}-sort`} name="sort" defaultValue={filters.sort} fullWidth>
        <option value="start_time">{locale === "ar" ? "الأقرب" : "Soonest"}</option>
        <option value="newest">{locale === "ar" ? "الأحدث" : "Newest"}</option>
        <option value="oldest">{locale === "ar" ? "الأقدم" : "Oldest"}</option>
      </Select>
    </label>
    <div className="flex gap-2">
      <Button type="submit" fullWidth>{t.apply}</Button>
      <Link className="focus-ring flex min-h-11 items-center justify-center rounded-[var(--radius-md)] border border-[var(--border-strong)] px-4 text-sm font-bold" href={`/${locale}/matches`}>{t.reset}</Link>
    </div>
  </div>;
}

export function MatchDiscoveryFilters({ locale, filters }: { locale: Locale; filters: MatchFilters }) {
  const t = matchDiscoveryCopy[locale];
  const [open, setOpen] = useState(false);
  const active = [
    filters.q && ["q", filters.q],
    filters.sport && ["sport", filters.sport],
    filters.skill && ["skill", t.skillLabels[filters.skill]],
    filters.date && ["date", filters.date],
    filters.status && ["status", t.statusLabels[filters.status]],
    filters.available && ["available", t.spots],
  ].filter(Boolean) as [string, string][];

  return <>
    <div className="lg:hidden">
      <Button type="button" variant="outline" fullWidth onClick={() => setOpen(true)}>{t.openFilters}{active.length ? ` (${active.length})` : ""}</Button>
    </div>
    <aside className="hidden lg:row-span-2 lg:block">
      <div className="sticky top-24 rounded-[var(--radius-lg)] border border-[var(--border-strong)] bg-[var(--surface-1)] p-5">
        <h2 className="mb-5 text-xl font-black">{t.filters}</h2>
        <form action={`/${locale}/matches`} method="get"><Fields locale={locale} filters={filters} id="desktop" /></form>
      </div>
    </aside>
    <Drawer open={open} onClose={() => setOpen(false)} title={t.filters}>
      <form action={`/${locale}/matches`} method="get"><Fields locale={locale} filters={filters} id="mobile" /></form>
    </Drawer>
    {active.length > 0 && <div className="col-span-full flex flex-wrap gap-2 lg:col-start-2 lg:col-end-3" aria-label={locale === "ar" ? "عوامل التصفية النشطة" : "Active filters"}>
      {active.map(([key, label]) => {
        const next = { ...filters, [key]: key === "available" ? false : "", page: 1 } as MatchFilters;
        return <Link key={key} className="focus-ring rounded-full border border-[var(--brand)]/30 bg-[var(--brand)]/10 px-3 py-1.5 text-xs font-bold text-[var(--brand)]" href={`/${locale}/matches?${publicMatchQuery(next)}`} aria-label={`${locale === "ar" ? "إزالة" : "Remove"} ${label}`}>{label} ×</Link>;
      })}
    </div>}
  </>;
}
