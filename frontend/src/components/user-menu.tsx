"use client";

import Link from "next/link";
import { useEffect, useId, useRef, useState } from "react";
import { copy, type Locale } from "@/lib/copy";

export function UserMenu({ locale, name }: { locale: Locale; name?: string }) {
  const t = copy[locale]; const [open, setOpen] = useState(false); const rootRef = useRef<HTMLDivElement>(null); const triggerRef = useRef<HTMLButtonElement>(null); const menuId = useId();
  const initial = name?.trim().slice(0, 1).toUpperCase() || t.userFallback;
  useEffect(() => {
    if (!open) return;
    function closeOutside(event: PointerEvent) { if (!rootRef.current?.contains(event.target as Node)) setOpen(false); }
    function keydown(event: KeyboardEvent) {
      if (event.key === "Escape") { setOpen(false); triggerRef.current?.focus(); }
      if (event.key === "ArrowDown") { event.preventDefault(); rootRef.current?.querySelector<HTMLAnchorElement>("[role=menuitem]")?.focus(); }
    }
    document.addEventListener("pointerdown", closeOutside); document.addEventListener("keydown", keydown);
    return () => { document.removeEventListener("pointerdown", closeOutside); document.removeEventListener("keydown", keydown); };
  }, [open]);
  return <div ref={rootRef} className="relative">
    <button ref={triggerRef} type="button" aria-label={t.userMenuOpen} aria-expanded={open} aria-controls={menuId} onClick={() => setOpen((value) => !value)} className="focus-ring grid size-11 place-items-center rounded-full border border-[var(--border-strong)] bg-[var(--surface-2)] font-black text-[var(--brand)] hover:border-[var(--brand)]">{initial}</button>
    {open && <div id={menuId} role="menu" aria-label={t.userMenuLabel} className="absolute end-0 top-[calc(100%+.5rem)] z-40 min-w-52 rounded-[var(--radius-lg)] border border-[var(--border-strong)] bg-[var(--surface-elevated)] p-2 shadow-[var(--shadow-lg)]">
      {name && <p className="truncate px-3 py-2 text-sm font-bold" dir="auto">{name}</p>}
      <Link role="menuitem" className="focus-ring block min-h-11 rounded-[var(--radius-md)] px-3 py-2.5 text-sm hover:bg-[var(--surface-3)]" href={`/${locale}/profile`} onClick={() => setOpen(false)}>{t.profile}</Link>
      <Link role="menuitem" className="focus-ring block min-h-11 rounded-[var(--radius-md)] px-3 py-2.5 text-sm hover:bg-[var(--surface-3)]" href={`/${locale}/bookings`} onClick={() => setOpen(false)}>{t.bookings}</Link>
      <form action={`/api/auth/logout?locale=${locale}`} method="post"><button role="menuitem" className="focus-ring min-h-11 w-full rounded-[var(--radius-md)] px-3 py-2.5 text-start text-sm text-[var(--danger)] hover:bg-[var(--surface-3)]" type="submit">{t.logout}</button></form>
    </div>}
  </div>;
}
