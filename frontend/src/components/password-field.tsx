"use client";

import React, { forwardRef, useState } from "react";
import { IconButton } from "@/components/ui/icon-button";
import { Input } from "@/components/ui/input";
import { copy, type Locale } from "@/lib/copy";

export interface PasswordFieldProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> { locale: Locale; label: string; error?: string; hint?: React.ReactNode; }

export const PasswordField = forwardRef<HTMLInputElement, PasswordFieldProps>(({ locale, label, error, hint, onKeyDown, onKeyUp, ...props }, ref) => {
  const t = copy[locale]; const [visible, setVisible] = useState(false); const [capsLock, setCapsLock] = useState(false);
  function detect(event: React.KeyboardEvent<HTMLInputElement>) { setCapsLock(event.getModifierState("CapsLock")); }
  return <Input ref={ref} type={visible ? "text" : "password"} label={label} error={error} hint={<>{hint}{capsLock && <span className="mt-1 block font-semibold text-[var(--warning)]" role="status">{t.passwordCapsLock}</span>}</>} trailingSlot={<IconButton className="size-9 min-h-9 border-0 bg-transparent" label={visible ? t.passwordHide : t.passwordShow} aria-pressed={visible} onClick={() => setVisible((value) => !value)}>{visible ? <span aria-hidden>◉</span> : <span aria-hidden>○</span>}</IconButton>} onKeyDown={(event) => { detect(event); onKeyDown?.(event); }} onKeyUp={(event) => { detect(event); onKeyUp?.(event); }} {...props} />;
});
PasswordField.displayName = "PasswordField";
