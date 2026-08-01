import React from "react";
import { cn } from "@/lib/cn";

export function PageHeader({ title, description, eyebrow, actions, className }: { title: React.ReactNode; description?: React.ReactNode; eyebrow?: React.ReactNode; actions?: React.ReactNode; className?: string }) {
  return <header className={cn("flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between", className)}>
    <div className="min-w-0">{eyebrow && <p className="eyebrow">{eyebrow}</p>}<h1 className="text-page-title mt-1">{title}</h1>{description && <p className="text-body mt-2 max-w-2xl text-[var(--text-muted)]">{description}</p>}</div>
    {actions && <div className="flex shrink-0 flex-wrap gap-2">{actions}</div>}
  </header>;
}
