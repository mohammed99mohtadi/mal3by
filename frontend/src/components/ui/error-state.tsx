import React, { useId } from "react";
import { Button } from "@/components/ui/button";
import { Surface } from "@/components/ui/surface";
import type { Locale } from "@/lib/copy";
import { stateCopy, type PageStateKind } from "@/lib/state-copy";

export function ErrorState({ locale, kind = "error", title, description, actionLabel, onAction }: { locale: Locale; kind?: PageStateKind; title?: string; description?: string; actionLabel?: string; onAction?: () => void }) {
  const fallback = stateCopy[locale][kind];
  const titleId = useId();
  return <Surface role={kind === "error" || kind === "offline" ? "alert" : "region"} aria-labelledby={titleId} className="flex min-h-56 flex-col items-center justify-center text-center" padding="lg">
    <h1 id={titleId} className="text-section-title">{title ?? fallback.title}</h1>
    <p className="text-body-sm mt-2 max-w-md text-[var(--text-muted)]">{description ?? fallback.description}</p>
    {actionLabel && onAction && <Button className="mt-5" onClick={onAction}>{actionLabel}</Button>}
  </Surface>;
}
