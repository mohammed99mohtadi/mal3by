import React from "react";
import { cn } from "@/lib/cn";

export interface RadioProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: React.ReactNode;
}

export const Radio = React.forwardRef<HTMLInputElement, RadioProps>(
  ({ className, disabled, label, ...props }, ref) => {
    return (
      <label className={cn("inline-flex items-center gap-2.5 min-h-[44px] cursor-pointer select-none", disabled && "cursor-not-allowed opacity-50")}>
        <input
          ref={ref}
          type="radio"
          disabled={disabled}
          className={cn(
            "size-5 rounded-full border border-[var(--border-strong)] bg-[var(--surface-1)] text-[var(--brand)] focus-ring transition-colors checked:bg-[var(--brand)] checked:border-transparent accent-[var(--brand)]",
            className
          )}
          {...props}
        />
        {label && <span className="text-sm font-medium text-[var(--text-primary)]">{label}</span>}
      </label>
    );
  }
);

Radio.displayName = "Radio";
