import { cn } from "@/lib/cn";

export function Divider({ orientation = "horizontal", className }: { orientation?: "horizontal" | "vertical"; className?: string }) {
  return <div role="separator" aria-orientation={orientation} className={cn("shrink-0 bg-[var(--border-strong)]", orientation === "horizontal" ? "h-px w-full" : "h-full w-px", className)} />;
}
