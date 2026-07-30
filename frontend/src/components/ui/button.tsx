import React from "react";
import { cn } from "@/lib/cn";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  fullWidth?: boolean;
  children: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      isLoading = false,
      fullWidth = false,
      className,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-bold text-center border transition-all duration-150 ease-in-out focus-ring cursor-pointer select-none disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none disabled:pointer-events-none";

    const variants = {
      primary: "bg-[var(--brand)] text-[var(--brand-foreground)] border-transparent hover:brightness-105 active:brightness-95",
      secondary: "bg-[var(--surface-2)] text-[var(--text-primary)] border-[var(--border-strong)] hover:bg-[var(--surface-3)] active:bg-[var(--surface-1)]",
      outline: "bg-transparent text-[var(--text-primary)] border-[var(--border-strong)] hover:border-[var(--brand)] hover:text-[var(--brand)] active:bg-[var(--surface-2)]",
      ghost: "bg-transparent text-[var(--text-secondary)] border-transparent hover:bg-[var(--surface-2)] hover:text-[var(--text-primary)] active:bg-[var(--surface-3)]",
      danger: "bg-[var(--danger)] text-white border-transparent hover:brightness-110 active:brightness-90",
    };

    const sizes = {
      sm: "text-xs px-3 py-1.5 min-h-[36px] rounded-[var(--radius-sm)] gap-1.5",
      md: "text-sm px-4 py-2.5 min-h-[44px] rounded-[var(--radius-md)] gap-2",
      lg: "text-base px-6 py-3.5 min-h-[50px] rounded-[var(--radius-lg)] gap-2.5",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        className={cn(
          baseStyles,
          variants[variant],
          sizes[size],
          fullWidth && "w-full",
          className
        )}
        {...props}
      >
        {isLoading ? (
          <>
            <svg
              className="animate-spin -ms-1 me-2 h-4 w-4 text-current"
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
              ></circle>
              <path
                className="opacity-75"
                fill="currentColor"
                d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
              ></path>
            </svg>
            <span>{children}</span>
          </>
        ) : (
          children
        )}
      </button>
    );
  }
);

Button.displayName = "Button";
