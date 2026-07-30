import React from "react";
import { cn } from "@/lib/cn";

export interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  hasError?: boolean;
  fullWidth?: boolean;
}

export const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  (
    {
      hasError = false,
      fullWidth = false,
      className,
      disabled,
      rows = 4,
      ...props
    },
    ref
  ) => {
    return (
      <textarea
        ref={ref}
        rows={rows}
        disabled={disabled}
        className={cn(
          "rounded-[var(--radius-md)] border bg-[var(--surface-1)] text-sm text-[var(--text-primary)] placeholder-[var(--text-muted)] p-3.5 transition-colors duration-150 focus-ring disabled:opacity-50 disabled:cursor-not-allowed disabled:bg-[var(--surface-2)]",
          hasError
            ? "border-[var(--danger)] text-[var(--danger)]"
            : "border-[var(--border-strong)]",
          fullWidth && "w-full",
          className
        )}
        {...props}
      />
    );
  }
);

Textarea.displayName = "Textarea";
