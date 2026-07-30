export const copy = {
  ar: {
    brand: "ملعبي",
    courts: "الملاعب",
    login: "تسجيل الدخول",
    register: "إنشاء حساب",
    profile: "حسابي",
    bookings: "حجوزاتي",
    hero: "احجز ملعبك. العب بطريقتك.",
    discover: "اكتشف الملاعب",
    featured: "ملاعب متاحة",
    reviews: "تقييمات موثقة",
    logout: "تسجيل الخروج",
    price: "د.ك / ساعة",
    empty: "لا توجد ملاعب متاحة الآن",
    back: "العودة للملاعب",
    navHome: "الرئيسية",
    navCourts: "الملاعب",
    navBookings: "حجوزاتي",
    navProfile: "حسابي",
    navLogin: "الدخول",
    switchLang: "تغيير إلى الإنجليزية",
    switchLangShort: "EN",

    // Homepage Hero
    heroEyebrow: "الحجز الرياضي في الكويت",
    heroHeadline: "احجز ملعبك. العب بطريقتك.",
    heroSubline: "اكتشف الملاعب المتاحة، اختر الوقت المناسب، واحتفظ بحجوزاتك في مكان واحد.",
    heroCta: "اكتشف الملاعب",
    heroCtaSecondary: "حجوزاتي",
    heroCtaLogin: "تسجيل الدخول للحجز",

    // Featured Courts
    featuredEyebrow: "استكشف",
    featuredTitle: "ملاعب متاحة",
    featuredViewAll: "عرض الكل",
    featuredLoading: "جاري تحميل الملاعب...",
    featuredEmpty: "لا توجد ملاعب متاحة حالياً",
    featuredEmptyDesc: "تحقق مرة أخرى لاحقاً أو تواصل معنا.",
    featuredError: "تعذّر تحميل الملاعب، يُرجى المحاولة مرة أخرى.",
    priceUnit: "د.ك / ساعة",

    // How It Works
    howTitle: "كيف يعمل ملعبي؟",
    howStep1Title: "اكتشف ملعبك",
    howStep1Desc: "تصفّح الملاعب الرياضية المتاحة وابحث عن الأنسب لك.",
    howStep2Title: "اختر الوقت",
    howStep2Desc: "اختر الوقت المناسب من الفترات المتاحة الفعلية.",
    howStep3Title: "أكّد الحجز",
    howStep3Desc: "احجز بسهولة واحتفظ بتفاصيل حجزك في مكانٍ واحد.",

    // Why Mal3by
    whyTitle: "لماذا ملعبي؟",
    whyBenefit1Title: "بحث سهل",
    whyBenefit1Desc: "استعرض الملاعب بحسب الرياضة والموقع والتوفر.",
    whyBenefit2Title: "إدارة الحجوزات",
    whyBenefit2Desc: "تابع حجوزاتك وأوقاتها من لوحة تحكم واحدة.",
    whyBenefit3Title: "عربي وإنجليزي",
    whyBenefit3Desc: "المنصة تدعم اللغة العربية والإنجليزية بالكامل.",
    whyBenefit4Title: "متوافق مع الجوّال",
    whyBenefit4Desc: "تجربة سلسة على الهاتف والحاسوب.",

    // Final CTA
    finalCtaTitle: "جاهز للعب؟",
    finalCtaDesc: "ابدأ الآن واستعرض الملاعب المتاحة.",
    finalCtaButton: "استعرض الملاعب",

    // Footer
    footerTagline: "ملعبي · الكويت",
  },
  en: {
    brand: "Mal3by",
    courts: "Courts",
    login: "Log in",
    register: "Create account",
    profile: "Profile",
    bookings: "My Bookings",
    hero: "Book your court. Play your way.",
    discover: "Explore courts",
    featured: "Available courts",
    reviews: "Verified reviews",
    logout: "Log out",
    price: "KWD / hour",
    empty: "No courts available right now",
    back: "Back to courts",
    navHome: "Home",
    navCourts: "Courts",
    navBookings: "Bookings",
    navProfile: "Profile",
    navLogin: "Log in",
    switchLang: "Switch to Arabic",
    switchLangShort: "العربية",

    // Homepage Hero
    heroEyebrow: "KUWAIT SPORTS BOOKING",
    heroHeadline: "Book your court. Play your way.",
    heroSubline: "Find available courts, choose a real time slot, and manage all your bookings in one place.",
    heroCta: "Explore Courts",
    heroCtaSecondary: "My Bookings",
    heroCtaLogin: "Log in to Book",

    // Featured Courts
    featuredEyebrow: "DISCOVER",
    featuredTitle: "Available Courts",
    featuredViewAll: "View all",
    featuredLoading: "Loading courts...",
    featuredEmpty: "No courts available right now",
    featuredEmptyDesc: "Check back soon or reach out to us.",
    featuredError: "Could not load courts. Please try again.",
    priceUnit: "KWD / hr",

    // How It Works
    howTitle: "How Mal3by Works",
    howStep1Title: "Find a Court",
    howStep1Desc: "Browse available sports courts and find the right one for you.",
    howStep2Title: "Pick a Slot",
    howStep2Desc: "Choose from real available time slots that suit your schedule.",
    howStep3Title: "Confirm Booking",
    howStep3Desc: "Book instantly and keep all your booking details in one place.",

    // Why Mal3by
    whyTitle: "Why Mal3by?",
    whyBenefit1Title: "Easy Discovery",
    whyBenefit1Desc: "Filter courts by sport, location, and availability.",
    whyBenefit2Title: "Booking Management",
    whyBenefit2Desc: "Track your upcoming and past bookings from one dashboard.",
    whyBenefit3Title: "Arabic & English",
    whyBenefit3Desc: "Full bilingual support for Arabic and English speakers.",
    whyBenefit4Title: "Mobile Friendly",
    whyBenefit4Desc: "A smooth experience on both phone and desktop.",

    // Final CTA
    finalCtaTitle: "Ready to Play?",
    finalCtaDesc: "Start now and browse available courts near you.",
    finalCtaButton: "Browse Courts",

    // Footer
    footerTagline: "Mal3by · Kuwait",
  },
} as const;

export type Locale = keyof typeof copy;
