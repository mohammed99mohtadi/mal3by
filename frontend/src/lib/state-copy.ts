import type { Locale } from "@/lib/copy";

export type PageStateKind = "error" | "offline" | "unauthorized" | "forbidden" | "not-found";
export const stateCopy: Record<Locale, Record<PageStateKind, { title: string; description: string }>> = {
  ar: {
    error: { title: "حدث خطأ", description: "تعذر إكمال الطلب. حاول مرة أخرى." },
    offline: { title: "لا يوجد اتصال", description: "تحقق من اتصالك بالإنترنت ثم حاول مرة أخرى." },
    unauthorized: { title: "سجّل الدخول للمتابعة", description: "يجب تسجيل الدخول لعرض هذه الصفحة." },
    forbidden: { title: "لا يمكنك الوصول", description: "ليس لديك صلاحية لعرض هذه الصفحة." },
    "not-found": { title: "الصفحة غير موجودة", description: "قد يكون الرابط غير صحيح أو لم تعد الصفحة متاحة." },
  },
  en: {
    error: { title: "Something went wrong", description: "We could not complete the request. Please try again." },
    offline: { title: "You are offline", description: "Check your internet connection, then try again." },
    unauthorized: { title: "Log in to continue", description: "You need to log in to view this page." },
    forbidden: { title: "Access denied", description: "You do not have permission to view this page." },
    "not-found": { title: "Page not found", description: "The link may be incorrect or the page is no longer available." },
  },
};
