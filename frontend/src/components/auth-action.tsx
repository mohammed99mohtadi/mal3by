import Link from "next/link";
import { cn } from "@/lib/cn";

export function AuthAction({ href, children, className }: { href: string; children: React.ReactNode; className?: string }) {
  return <Link href={href} className={cn("auth-action focus-ring", className)}>{children}</Link>;
}
