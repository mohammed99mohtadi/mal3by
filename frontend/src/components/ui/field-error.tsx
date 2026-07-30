import React from "react";
import { cn } from "@/lib/cn";

export interface FieldErrorProps extends React.HTMLAttributes<HTMLParagraphElement> {
  id?: string;
  message?: string;
}

export const FieldError: React.FC<FieldErrorProps> = ({
  id,
  message,
  className,
  children,
  ...props
}) => {
  const content = message ?? children;
  if (!content) return null;

  return (
    <p
      id={id}
      role="alert"
      className={cn("mt-1.5 text-xs font-medium text-[var(--danger)]", className)}
      {...props}
    >
      {content}
    </p>
  );
};
