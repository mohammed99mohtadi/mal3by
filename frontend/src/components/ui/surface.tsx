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
    const baseStyles = "rounded-[var(--radius-lg)] border border-[var(--border-strong)] transition-all duration-[var(--duration-fast)]";

    const variants = {
      base: "bg-[var(--surface-1)] shadow-[var(--shadow-sm)]",
      elevated: "bg-[var(--surface-elevated)] shadow-[var(--shadow-md)]",
      interactive:
        "bg-[var(--surface-1)] shadow-[var(--shadow-sm)] hover:border-[var(--brand)]/50 hover:bg-[var(--surface-muted)] cursor-pointer focus-ring will-change-transform",
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
