"use client";

import { useRouter } from "next/navigation";
import { ErrorState } from "@/components/ui/error-state";
import { copy, type Locale } from "@/lib/copy";

export function ProfileError({ locale }: { locale: Locale }) { const router = useRouter(); return <ErrorState locale={locale} title={copy[locale].profileLoadErrorTitle} description={copy[locale].profileLoadErrorDescription} actionLabel={copy[locale].retry} onAction={() => router.refresh()} />; }
