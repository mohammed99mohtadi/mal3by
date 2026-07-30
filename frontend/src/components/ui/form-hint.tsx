import React from "react";
import { cn } from "@/lib/cn";

export interface FormHintProps extends React.HTMLAttributes<HTMLParagraphElement> {
  id?: string;
}

export const FormHint: React.FC<FormHintProps> = ({
  id,
  className,
  children,
  ...props
}) => {
  return (
    <p
      id={id}
      className={cn("mt-1.5 text-xs text-[var(--text-muted)]", className)}
      {...props}
    >
      {children}
    </p>
  );
};
