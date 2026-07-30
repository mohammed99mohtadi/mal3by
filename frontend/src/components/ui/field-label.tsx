import React from "react";
import { cn } from "@/lib/cn";

export interface FieldLabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {
  required?: boolean;
}

export const FieldLabel: React.FC<FieldLabelProps> = ({
  required = false,
  className,
  children,
  ...props
}) => {
  return (
    <label
      className={cn("block text-sm font-semibold text-[var(--text-primary)] mb-1.5", className)}
      {...props}
    >
      {children}
      {required && (
        <span className="ms-1 text-[var(--danger)]" aria-hidden="true">
          *
        </span>
      )}
    </label>
  );
};
