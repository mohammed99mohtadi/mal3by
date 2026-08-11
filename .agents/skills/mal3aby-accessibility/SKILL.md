---
name: mal3aby-accessibility
description: Implement and audit accessible bilingual MAL3ABY interfaces. Use for semantic HTML, keyboard and focus behavior, forms, validation, announcements, contrast, reduced motion, touch targets, Arabic RTL, English LTR, mixed-direction values, or directional icons.
---

# MAL3ABY Accessibility

- Keep `lang="ar" dir="rtl"` and `lang="en" dir="ltr"` at the document root. Never fake RTL with text alignment.
- Use logical CSS properties. Isolate email, phone, IDs, codes, currency, and time ranges with `bdi`, `dir="ltr"`, or existing Bidi helpers.
- Mirror back/forward arrows and directional icons in RTL; do not mirror brand, play, or status symbols.
- Use semantic landmarks, one visible page `h1`, logical headings, and the existing skip link.
- Make flows keyboard-completable with logical DOM order and visible `:focus-visible`.
- Keep targets at least 44 by 44 CSS pixels; do not rely on hover or color alone.
- Dialogs/drawers need an accessible name, focus trap, Escape, background blocking, and focus restoration.
- Forms need programmatic labels, correct type/inputMode/autocomplete, associated hints/errors, `aria-invalid`, and preserved values after failure.
- On submit failure, focus an error summary or first invalid field. Use deliberate `aria-live` messaging without duplicate speech.
- Expose loading with duplicate-submission prevention, `aria-busy`, stable labels, and perceivable progress. Never announce false success.
- Use native checkbox/radio behavior or a complete keyboard equivalent; selection cannot be color-only.
- Verify contrast, reduced motion, Arabic/English keyboard flows, 200% zoom, 320px reflow, screen-reader names, focus restoration, announcements, and bidi punctuation.
- Use Testing Library role/name queries and `web-design-guidelines`; rendering alone is not accessibility verification.
