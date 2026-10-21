"use client";

import Image from "next/image";
import Link from "next/link";
import { useState, type FormEvent } from "react";
import vestCard from "@/assets/vest-card.png";
import { useFeedback } from "@/components/providers/Feedback";
import { formGrid, stack } from "@/components/portal/layout";
import { Field } from "@/components/ui/Field";
import { ArrowRight, BatteryMedium, Icon, LinkIcon, LogOut, Save, Wifi } from "@/components/ui/Icon";
import { Avatar, btn, card, cardPad, cn, Notice, Pill } from "@/components/ui/primitives";
import { DEMO_PASSWORD } from "@/lib/demo-data";
import { updateDemo, useDemo, type DemoData } from "@/lib/demo-store";
import { focusFirstInvalid, validateForm, type FieldErrors } from "@/lib/validation";

type Role = "patient" | "clinician";

export function ProfileView({ role }: { role: Role }) {
  const clinician = role === "clinician";
  const person = useDemo((d) => (clinician ? d.clinician : d.patient));
  const { openModal } = useFeedback();

  return (
    <div className="grid grid-cols-[minmax(0,1.5fr)_minmax(280px,1fr)] gap-[22px] items-start max-2xl:grid-cols-[1fr]">
      <section className={cn(card, cardPad)}>
        <div className="flex flex-wrap items-center gap-4 pb-[22px] border-b border-line mb-6 max-md:gap-3">
          <Avatar name={person.name} size="lg" clinical={clinician} />
          <div>
            <h2 className="text-[21px]">{person.name}</h2>
            <p className="text-muted text-[12px] [overflow-wrap:anywhere]">
              {clinician ? "Tenaga medis" : "Pasien"}, {person.email}
            </p>
          </div>
        </div>
        <h3 className="mb-5">Informasi {clinician ? "profesional" : "pribadi"}</h3>
        <IdentityForm key={JSON.stringify(person)} role={role} person={person} />
      </section>

      {clinician ? (
        <aside className={stack}>
          <section className={cn(card, cardPad)}>
            <h3>Status identitas</h3>
            <div className="mt-6">
              <Pill tone="warn">Belum diverifikasi</Pill>
            </div>
          </section>
          <section className={cn(card, cardPad)}>
            <h3>Pasien dalam pemantauan</h3>
            <p className="text-muted mt-6">Tinjau kondisi dan riwayat pasien Anda.</p>
            <Link href="/clinician/patients" className={cn(btn(), "mt-6")}>
              Lihat pasien <Icon icon={ArrowRight} />
            </Link>
          </section>
        </aside>
      ) : (
        <PatientSide onPair={() => openModal("pair")} />
      )}

      <section className={cn(card, cardPad, "col-span-full max-2xl:col-auto")}>
        <h3 className="mb-5">Keamanan akun</h3>
        <PasswordForm />
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

function IdentityForm({
  role,
  person,
}: {
  role: Role;
  person: DemoData["patient"] | DemoData["clinician"];
}) {
  const [errors, setErrors] = useState<FieldErrors>({});
  const { toast } = useFeedback();

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const next = validateForm(form);
    setErrors(next);
    if (Object.keys(next).length) return focusFirstInvalid(form, next);
    const values = Object.fromEntries(new FormData(form)) as Record<string, string>;
    updateDemo((d) => ({ ...d, [role]: { ...d[role], ...values } }));
    toast("Perubahan profil berhasil disimpan.");
  }

  return (
    <form noValidate onSubmit={submit}>
      <div className={formGrid}>
        <Field name="name" label="Nama lengkap" defaultValue={person.name} required error={errors.name} />
        <Field name="email" label="Email" type="email" defaultValue={person.email} required error={errors.email} />
        {"specialty" in person ? (
          <>
            <Field name="specialty" label="Spesialisasi" defaultValue={person.specialty} />
            <Field name="institution" label="Institusi" defaultValue={person.institution} />
            <Field name="str" label="Nomor STR / SIP (opsional)" defaultValue={person.str} />
          </>
        ) : (
          <Field name="dob" label="Tanggal lahir" type="date" defaultValue={person.dob} />
        )}
      </div>
      <button type="submit" className={cn(btn({ variant: "primary" }), "mt-6")}>
        <Icon icon={Save} />
        Simpan perubahan
      </button>
    </form>
  );
}

function PasswordForm() {
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");
  const { toast } = useFeedback();

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    let next = validateForm(form);
    const v = Object.fromEntries(new FormData(form)) as Record<string, string>;
    setFormError("");
    if (!Object.keys(next).length) {
      if (v.current !== DEMO_PASSWORD) {
        setErrors({});
        setFormError("Password saat ini tidak sesuai.");
        return;
      }
      if (v.newpassword !== v.confirm) next = { confirm: "Konfirmasi password tidak sesuai." };
    }
    setErrors(next);
    if (Object.keys(next).length) return focusFirstInvalid(form, next);
    form.reset();
    toast("Perubahan password belum tersedia.");
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
      <button type="submit" className={cn(btn(), "mt-6")}>
        Ubah password
      </button>
    </form>
  );
}

function PatientSide({ onPair }: { onPair: () => void }) {
  const clinicianName = useDemo((d) => d.clinician.name);
  return (
    <aside className={stack}>
      <section
        aria-labelledby="device-title"
        className={cn(card, "p-[22px] md:max-xl:p-[18px] max-md:p-5 max-xxs:p-[17px]")}
      >
        <div className="flex flex-wrap items-center justify-between gap-3 *:min-w-0">
          <h3 id="device-title">Perangkat saya</h3>
          <Pill>Terhubung</Pill>
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
            <h4 className="text-[24px] tracking-[-.7px] leading-[1.25] mt-[5px] md:max-xl:text-[22px]">PC-001</h4>
            <span className="flex items-center gap-1.5 text-[11px] leading-[1.5] text-teal mt-[9px]">
              <Icon icon={Wifi} className="size-[15px]" />
              Koneksi aktif
            </span>
          </div>
        </div>
        <div className="pt-[15px] pb-[19px] border-t border-line">
          <div className="flex items-center justify-between gap-3 text-[12px] *:min-w-0">
            <span className="flex items-center gap-3">
              <Icon icon={BatteryMedium} className="size-[17px] text-teal" />
              Baterai
            </span>
            <strong className="text-[13px] font-semibold">78%</strong>
          </div>
          <div
            role="meter"
            aria-label="Baterai perangkat"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={78}
            className="h-[5px] mt-3 rounded-[4px] bg-[#e5eeeb] overflow-hidden"
          >
            <span className="block h-full rounded-[inherit] bg-[#398c80] w-[78%]" />
          </div>
        </div>
        <button
          type="button"
          onClick={onPair}
          className="inline-flex items-center justify-center gap-[9px] w-full min-h-11 px-3 py-2 rounded-[8px] border border-line bg-white text-navy font-semibold text-[12px] leading-[1.4] transition-[background,border-color] duration-180 ease-[ease] hover:bg-[#edf7f3] hover:border-[#9caea4]"
        >
          <Icon icon={LinkIcon} />
          Hubungkan ulang
        </button>
      </section>
      <section className={cn(card, cardPad)}>
        <h3 className="mb-5">Tenaga medis pendamping</h3>
        <div className="flex items-center gap-3 *:min-w-0">
          <Avatar name={clinicianName} clinical />
          <div>
            <h4>{clinicianName}</h4>
            <small>RS Akademik UGM</small>
          </div>
        </div>
        <p className="text-[11px] text-muted mt-3.5">Penugasan dikelola oleh pengelola layanan.</p>
      </section>
    </aside>
  );
}
