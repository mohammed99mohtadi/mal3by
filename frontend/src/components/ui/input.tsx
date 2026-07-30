import React from "react";
import { cn } from "@/lib/cn";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
  leadingSlot?: React.ReactNode;
  trailingSlot?: React.ReactNode;
  fullWidth?: boolean;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      hasError = false,
      leadingSlot,
      trailingSlot,
      fullWidth = false,
      className,
      disabled,
      type = "text",
      ...props
    },
    ref
  ) => {
    return (
      <div
        className={cn(
          "relative inline-flex items-center rounded-[var(--radius-md)] border bg-[var(--surface-1)] transition-colors duration-150 focus-within:border-[var(--brand)] focus-within:ring-2 focus-within:ring-[var(--brand)]/20",
          hasError
            ? "border-[var(--danger)] text-[var(--danger)] focus-within:border-[var(--danger)] focus-within:ring-[var(--danger)]/20"
            : "border-[var(--border-strong)] text-[var(--text-primary)]",
          disabled && "opacity-50 cursor-not-allowed bg-[var(--surface-2)]",
          fullWidth && "w-full"
        )}
      >
        {leadingSlot && (
          <span className="ps-3 flex items-center shrink-0 text-[var(--text-muted)]">
            {leadingSlot}
          </span>
        )}
        <input
          ref={ref}
          type={type}
          disabled={disabled}
          className={cn(
            "w-full min-h-[44px] bg-transparent text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] focus:outline-none disabled:cursor-not-allowed",
            leadingSlot ? "ps-2" : "ps-3.5",
            trailingSlot ? "pe-2" : "pe-3.5",
            className
          )}
          {...props}
        />
        {trailingSlot && (
          <span className="pe-3 flex items-center shrink-0 text-[var(--text-muted)]">
            {trailingSlot}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
