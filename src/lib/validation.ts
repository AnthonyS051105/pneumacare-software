// Validasi form demo — padanan validation()/thresholdValid() di referensi app.js.

export type FieldErrors = Record<string, string>;

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export const isEmail = (value: string) => EMAIL_PATTERN.test(value);

/** Validasi umum: wajib diisi, format email, dan panjang password minimal 8. */
export function validateForm(form: HTMLFormElement): FieldErrors {
  const errors: FieldErrors = {};
  form.querySelectorAll("input").forEach((input) => {
    if (input.required && !input.value.trim()) errors[input.name] = "Kolom ini wajib diisi.";
    else if (input.type === "email" && input.value && !isEmail(input.value))
      errors[input.name] = "Masukkan alamat email yang valid.";
    else if (input.type === "password" && input.value.length < 8)
      errors[input.name] = "Password minimal 8 karakter.";
  });
  return errors;
}

export const thresholdKeys = ["hrmin", "hrmax", "spo2min", "rrmin", "rrmax"] as const;

/** Ambang vital valid bila semua angka > 0, maks > min, dan SpO₂ <= 100. */
export function thresholdErrors(raw: Record<string, string>): FieldErrors | null {
  const v = Object.fromEntries(thresholdKeys.map((k) => [k, Number(raw[k])])) as Record<string, number>;
  const valid =
    thresholdKeys.every((k) => raw[k] !== "" && raw[k] !== undefined && Number.isFinite(v[k]) && v[k] > 0) &&
    v.hrmax > v.hrmin &&
    v.rrmax > v.rrmin &&
    v.spo2min <= 100;
  if (valid) return null;
  const errors: FieldErrors = {};
  thresholdKeys.forEach((k) => {
    if (!raw[k] || v[k] <= 0) errors[k] = "Isi angka lebih besar dari nol.";
  });
  if (v.hrmax <= v.hrmin) errors.hrmax = "Maksimum harus lebih besar dari minimum.";
  if (v.rrmax <= v.rrmin) errors.rrmax = "Maksimum harus lebih besar dari minimum.";
  if (v.spo2min > 100) errors.spo2min = "SpO₂ maksimal 100%.";
  return errors;
}

/** Fokus ke input pertama yang ditandai invalid setelah state error dirender. */
export function focusFirstInvalid(form: HTMLFormElement, errors: FieldErrors) {
  const first = Object.keys(errors)[0];
  if (first) requestAnimationFrame(() => (form.elements.namedItem(first) as HTMLElement | null)?.focus());
}
