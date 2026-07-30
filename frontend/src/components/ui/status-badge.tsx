import React from "react";
import { cn } from "@/lib/cn";

export interface StatusBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  status?: "neutral" | "success" | "warning" | "danger" | "info";
  size?: "sm" | "md";
  children: React.ReactNode;
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({
  status = "neutral",
  size = "md",
  className,
  children,
  ...props
}) => {
  const baseStyles =
    "inline-flex items-center justify-center font-bold rounded-[var(--radius-pill)] border transition-colors select-none";

  const statuses = {
    neutral: "bg-[var(--surface-3)] text-[var(--text-secondary)] border-[var(--border-subtle)]",
    success: "bg-[var(--success)]/15 text-[var(--success)] border-[var(--success)]/30",
    warning: "bg-[var(--warning)]/15 text-[var(--warning)] border-[var(--warning)]/30",
    danger: "bg-[var(--danger)]/15 text-[var(--danger)] border-[var(--danger)]/30",
    info: "bg-[var(--info)]/15 text-[var(--info)] border-[var(--info)]/30",
  };

  const sizes = {
    sm: "text-[0.7rem] px-2 py-0.5 gap-1",
    md: "text-xs px-2.5 py-1 gap-1.5",
  };

  return (
    <span
      className={cn(baseStyles, statuses[status], sizes[size], className)}
      {...props}
    >
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full shrink-0",
          status === "neutral" && "bg-[var(--text-muted)]",
          status === "success" && "bg-[var(--success)]",
          status === "warning" && "bg-[var(--warning)]",
          status === "danger" && "bg-[var(--danger)]",
          status === "info" && "bg-[var(--info)]"
        )}
        aria-hidden="true"
      />
      {children}
    </span>
  );
};
