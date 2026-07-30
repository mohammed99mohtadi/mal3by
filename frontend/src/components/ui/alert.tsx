import React from "react";
import { cn } from "@/lib/cn";

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  tone?: "info" | "success" | "warning" | "danger";
  title?: string;
  message: React.ReactNode;
}

const toneConfig = {
  info: {
    containerClass: "bg-[var(--info)]/10 border-[var(--info)]/30 text-[var(--info)]",
    textClass: "text-[var(--info)]",
    icon: (
      <svg className="size-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    role: "status" as const,
  },
  success: {
    containerClass: "bg-[var(--success)]/10 border-[var(--success)]/30 text-[var(--success)]",
    textClass: "text-[var(--success)]",
    icon: (
      <svg className="size-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    role: "status" as const,
  },
  warning: {
    containerClass: "bg-[var(--warning)]/10 border-[var(--warning)]/30 text-[var(--warning)]",
    textClass: "text-[var(--warning)]",
    icon: (
      <svg className="size-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.834-1.964-.834-2.732 0L3.07 16.5c-.77.833.192 2.5 1.732 2.5z" />
      </svg>
    ),
    role: "alert" as const,
  },
  danger: {
    containerClass: "bg-[var(--danger)]/10 border-[var(--danger)]/30 text-[var(--danger)]",
    textClass: "text-[var(--danger)]",
    icon: (
      <svg className="size-5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    role: "alert" as const,
  },
};

export const Alert: React.FC<AlertProps> = ({
  tone = "info",
  title,
  message,
  className,
  ...props
}) => {
  const config = toneConfig[tone];

  return (
    <div
      role={config.role}
      className={cn(
        "flex items-start gap-3 rounded-[var(--radius-md)] border p-4",
        config.containerClass,
        className
      )}
      {...props}
    >
      <span aria-hidden="true">{config.icon}</span>
      <div className="flex-1 min-w-0">
        {title && (
          <p className="font-semibold text-sm mb-1">{title}</p>
        )}
        <p className="text-sm opacity-90">{message}</p>
      </div>
    </div>
  );
};
