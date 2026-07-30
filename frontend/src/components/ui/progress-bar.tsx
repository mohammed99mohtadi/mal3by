import React from "react";
import { cn } from "@/lib/cn";

export interface ProgressBarProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number; // 0-100
  label?: string;
  showValue?: boolean;
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  showValue = false,
  className,
  ...props
}) => {
  const clamped = Math.min(100, Math.max(0, value));

  return (
    <div className={cn("w-full", className)} {...props}>
      {(label || showValue) && (
        <div className="flex items-center justify-between mb-1.5">
          {label && (
            <span className="text-xs font-medium text-[var(--text-secondary)]">
              {label}
            </span>
          )}
          {showValue && (
            <span className="text-xs font-bold text-[var(--text-primary)]">
              {clamped}%
            </span>
          )}
        </div>
      )}
      <progress
        value={clamped}
        max={100}
        aria-label={label ?? `${clamped}%`}
        className="sr-only"
      />
      <div
        role="none"
        className="w-full h-2 rounded-[var(--radius-pill)] bg-[var(--surface-3)] overflow-hidden"
      >
        <div
          className="h-full rounded-[var(--radius-pill)] bg-[var(--brand)] transition-all duration-300 ease-standard"
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
};
