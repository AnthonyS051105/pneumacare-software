"use client";

import Image from "next/image";
import Link from "next/link";
import { useState, type FormEvent, type ReactNode } from "react";
import vestCard from "@/assets/vest-card.png";
import { useFeedback } from "@/components/providers/Feedback";
import { usePatientData } from "@/components/providers/PatientData";
import { formGrid, stack } from "@/components/portal/layout";
import { Field } from "@/components/ui/Field";
import { ArrowRight, BatteryMedium, Icon, LinkIcon, LogOut, Save, Wifi } from "@/components/ui/Icon";
import { Avatar, btn, card, cardPad, cn, Notice, Pill } from "@/components/ui/primitives";
import { ApiError } from "@/lib/api";
import {
  fetchClinicianProfile,
  updateClinicianProfile,
  type ClinicianProfile,
} from "@/lib/clinicianApi";
import { updatePatientProfile, type PatientProfile } from "@/lib/patientApi";
import { CLINICIAN_PROFILE_EVENT } from "@/lib/clinicianPatients";
import { useApi } from "@/lib/useApi";
import { focusFirstInvalid, validateForm, type FieldErrors } from "@/lib/validation";

type Role = "patient" | "clinician";

export function ProfileView({ role }: { role: Role }) {
  return role === "patient" ? <PatientProfileView /> : <ClinicianProfileView />;
}

function ClinicianProfileView() {
  const state = useApi(fetchClinicianProfile, "clinician-profile");
  if (state.status === "loading")
    return (
      <p role="status" className="py-16 text-center text-muted text-[13px]">
        Memuat profil…
      </p>
    );
  if (state.status === "error")
    return (
      <div role="alert">
        <Notice type="error">{state.message}</Notice>
        <button type="button" className={cn(btn({ small: true }), "mt-3")} onClick={state.reload}>
          Coba lagi
        </button>
      </div>
    );
  const person = state.data;
  return (
    <ProfileShell
      clinician
      name={person.full_name}
      email={person.email}
      form={
        <ClinicianIdentityForm
          key={JSON.stringify(person)}
          person={person}
          onSaved={(next) => state.setData(() => next)}
        />
      }
      side={
        <aside className={stack}>
          <section className={cn(card, cardPad)}>
            <h3>Status identitas</h3>
            <div className="mt-6">
              <Pill tone="warn">Belum diverifikasi</Pill>
            </div>
            <p className="text-[11px] text-muted mt-3.5">
              Nomor STR/SIP disimpan sebagai informasi dan tidak diverifikasi ke sistem eksternal.
            </p>
          </section>
          <section className={cn(card, cardPad)}>
            <h3>Pasien dalam pemantauan</h3>
            <p className="text-muted mt-6">Tinjau kondisi dan riwayat pasien Anda.</p>
            <Link href="/clinician/patients" className={cn(btn(), "mt-6")}>
              Lihat pasien <Icon icon={ArrowRight} />
            </Link>
          </section>
        </aside>
      }
      password={<PasswordForm role="clinician" />}
    />
  );
}

function PatientProfileView() {
  const { profile } = usePatientData();
  const { openModal } = useFeedback();
  return (
    <ProfileShell
      name={profile.full_name}
      email={profile.email}
      form={<PatientIdentityForm key={`${profile.full_name}|${profile.date_of_birth}`} profile={profile} />}
      side={<PatientSide profile={profile} onPair={() => openModal("pair")} />}
      password={<PasswordForm role="patient" />}
    />
  );
}

function ProfileShell({
  clinician = false,
  name,
  email,
  form,
  side,
  password,
}: {
  clinician?: boolean;
  name: string;
  email: string;
  form: ReactNode;
  side: ReactNode;
  password: ReactNode;
}) {
  const { openModal } = useFeedback();
  return (
    <div className="grid grid-cols-[minmax(0,1.5fr)_minmax(280px,1fr)] gap-[22px] items-start max-2xl:grid-cols-[1fr]">
      <section className={cn(card, cardPad)}>
        <div className="flex flex-wrap items-center gap-4 pb-[22px] border-b border-line mb-6 max-md:gap-3">
          <Avatar name={name} size="lg" clinical={clinician} />
          <div>
            <h2 className="text-[21px]">{name}</h2>
            <p className="text-muted text-[12px] [overflow-wrap:anywhere]">
              {clinician ? "Tenaga medis" : "Pasien"}, {email}
            </p>
          </div>
        </div>
        <h3 className="mb-5">Informasi {clinician ? "profesional" : "pribadi"}</h3>
        {form}
      </section>

      {side}

      <section className={cn(card, cardPad, "col-span-full max-2xl:col-auto")}>
        <h3 className="mb-5">Keamanan akun</h3>
        {password}
      </section>
      <div>
        <button type="button" className={btn({ variant: "danger" })} onClick={() => openModal("logout")}>
          <Icon icon={LogOut} />
          Keluar dari akun
        </button>
      </div>
    </div>
  );
}

function PatientIdentityForm({ profile }: { profile: PatientProfile }) {
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const { toast } = useFeedback();
  const { reload } = usePatientData();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    const form = event.currentTarget;
    const next = validateForm(form);
    setErrors(next);
    setFormError("");
    if (Object.keys(next).length) return focusFirstInvalid(form, next);
    const v = Object.fromEntries(new FormData(form)) as Record<string, string>;
    setSaving(true);
    try {
      await updatePatientProfile({ full_name: v.name.trim(), date_of_birth: v.dob || null });
      await reload();
      toast("Perubahan profil berhasil disimpan.");
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Tidak dapat terhubung ke server.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form noValidate onSubmit={submit}>
      <div className={formGrid}>
        <Field name="name" label="Nama lengkap" defaultValue={profile.full_name} required error={errors.name} />
        <Field
          name="email"
          label="Email"
          type="email"
          defaultValue={profile.email}
          readOnly
          hint="Email tidak dapat diubah."
        />
        <Field name="dob" label="Tanggal lahir" type="date" defaultValue={profile.date_of_birth ?? ""} />
      </div>
      <div role="alert">{formError && <Notice type="error">{formError}</Notice>}</div>
      <button type="submit" disabled={saving} className={cn(btn({ variant: "primary" }), "mt-6")}>
        <Icon icon={Save} />
        {saving ? "Menyimpan…" : "Simpan perubahan"}
      </button>
    </form>
  );
}

function ClinicianIdentityForm({
  person,
  onSaved,
}: {
  person: ClinicianProfile;
  onSaved: (next: ClinicianProfile) => void;
}) {
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const { toast } = useFeedback();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    const form = event.currentTarget;
    const next = validateForm(form);
    setErrors(next);
    setFormError("");
    if (Object.keys(next).length) return focusFirstInvalid(form, next);
    const v = Object.fromEntries(new FormData(form)) as Record<string, string>;
    setSaving(true);
    try {
      const saved = await updateClinicianProfile({
        full_name: v.name.trim(),
        specialization: v.specialty.trim() || null,
        institution: v.institution.trim() || null,
        str_sip_number: v.str.trim() || null,
      });
      onSaved(saved);
      window.dispatchEvent(new Event(CLINICIAN_PROFILE_EVENT));
      toast("Perubahan profil berhasil disimpan.");
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : "Tidak dapat terhubung ke server.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form noValidate onSubmit={submit}>
      <div className={formGrid}>
        <Field name="name" label="Nama lengkap" defaultValue={person.full_name} required error={errors.name} />
        <Field name="email" label="Email" type="email" defaultValue={person.email} readOnly hint="Email tidak dapat diubah." />
        <Field name="specialty" label="Spesialisasi" defaultValue={person.specialization ?? ""} />
        <Field name="institution" label="Institusi" defaultValue={person.institution ?? ""} />
        <Field name="str" label="Nomor STR / SIP (opsional)" defaultValue={person.str_sip_number ?? ""} />
      </div>
      <div role="alert">{formError && <Notice type="error">{formError}</Notice>}</div>
      <button type="submit" disabled={saving} className={cn(btn({ variant: "primary" }), "mt-6")}>
        <Icon icon={Save} />
        {saving ? "Menyimpan…" : "Simpan perubahan"}
      </button>
    </form>
  );
}

function PasswordForm({ role }: { role: Role }) {
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const { toast } = useFeedback();

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    const form = event.currentTarget;
    let next = validateForm(form);
    const v = Object.fromEntries(new FormData(form)) as Record<string, string>;
    setFormError("");
    if (!Object.keys(next).length) {
      if (v.newpassword.length < 8) next = { newpassword: "Password baru minimal 8 karakter." };
      else if (v.newpassword !== v.confirm) next = { confirm: "Konfirmasi password tidak sesuai." };
    }
    setErrors(next);
    if (Object.keys(next).length) return focusFirstInvalid(form, next);

    setSaving(true);
    try {
      const passwords = { current_password: v.current, new_password: v.newpassword };
      if (role === "clinician") await updateClinicianProfile(passwords);
      else await updatePatientProfile(passwords);
      form.reset();
      toast("Password berhasil diubah.");
    } catch (error) {
      if (error instanceof ApiError && error.status === 400 && /current_password/.test(error.message)) {
        setFormError("Password saat ini tidak sesuai.");
      } else {
        setFormError(error instanceof ApiError ? error.message : "Tidak dapat terhubung ke server.");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <form noValidate onSubmit={submit}>
      <div className={formGrid}>
        <Field name="current" label="Password saat ini" type="password" required error={errors.current} />
        <Field
          name="newpassword"
          label="Password baru"
          type="password"
          hint="Minimal 8 karakter"
          required
          error={errors.newpassword}
        />
        <Field name="confirm" label="Konfirmasi password baru" type="password" required error={errors.confirm} />
      </div>
      <div role="alert">{formError && <Notice type="error">{formError}</Notice>}</div>
      <button type="submit" disabled={saving} className={cn(btn(), "mt-6")}>
        {saving ? "Menyimpan…" : "Ubah password"}
      </button>
    </form>
  );
}

function PatientSide({ profile, onPair }: { profile: PatientProfile; onPair: () => void }) {
  const { device, clinician } = profile;
  const online = device?.status === "online";
  const battery = device?.battery_percent != null ? Math.round(device.battery_percent) : null;
  return (
    <aside className={stack}>
      <section
        aria-labelledby="device-title"
        className={cn(card, "p-[22px] md:max-xl:p-[18px] max-md:p-5 max-xxs:p-[17px]")}
      >
        <div className="flex flex-wrap items-center justify-between gap-3 *:min-w-0">
          <h3 id="device-title">Perangkat saya</h3>
          <Pill tone={online ? "" : "off"}>{!device ? "Belum terhubung" : online ? "Terhubung" : "Offline"}</Pill>
        </div>
        <div className="grid grid-cols-[minmax(0,122px)_minmax(0,1fr)] gap-5 items-center my-5 md:max-xl:grid-cols-[88px_minmax(0,1fr)] md:max-xl:gap-3 max-md:grid-cols-[104px_minmax(0,1fr)] max-xxs:grid-cols-[88px_minmax(0,1fr)] max-xxs:gap-[15px]">
          <div className="aspect-square bg-mint rounded-[14px] p-2 grid place-items-center">
            <Image
              src={vestCard}
              alt="Ilustrasi rompi pemantauan PNEUMACARE"
              sizes="122px"
              className="w-full h-full object-contain"
            />
          </div>
          <div className="min-w-0">
            <small className="block text-[11px] text-[#687e82] leading-[1.5]">Rompi pemantauan</small>
            <h4 className="text-[24px] tracking-[-.7px] leading-[1.25] mt-[5px] md:max-xl:text-[22px] [overflow-wrap:anywhere]">
              {device?.device_id ?? "Belum ada rompi"}
            </h4>
            {device && (
              <span className={cn("flex items-center gap-1.5 text-[11px] leading-[1.5] mt-[9px]", online ? "text-teal" : "text-muted")}>
                <Icon icon={Wifi} className="size-[15px]" />
                {online ? "Koneksi aktif" : "Koneksi terputus"}
              </span>
            )}
          </div>
        </div>
        {device && (
          <div className="pt-[15px] pb-[19px] border-t border-line">
            <div className="flex items-center justify-between gap-3 text-[12px] *:min-w-0">
              <span className="flex items-center gap-3">
                <Icon icon={BatteryMedium} className="size-[17px] text-teal" />
                Baterai
              </span>
              <strong className="text-[13px] font-semibold">{battery !== null ? `${battery}%` : "—"}</strong>
            </div>
            {battery !== null && (
              <div
                role="meter"
                aria-label="Baterai perangkat"
                aria-valuemin={0}
                aria-valuemax={100}
                aria-valuenow={battery}
                className="h-[5px] mt-3 rounded-[4px] bg-[#e5eeeb] overflow-hidden"
              >
                <span className="block h-full rounded-[inherit] bg-[#398c80]" style={{ width: `${battery}%` }} />
              </div>
            )}
          </div>
        )}
        <button
          type="button"
          onClick={onPair}
          className="inline-flex items-center justify-center gap-[9px] w-full min-h-11 px-3 py-2 rounded-[8px] border border-line bg-white text-navy font-semibold text-[12px] leading-[1.4] transition-[background,border-color] duration-180 ease-[ease] hover:bg-[#edf7f3] hover:border-[#9caea4]"
        >
          <Icon icon={LinkIcon} />
          {device ? "Hubungkan ulang" : "Hubungkan rompi"}
        </button>
      </section>
      <section className={cn(card, cardPad)}>
        <h3 className="mb-5">Tenaga medis pendamping</h3>
        {clinician ? (
          <div className="flex items-center gap-3 *:min-w-0">
            <Avatar name={clinician.full_name} clinical />
            <div>
              <h4>{clinician.full_name}</h4>
              <small>{[clinician.specialization, clinician.institution].filter(Boolean).join(" · ")}</small>
            </div>
          </div>
        ) : (
          <p className="text-muted">Belum ada tenaga medis pendamping.</p>
        )}
        <p className="text-[11px] text-muted mt-3.5">Penugasan dikelola oleh pengelola layanan.</p>
      </section>
    </aside>
  );
}
