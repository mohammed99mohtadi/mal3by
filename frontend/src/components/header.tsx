import { cookies } from "next/headers";
import { HeaderNav } from "./header-nav";

export interface HeaderProps {
  locale: string;
}

export async function Header({ locale }: HeaderProps) {
  const cookieStore = await cookies();
  const isLoggedIn = Boolean(cookieStore.get("mal3by_session"));

  return <HeaderNav locale={locale} isLoggedIn={isLoggedIn} />;
}
