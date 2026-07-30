import React from "react";
import { cn } from "@/lib/cn";

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  hasError?: boolean;
  fullWidth?: boolean;
}

export const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  (
    {
      hasError = false,
      fullWidth = false,
      className,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    return (
      <div className={cn("relative inline-flex items-center", fullWidth && "w-full")}>
        <select
          ref={ref}
          disabled={disabled}
          className={cn(
            "w-full min-h-[44px] rounded-[var(--radius-md)] border bg-[var(--surface-1)] text-sm text-[var(--text-primary)] transition-colors duration-150 ps-3.5 pe-10 py-2.5 appearance-none focus-ring disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-[var(--surface-2)]",
            hasError
              ? "border-[var(--danger)] text-[var(--danger)]"
              : "border-[var(--border-strong)]",
            className
          )}
          {...props}
        >
          {children}
        </select>
        <span className="pointer-events-none absolute end-3 top-1/2 -translate-y-1/2 text-[var(--text-muted)]">
          <svg className="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 9l-7 7-7-7" />
          </svg>
        </span>
      </div>
    );
  }
);

Select.displayName = "Select";
