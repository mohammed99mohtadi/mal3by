import { cookies } from "next/headers";
import { BottomNavItems } from "./bottom-nav-items";

export interface BottomNavigationProps {
  locale: string;
}

export async function BottomNavigation({ locale }: BottomNavigationProps) {
  const cookieStore = await cookies();
  const isLoggedIn = Boolean(cookieStore.get("mal3by_session"));

  return <BottomNavItems locale={locale} isLoggedIn={isLoggedIn} />;
}
