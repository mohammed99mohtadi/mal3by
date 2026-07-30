import React from "react";
import { cn } from "@/lib/cn";
import { Button, type ButtonProps } from "@/components/ui/button";

export interface EmptyStateProps extends React.HTMLAttributes<HTMLDivElement> {
  icon?: React.ReactNode;
  title: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  actionVariant?: ButtonProps["variant"];
  actionHref?: string;
  size?: "compact" | "large";
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  icon,
  title,
  description,
  actionLabel,
  onAction,
  actionVariant = "primary",
  size = "large",
  className,
  ...props
}) => {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center text-center",
        size === "large" ? "py-16 px-6 gap-4" : "py-8 px-4 gap-3",
        className
      )}
      {...props}
    >
      {icon && (
        <span
          aria-hidden="true"
          className={cn(
            "text-[var(--text-muted)]",
            size === "large" ? "mb-2" : "mb-1"
          )}
        >
          {icon}
        </span>
      )}
      <div>
        <p
          className={cn(
            "font-bold text-[var(--text-primary)]",
            size === "large" ? "text-lg" : "text-base"
          )}
        >
          {title}
        </p>
        {description && (
          <p
            className={cn(
              "text-[var(--text-muted)] mt-1",
              size === "large" ? "text-sm" : "text-xs"
            )}
          >
            {description}
          </p>
        )}
      </div>
      {actionLabel && onAction && (
        <Button
          variant={actionVariant}
          size={size === "large" ? "md" : "sm"}
          onClick={onAction}
          className="mt-2"
        >
          {actionLabel}
        </Button>
      )}
    </div>
  );
};
