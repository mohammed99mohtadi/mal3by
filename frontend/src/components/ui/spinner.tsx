import React from "react";
import { cn } from "@/lib/cn";

export interface SpinnerProps extends React.HTMLAttributes<HTMLSpanElement> {
  size?: "sm" | "md" | "lg";
  label?: string;
}

const sizes = {
  sm: "size-4",
  md: "size-6",
  lg: "size-8",
};

export const Spinner: React.FC<SpinnerProps> = ({
  size = "md",
  label,
  className,
  ...props
}) => {
  return (
    <span
      role="status"
      aria-label={!label ? "Loading" : undefined}
      className={cn("inline-flex items-center gap-2", className)}
      {...props}
    >
      <svg
        className={cn("animate-spin text-[var(--brand)]", sizes[size])}
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
        aria-hidden="true"
      >
        <circle
          className="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          strokeWidth="4"
        />
        <path
          className="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
        />
      </svg>
      {label && (
        <span className="text-sm text-[var(--text-muted)]">{label}</span>
      )}
    </span>
  );
};
