import React from "react";
import { cn } from "@/lib/cn";

export interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  label: string;
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
}

export const IconButton = React.forwardRef<HTMLButtonElement, IconButtonProps>(({ label, size = "md", isLoading = false, disabled, className, children, ...props }, ref) => {
  const sizes = { sm: "size-11", md: "size-11", lg: "size-12" };
  return <button ref={ref} type="button" aria-label={label} aria-busy={isLoading || undefined} disabled={disabled || isLoading} className={cn("focus-ring inline-grid shrink-0 place-items-center rounded-[var(--radius-md)] border border-[var(--border-strong)] bg-[var(--surface-1)] text-[var(--text-secondary)] transition-colors hover:border-[var(--brand)] hover:text-[var(--brand)] active:bg-[var(--surface-3)] disabled:pointer-events-none disabled:opacity-50", sizes[size], className)} {...props}>
    {isLoading ? <span className="size-4 animate-spin rounded-full border-2 border-current border-e-transparent" aria-hidden="true" /> : children}
  </button>;
});
IconButton.displayName = "IconButton";
