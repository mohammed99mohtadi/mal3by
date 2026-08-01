import React from "react";
import { cn } from "@/lib/cn";

export function BidiText({ value, kind = "auto", className }: { value: React.ReactNode; kind?: "auto" | "email" | "phone" | "id" | "price" | "date" | "time" | "uuid"; className?: string }) {
  const ltr = kind !== "auto";
  return <bdi dir={ltr ? "ltr" : "auto"} className={cn("bidi-isolate", ltr && "bidi-value", className)}>{value}</bdi>;
}
