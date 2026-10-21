"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState, type FormEvent } from "react";
import { authFormGrid, authMuted } from "@/components/auth/AuthLayout";
import { useFeedback } from "@/components/providers/Feedback";
import { Field } from "@/components/ui/Field";
import { ArrowRight, Icon } from "@/components/ui/Icon";
import { btn, cn, Notice } from "@/components/ui/primitives";
import { VALID_PAIR_CODES } from "@/lib/demo-data";
import { updateDemo, useUi } from "@/lib/demo-store";
import { focusFirstInvalid, validateForm, type FieldErrors } from "@/lib/validation";

export function SignupForm({ role }: { role: "patient" | "clinician" }) {
  const clinician = role === "clinician";
  const router = useRouter();
  const { toast } = useFeedback();
  const [, setChosenRole] = useUi("chosenRole");
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");

  // Seperti referensi: membuka langkah 2 ikut mengingat peran terpilih.
  useEffect(() => setChosenRole(clinician ? "clinician" : "pasien"), [clinician]); // eslint-disable-line react-hooks/exhaustive-deps

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
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
      } else if (!clinician && !VALID_PAIR_CODES.includes(v.paircode.toUpperCase()))
        next = { paircode: "Kode pairing tidak ditemukan. Gunakan PC-4821 pada demo." };
    }
    setErrors(next);
    if (Object.keys(next).length) return focusFirstInvalid(form, next);
    updateDemo((d) => ({
      ...d,
      [role]: {
        ...d[role],
        name: v.name,
        email: v.email,
        ...(clinician ? { str: v.str, specialty: v.specialty, institution: v.institution } : {}),
      },
    }));
    router.push(clinician ? "/clinician/patients" : "/patient/home");
    toast("Akun demo berhasil dibuat. Anda telah masuk ke dashboard.");
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
        <button type="submit" className={cn(btn({ variant: "primary", full: true }), "mt-6")}>
          Buat Akun <Icon icon={ArrowRight} />
        </button>
      </form>
      <p className={cn("text-center mt-6", authMuted)}>
        Sudah memiliki akun? <Link href="/login">Masuk</Link>
      </p>
    </>
  );
}
