import React from "react";
import { cn } from "@/lib/cn";

export function VisuallyHidden({ className, ...props }: React.HTMLAttributes<HTMLSpanElement>) {
  return <span className={cn("sr-only", className)} {...props} />;
}
