import React from "react";
import { cn } from "@/lib/cn";

export function MobileActionBar({ children, className }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("fixed inset-x-0 bottom-[calc(var(--mobile-nav-height)+var(--safe-bottom))] z-20 flex gap-2 border-t border-[var(--border-strong)] bg-[var(--surface-1)]/95 p-3 backdrop-blur md:static md:border-0 md:bg-transparent md:p-0", className)}>{children}</div>;
}
