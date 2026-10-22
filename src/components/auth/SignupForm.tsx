"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { authFormGrid, authMuted } from "@/components/auth/AuthLayout";
import { useFeedback } from "@/components/providers/Feedback";
import { Field } from "@/components/ui/Field";
import { ArrowRight, Icon } from "@/components/ui/Icon";
import { btn, cn, Notice } from "@/components/ui/primitives";
import { ApiError } from "@/lib/api";
import { homePathFor, signup } from "@/lib/authApi";
import { useUi } from "@/lib/demo-store";
import { focusFirstInvalid, validateForm, type FieldErrors } from "@/lib/validation";

export function SignupForm({ role }: { role: "patient" | "clinician" }) {
  const clinician = role === "clinician";
  const router = useRouter();
  const { toast } = useFeedback();
  const [, setChosenRole] = useUi("chosenRole");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  // Seperti referensi: membuka langkah 2 ikut mengingat peran terpilih.
  useEffect(() => setChosenRole(clinician ? "clinician" : "pasien"), [clinician]); // eslint-disable-line react-hooks/exhaustive-deps

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) return;
    const form = event.currentTarget;
    let next = validateForm(form);
    setFormError("");
    const v = Object.fromEntries(new FormData(form)) as Record<string, string>;
    if (!Object.keys(next).length) {
      if (v.password !== v.confirm) next = { confirm: "Konfirmasi password tidak sesuai." };
      else if (!v.terms) {
        setErrors({});
        setFormError("Persetujuan penggunaan data demo diperlukan.");
        return;
      }
    }
    setErrors(next);
    if (Object.keys(next).length) return focusFirstInvalid(form, next);
    setSubmitting(true);
    try {
      const user = await signup({
        role: clinician ? "clinician" : "pasien",
        email: v.email.trim().toLowerCase(),
        password: v.password,
        full_name: v.name.trim(),
        ...(clinician
          ? {
              str_sip_number: v.str?.trim() || undefined,
              specialization: v.specialty?.trim() || undefined,
              institution: v.institution?.trim() || undefined,
            }
          : { pairing_code: v.paircode.trim().toUpperCase() }),
      });
      router.push(homePathFor(user.role));
      toast("Akun berhasil dibuat. Anda telah masuk ke dashboard.");
    } catch (error) {
      setSubmitting(false);
      if (!(error instanceof ApiError)) {
        setFormError("Tidak dapat terhubung ke server. Pastikan backend sedang berjalan.");
        return;
      }
      const pairingUsed = error.status === 409 && /pairing/i.test(error.message);
      const field: FieldErrors | null =
        error.status === 404
          ? { paircode: "Kode pairing tidak ditemukan. Periksa kembali kode pada rompi Anda." }
          : pairingUsed
            ? { paircode: "Kode pairing ini sudah digunakan oleh akun lain." }
            : error.status === 409
              ? { email: "Email ini sudah terdaftar. Silakan masuk atau gunakan email lain." }
              : null;
      if (field) {
        setErrors(field);
        focusFirstInvalid(form, field);
      } else {
        setFormError(error.message);
      }
    }
  }

  return (
    <>
      <form noValidate onSubmit={submit} className="mt-7">
        <div className={authFormGrid}>
          <Field name="name" label="Nama lengkap" required error={errors.name} />
          <Field name="email" label="Email" type="email" required error={errors.email} />
          <Field name="password" label="Password" type="password" hint="Minimal 8 karakter" required error={errors.password} />
          <Field name="confirm" label="Konfirmasi password" type="password" required error={errors.confirm} />
          {clinician ? (
            <>
              <Field name="str" label="Nomor STR / SIP (opsional)" />
              <Field name="specialty" label="Spesialisasi (opsional)" />
              <Field name="institution" label="Institusi (opsional)" />
            </>
          ) : (
            <>
              <Field name="paircode" label="Kode pairing rompi" hint="Contoh demo: PC-4821" required error={errors.paircode} />
              <Field name="doctor" label="Dokter / klinik (opsional)" />
            </>
          )}
        </div>
        <div className="mt-6">
          <Notice small type={clinician ? "warn" : ""}>
            {clinician
              ? "Registrasi demo belum melakukan verifikasi STR/SIP. Identitas tenaga medis harus diverifikasi pada implementasi produksi."
              : "Kode pairing menghubungkan rompi dengan akun Anda. Mintalah kode kepada pengelola perangkat."}
          </Notice>
        </div>
        <label className="flex items-center gap-3 mt-6">
          <input type="checkbox" name="terms" required /> Saya menyetujui penggunaan data untuk demo pemantauan.
        </label>
        <div role="alert">{formError && <Notice type="error" small>{formError}</Notice>}</div>
        <button type="submit" disabled={submitting} className={cn(btn({ variant: "primary", full: true }), "mt-6")}>
          {submitting ? "Memproses…" : "Buat Akun"} <Icon icon={ArrowRight} />
        </button>
      </form>
      <p className={cn("text-center mt-6", authMuted)}>
        Sudah memiliki akun? <Link href="/login">Masuk</Link>
      </p>
    </>
  );
}
