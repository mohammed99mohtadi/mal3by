import React from "react";
import { cn } from "@/lib/cn";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "text" | "circular" | "rectangular";
}

export const Skeleton: React.FC<SkeletonProps> = ({
  variant = "rectangular",
  className,
  ...props
}) => {
  const baseStyles = "skeleton-shimmer bg-[var(--skeleton)] shrink-0 overflow-hidden";

  const variants = {
    text: "h-4 rounded-[var(--radius-sm)] w-full",
    circular: "rounded-full",
    rectangular: "rounded-[var(--radius-md)]",
  };

  return (
    <div
      aria-hidden="true"
      className={cn(baseStyles, variants[variant], className)}
      {...props}
    />
  );
};
