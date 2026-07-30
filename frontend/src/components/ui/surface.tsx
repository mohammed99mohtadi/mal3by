import React from "react";
import { cn } from "@/lib/cn";

export interface SurfaceProps extends React.HTMLAttributes<HTMLDivElement> {
  as?: "div" | "article" | "section" | "aside";
  variant?: "base" | "elevated" | "interactive";
  padding?: "none" | "sm" | "md" | "lg";
}

export const Surface = React.forwardRef<HTMLDivElement, SurfaceProps>(
  (
    {
      as: Component = "div",
      variant = "base",
      padding = "md",
      className,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles = "rounded-[var(--radius-lg)] border border-[var(--border-strong)] transition-all duration-150";

    const variants = {
      base: "bg-[var(--surface-1)] box-shadow-[var(--shadow-sm)]",
      elevated: "bg-[var(--surface-2)] box-shadow-[var(--shadow-md)]",
      interactive:
        "bg-[var(--surface-1)] box-shadow-[var(--shadow-sm)] hover:border-[var(--brand)]/50 hover:bg-[var(--surface-2)] cursor-pointer focus-ring",
    };

    const paddings = {
      none: "p-0",
      sm: "p-3 sm:p-4",
      md: "p-4 sm:p-6",
      lg: "p-6 sm:p-8",
    };

    return (
      <Component
        ref={ref}
        className={cn(baseStyles, variants[variant], paddings[padding], className)}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

Surface.displayName = "Surface";
