import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { ProfileError } from "./profile-error";
const refresh = vi.fn(); vi.mock("next/navigation", () => ({ useRouter: () => ({ refresh }) }));
describe("ProfileError", () => { it("renders safe localized recovery without raw errors", () => { render(<ProfileError locale="ar" />); expect(screen.getByRole("heading", { name: "تعذر تحميل الملف الشخصي" })).toBeInTheDocument(); fireEvent.click(screen.getByRole("button", { name: "إعادة المحاولة" })); expect(refresh).toHaveBeenCalled(); }); });
