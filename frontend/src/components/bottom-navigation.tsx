import { cookies } from "next/headers";
import type { Locale } from "@/lib/copy";
import { BottomNavItems } from "./bottom-nav-items";

export async function BottomNavigation({ locale }: { locale: Locale }) {
  return <BottomNavItems locale={locale} isLoggedIn={Boolean((await cookies()).get("mal3by_session"))} />;
}
