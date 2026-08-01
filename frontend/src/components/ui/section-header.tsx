import React from "react";
import { cn } from "@/lib/cn";

export function SectionHeader({ title, description, actions, id, className }: { title: React.ReactNode; description?: React.ReactNode; actions?: React.ReactNode; id?: string; className?: string }) {
  return <header className={cn("flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between", className)}><div><h2 id={id} className="text-section-title">{title}</h2>{description && <p className="text-body-sm mt-1 text-[var(--text-muted)]">{description}</p>}</div>{actions && <div className="shrink-0">{actions}</div>}</header>;
}
