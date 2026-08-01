"use client";

import { useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { Alert } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PasswordField } from "@/components/password-field";
import { copy, type Locale } from "@/lib/copy";
import { safeReturnPath } from "@/lib/redirect";

type Field = "full_name" | "email" | "phone_number" | "password" | "password_confirmation";
type Errors = Partial<Record<Field, string>>;

export function AuthForm({ locale, mode, returnTo }: { locale: Locale; mode: "login" | "register"; returnTo?: string | null }) {
  const t = copy[locale]; const router = useRouter(); const [errors, setErrors] = useState<Errors>({}); const [summary, setSummary] = useState(""); const [loading, setLoading] = useState(false); const [passwordValue, setPasswordValue] = useState("");
  const submitting = useRef(false); const nameRef = useRef<HTMLInputElement>(null); const emailRef = useRef<HTMLInputElement>(null); const phoneRef = useRef<HTMLInputElement>(null); const passwordRef = useRef<HTMLInputElement>(null); const confirmationRef = useRef<HTMLInputElement>(null);
  function focusField(field: Field) { if (field === "full_name") nameRef.current?.focus(); else if (field === "email") emailRef.current?.focus(); else if (field === "phone_number") phoneRef.current?.focus(); else if (field === "password") passwordRef.current?.focus(); else confirmationRef.current?.focus(); }
  function validate(values: Record<string, string>): Errors {
    const next: Errors = {};
    if (mode === "register" && values.full_name.trim().length < 2) next.full_name = t.nameError;
    if (!/^\S+@\S+\.\S+$/.test(values.email)) next.email = t.emailError;
    if (values.password.length < 8 || values.password.length > 100) next.password = t.passwordError;
    if (mode === "register" && values.password_confirmation !== values.password) next.password_confirmation = t.passwordMismatch;
    return next;
  }
  async function submit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault(); if (submitting.current) return;
    const data = new FormData(event.currentTarget); const values = Object.fromEntries(Array.from(data.entries()).map(([key,value]) => [key, String(value)])); const next = validate(values); setErrors(next); setSummary("");
    const first = Object.keys(next)[0] as Field | undefined; if (first) { focusField(first); return; }
    submitting.current = true; setLoading(true);
    const body = mode === "login" ? { email: values.email, password: values.password } : { full_name: values.full_name.trim(), email: values.email, password: values.password, ...(values.phone_number.trim() ? { phone_number: values.phone_number.trim() } : {}) };
    try {
      const response = await fetch(mode === "login" ? "/api/auth/login" : "/api/auth/register", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
      const payload = await response.json().catch(() => null) as { detail?: unknown } | null;
      if (!response.ok) {
        const detail = typeof payload?.detail === "string" ? payload.detail.toLowerCase() : "";
        const message = mode === "login" && response.status === 401 ? t.invalidCredentials : mode === "register" && response.status === 400 && (detail.includes("email") || detail.includes("phone")) ? t.duplicateAccount : response.status === 422 ? t.invalidDetails : t.authUnexpectedError;
        setSummary(message); return;
      }
      router.push(mode === "login" ? safeReturnPath(returnTo ?? null, locale) : `/${locale}/login`); router.refresh();
    } catch { setSummary(t.authNetworkError); }
    finally { submitting.current = false; setLoading(false); }
  }
  const strength = passwordValue.length >= 12 ? t.passwordStrengthStrong : passwordValue.length >= 8 ? t.passwordStrengthReady : t.passwordStrengthShort;
  return <form noValidate onSubmit={submit} className="mt-7 grid gap-5">
    {summary && <Alert tone="danger" title={t.authErrorTitle} message={summary} />}
    {mode === "register" && <Input ref={nameRef} fullWidth required name="full_name" autoComplete="name" label={t.fullNameLabel} error={errors.full_name} maxLength={100} />}
    <Input ref={emailRef} fullWidth required name="email" type="email" inputMode="email" autoCapitalize="none" autoCorrect="off" autoComplete="email" dir="ltr" label={t.emailLabel} error={errors.email} />
    {mode === "register" && <Input ref={phoneRef} fullWidth name="phone_number" type="tel" inputMode="tel" autoComplete="tel" dir="ltr" label={t.phoneLabel} hint={t.phoneOptional} error={errors.phone_number} maxLength={20} />}
    <PasswordField ref={passwordRef} locale={locale} required name="password" label={t.passwordLabel} autoComplete={mode === "login" ? "current-password" : "new-password"} minLength={8} maxLength={100} error={errors.password} value={passwordValue} onChange={(event) => setPasswordValue(event.target.value)} hint={mode === "register" ? <span>{t.passwordGuidance} <strong>{strength}</strong></span> : undefined} />
    {mode === "register" && <PasswordField ref={confirmationRef} locale={locale} required name="password_confirmation" label={t.passwordConfirmLabel} autoComplete="new-password" error={errors.password_confirmation} />}
    <Button type="submit" fullWidth size="lg" isLoading={loading}>{loading ? t.authSubmitting : mode === "login" ? t.login : t.register}</Button>
  </form>;
}
