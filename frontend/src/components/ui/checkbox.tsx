import React from "react";
import { cn } from "@/lib/cn";

export interface CheckboxProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: React.ReactNode;
}

export const Checkbox = React.forwardRef<HTMLInputElement, CheckboxProps>(
  ({ className, disabled, label, ...props }, ref) => {
    return (
      <label className={cn("inline-flex items-center gap-2.5 min-h-[44px] cursor-pointer select-none", disabled && "cursor-not-allowed opacity-50")}>
        <input
          ref={ref}
          type="checkbox"
          disabled={disabled}
          className={cn(
            "size-5 rounded border border-[var(--border-strong)] bg-[var(--surface-1)] text-[var(--brand)] focus-ring transition-colors checked:bg-[var(--brand)] checked:border-transparent accent-[var(--brand)]",
            className
          )}
          {...props}
        />
        {label && <span className="text-sm font-medium text-[var(--text-primary)]">{label}</span>}
      </label>
    );
  }
);

Checkbox.displayName = "Checkbox";
