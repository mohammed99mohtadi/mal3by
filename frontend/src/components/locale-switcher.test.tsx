import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
vi.mock("next/navigation",()=>({usePathname:()=>"/ar/courts/8"}));
vi.mock("next/link",()=>({default:({href,children}:{href:string;children:React.ReactNode})=><a href={href}>{children}</a>}));
import { LocaleSwitcher } from "./locale-switcher";
describe("LocaleSwitcher",()=>it("preserves path while replacing locale",()=>{render(<LocaleSwitcher locale="ar"/>);expect(screen.getByRole("link")).toHaveAttribute("href","/en/courts/8")}));
