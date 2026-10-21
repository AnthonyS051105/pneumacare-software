"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useRef, useState, type FormEvent } from "react";
import { authMuted } from "@/components/auth/AuthLayout";
import { useFeedback } from "@/components/providers/Feedback";
import { Field } from "@/components/ui/Field";
import { ArrowRight, Icon } from "@/components/ui/Icon";
import { btn, cn, Notice } from "@/components/ui/primitives";
import { DEMO_CLINICIAN_EMAIL, DEMO_PASSWORD, DEMO_PATIENT_EMAIL } from "@/lib/demo-data";
import { focusFirstInvalid, validateForm, type FieldErrors } from "@/lib/validation";

const REMEMBER_KEY = "pneuma-email";

export function LoginForm() {
  const router = useRouter();
  const { openModal } = useFeedback();
  const formRef = useRef<HTMLFormElement>(null);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");

  useEffect(() => {
    try {
      const remembered = localStorage.getItem(REMEMBER_KEY);
      const email = formRef.current?.elements.namedItem("email") as HTMLInputElement | null;
      if (remembered && email) email.value = remembered;
    } catch {}
  }, []);

  function fill(email: string) {
    const form = formRef.current;
    if (!form) return;
    const emailInput = form.elements.namedItem("email") as HTMLInputElement;
    const password = form.elements.namedItem("password") as HTMLInputElement;
    emailInput.value = email;
    password.value = DEMO_PASSWORD;
    password.type = "password";
    emailInput.focus();
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const next = validateForm(form);
    setErrors(next);
    setFormError("");
    if (Object.keys(next).length) return focusFirstInvalid(form, next);
    const v = Object.fromEntries(new FormData(form)) as Record<string, string>;
    const email = v.email.toLowerCase();
    const clinician = email === DEMO_CLINICIAN_EMAIL;
    const patient = email === DEMO_PATIENT_EMAIL;
    if ((!clinician && !patient) || v.password !== DEMO_PASSWORD) {
      setFormError("Email atau password salah.");
      return;
    }
    try {
      if (v.remember) localStorage.setItem(REMEMBER_KEY, v.email);
      else localStorage.removeItem(REMEMBER_KEY);
    } catch {}
    router.push(clinician ? "/clinician/patients" : "/patient/home");
  }

  return (
    <>
      <form ref={formRef} noValidate onSubmit={submit} className="mt-7">
        <Field name="email" label="Email" type="email" required error={errors.email} className="mt-[18px]" />
        <Field
          name="password"
          label="Password"
          type="password"
          required
          autoComplete="current-password"
          error={errors.password}
          className="mt-[18px]"
        />
        <div className="flex items-center justify-between gap-3 mt-6 *:min-w-0">
          <label className="flex items-center gap-3">
            <input type="checkbox" name="remember" /> Ingat email saya
          </label>
          <button type="button" className={btn({ variant: "ghost", small: true })} onClick={() => openModal("forgot")}>
            Lupa password?
          </button>
        </div>
        <div role="alert">{formError && <Notice type="error" small>{formError}</Notice>}</div>
        <button type="submit" className={cn(btn({ variant: "primary", full: true }), "mt-6")}>
          Masuk <Icon icon={ArrowRight} />
        </button>
      </form>
      <p className={cn("text-center mt-6", authMuted)}>
        Belum memiliki akun? <Link href="/signup">Daftar akun</Link>
      </p>
      <details open className="border-t border-line mt-[30px] pt-[18px]">
        <summary className="text-[12px] text-muted cursor-pointer">Jelajahi dengan akun demo</summary>
        <p className="text-[12px] mt-3.5 mb-2">
          Pilih akun untuk mengisi form. Password: <b>{DEMO_PASSWORD}</b>
        </p>
        <div className="flex flex-wrap items-center gap-3">
          <button type="button" className={btn({ small: true })} onClick={() => fill(DEMO_PATIENT_EMAIL)}>
            Demo pasien
          </button>
          <button type="button" className={btn({ small: true })} onClick={() => fill(DEMO_CLINICIAN_EMAIL)}>
            Demo tenaga medis
          </button>
        </div>
      </details>
    </>
  );
}
