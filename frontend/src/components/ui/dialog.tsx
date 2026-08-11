"use client";

import React, { useEffect, useId, useRef } from "react";
import { cn } from "@/lib/cn";

const focusable = 'button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function Dialog({ open, onClose, title, description, children, initialFocusRef, variant = "dialog", closeLabel = "Close" }: { open: boolean; onClose: () => void; title: React.ReactNode; description?: React.ReactNode; children: React.ReactNode; initialFocusRef?: React.RefObject<HTMLElement | null>; variant?: "dialog" | "drawer"; closeLabel?: string }) {
  const panelRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);
  const titleId = useId(); const descriptionId = useId();
  useEffect(() => {
    if (!open) return;
    triggerRef.current = document.activeElement as HTMLElement;
    const panel = panelRef.current;
    (initialFocusRef?.current ?? panel?.querySelector<HTMLElement>(focusable) ?? panel)?.focus();
    function keydown(event: KeyboardEvent) {
      if (event.key === "Escape") { event.preventDefault(); onClose(); return; }
      if (event.key !== "Tab" || !panel) return;
      const items = Array.from(panel.querySelectorAll<HTMLElement>(focusable));
      if (!items.length) { event.preventDefault(); panel.focus(); return; }
      const first = items[0]; const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    document.addEventListener("keydown", keydown);
    return () => { document.removeEventListener("keydown", keydown); triggerRef.current?.focus(); };
  }, [open, onClose, initialFocusRef]);
  if (!open) return null;
  return <div className={cn("fixed inset-0 z-50 flex bg-[var(--overlay)] p-4", variant === "drawer" ? "items-end justify-center sm:items-center" : "items-center justify-center")} onMouseDown={(event) => { if (event.target === event.currentTarget) onClose(); }}>
    <div ref={panelRef} role="dialog" aria-modal="true" aria-labelledby={titleId} aria-describedby={description ? descriptionId : undefined} tabIndex={-1} className={cn("max-h-[min(90vh,48rem)] w-full overflow-y-auto border border-[var(--border-strong)] bg-[var(--surface-elevated)] p-5 shadow-[var(--shadow-lg)] focus:outline-none", variant === "drawer" ? "mobile-filter-sheet rounded-t-[var(--radius-xl)] sm:max-w-lg sm:rounded-[var(--radius-xl)]" : "max-w-lg rounded-[var(--radius-xl)]")}>
      <div className="flex items-center justify-between gap-3"><h2 id={titleId} className="text-section-title">{title}</h2>{variant === "drawer" && <button type="button" onClick={onClose} aria-label={closeLabel} className="focus-ring grid min-h-11 min-w-11 place-items-center rounded-[var(--radius-md)] border border-[var(--border-strong)] text-xl text-[var(--text-muted)]">×</button>}</div>{description && <p id={descriptionId} className="text-body-sm mt-2 text-[var(--text-muted)]">{description}</p>}<div className="mt-4">{children}</div>
    </div>
  </div>;
}
