import React from "react";
import { cn } from "@/lib/cn";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  hasError?: boolean;
  leadingSlot?: React.ReactNode;
  trailingSlot?: React.ReactNode;
  fullWidth?: boolean;
  label?: React.ReactNode;
  error?: React.ReactNode;
  hint?: React.ReactNode;
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
      label,
      error,
      hint,
      id,
      "aria-describedby": describedBy,
      ...props
    },
    ref
  ) => {
    const generatedId = React.useId();
    const inputId = id ?? generatedId;
    const errorId = error ? `${inputId}-error` : undefined;
    const hintId = hint ? `${inputId}-hint` : undefined;
    const description = [describedBy, errorId, hintId].filter(Boolean).join(" ") || undefined;
    const invalid = hasError || Boolean(error);
    const control = (
      <div
        className={cn(
          "relative inline-flex items-center rounded-[var(--radius-md)] border bg-[var(--surface-1)] transition-colors duration-150 focus-within:border-[var(--brand)] focus-within:ring-2 focus-within:ring-[var(--brand)]/20",
          invalid
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
          id={inputId}
          disabled={disabled}
          aria-invalid={invalid || undefined}
          aria-describedby={description}
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
    if (!label && !error && !hint) return control;
    return <div className={cn(fullWidth && "w-full")}>
      {label && <label className="text-label mb-1.5 block text-[var(--text-primary)]" htmlFor={inputId}>{label}</label>}
      {control}
      {hint && <p id={hintId} className="text-helper mt-1.5">{hint}</p>}
      {error && <p id={errorId} role="alert" className="text-helper mt-1.5 font-semibold text-[var(--danger)]">{error}</p>}
    </div>;
  }
);

Input.displayName = "Input";
