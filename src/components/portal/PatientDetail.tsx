"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type FormEvent } from "react";
import { useFeedback } from "@/components/providers/Feedback";
import { AlertItem } from "@/components/portal/AlertItem";
import { connectionBar } from "@/components/portal/Connection";
import { chartGrid, formGrid, split, stack } from "@/components/portal/layout";
import { Metric, metricsGrid } from "@/components/portal/Metric";
import { Field, inputClass } from "@/components/ui/Field";
import {
  ArrowLeft,
  AudioLines,
  BatteryMedium,
  Bell,
  CircleHelp,
  Clock3,
  Icon,
  Save,
  Signal,
} from "@/components/ui/Icon";
import { Avatar, btn, card, cardPad, cn, Empty, LegendItem, Notice, Pill } from "@/components/ui/primitives";
import { VitalChart } from "@/components/ui/VitalChart";
import { alerts, patients, values, vitalKeys, type Patient } from "@/lib/demo-data";
import { updateDemo, useDemo } from "@/lib/demo-store";
import { detailHref, type DetailTab } from "@/lib/routes";
import { thresholdErrors, thresholdKeys, type FieldErrors } from "@/lib/validation";

/** Cari pasien fixture atau pasien tambahan (localStorage); fallback seperti referensi. */
export function usePatient(id: string): Patient {
  const extra = useDemo((d) => d.extra);
  return [...patients, ...extra].find((p) => p.id === id) ?? patients[2];
}

const TABS: [DetailTab, string][] = [
  ["vitals", "Vital Real-time"],
  ["trends", "Tren & Severity"],
  ["alerts", "Riwayat Alert"],
  ["thresholds", "Konfigurasi Ambang"],
];

export function DetailHeader({ id }: { id: string }) {
  const p = usePatient(id);
  const pathname = usePathname();
  return (
    <>
      <Link href="/clinician/patients" className="flex items-center gap-3 text-muted mb-5">
        <Icon icon={ArrowLeft} /> Kembali ke daftar pasien
      </Link>
      <div className={cn(card, "flex flex-wrap items-center gap-4 p-[22px] max-md:gap-3")}>
        <div className="flex items-center gap-3 *:min-w-0 max-md:flex-wrap">
          <Avatar name={p.name} size="lg" />
          <div>
            <h2 className="text-[21px]">{p.name}</h2>
            <p className="text-muted text-[12px] [overflow-wrap:anywhere]">
              {p.age ? p.age + " tahun" : "Usia belum tersedia"}, ID pasien: {p.id.toUpperCase()} ({p.device})
            </p>
          </div>
        </div>
        <div className="ml-auto max-md:ml-0">
          <Pill tone={p.online ? "" : "off"} className="mt-2">
            {p.online ? "Perangkat terhubung" : "Perangkat offline"}
          </Pill>
          <p className="text-[12px]">
            <small>Terakhir diperbarui {p.online ? "09.30" : "09.10"} WIB</small>
          </p>
        </div>
      </div>
      <nav
        aria-label="Detail pasien"
        className="flex gap-7 mt-5 mb-6 border-b border-line overflow-x-auto max-md:gap-[22px] max-md:my-5"
      >
        {TABS.map(([tab, label]) => {
          const href = detailHref(p.id, tab);
          const active = pathname === href;
          return (
            <Link
              key={tab}
              href={href}
              className={cn(
                "whitespace-nowrap px-0.5 py-3 border-b-2 text-[13px] max-md:text-[12px] max-md:py-[11px] max-md:min-h-11",
                active ? "border-primary text-navy font-semibold" : "border-transparent text-muted font-medium",
              )}
            >
              {label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}

export function VitalsTab({ id }: { id: string }) {
  const p = usePatient(id);
  return (
    <div className={stack}>
      {!p.online && (
        <Notice type="warn">
          Perangkat offline. Kondisi terkini belum diketahui. Nilai terakhir tidak ditampilkan sebagai pembacaan
          terkini.
        </Notice>
      )}
      <div className={metricsGrid}>
        {vitalKeys.map((k) => (
          <Metric key={k} vital={k} clinical unknown={!p.online} val={p[k]} />
        ))}
      </div>
      <div className={chartGrid}>
        {vitalKeys.map((k) => (
          <div key={k} className={cn(card, cardPad)}>
            <div className="flex items-center justify-between gap-3 mb-5 *:min-w-0">
              <h3>{values[k].technical}</h3>
            </div>
            <VitalChart vital={k} offline={!p.online} center={p[k] ?? undefined} />
          </div>
        ))}
        <div className={cn(card, cardPad)}>
          <h3 className="mb-5">Kualitas Sinyal PPG</h3>
          <VitalChart vital="hr" wave offline={!p.online} />
          <div className="flex items-center justify-between gap-3 *:min-w-0">
            <span className="text-muted">{p.online ? "Kualitas sinyal: baik" : "Sinyal tidak tersedia"}</span>
            <Pill>PPG</Pill>
          </div>
        </div>
      </div>
      <div className={connectionBar}>
        <Icon icon={BatteryMedium} className="size-[17px] max-md:size-4" />
        {"Baterai 78% "}
        <Icon icon={Signal} className="size-[17px] max-md:size-4" />
        Sinyal {p.online ? "baik " : "tidak tersedia "}
        <Icon icon={Clock3} className="size-[17px] max-md:size-4" />
        Pembaruan {p.online ? "09.30" : "09.10"} WIB
      </div>
    </div>
  );
}

const ring =
  "grid place-items-center size-[95px] rounded-full my-[18px] mx-auto before:content-[''] before:size-[78px] before:bg-white before:rounded-full before:[grid-area:1/1]";

export function TrendsTab() {
  return (
    <div className={stack}>
      <Notice>Hasil skrining memerlukan peninjauan tenaga medis.</Notice>
      <div className={split}>
        <div className={cn(card, cardPad)}>
          <h3>Analisis Suara Paru</h3>
          <p className="text-muted">Empat kanal posterior</p>
          <div className="grid min-w-0 grid-cols-4 gap-3 mt-6 max-2xl:grid-cols-2 max-md:grid-cols-[1fr_1fr] max-md:gap-4">
            {["Posterior kiri atas", "Posterior kanan atas", "Posterior kiri bawah", "Posterior kanan bawah"].map((t) => (
              <div key={t} className="border-b border-line py-4 px-1 text-center text-[11px]">
                <Icon icon={AudioLines} className="text-primary mb-2" />
                <br />
                {t}
                <br />
                <small>Sinyal paru</small>
              </div>
            ))}
          </div>
          <div className="grid grid-cols-[1fr_1fr] gap-0 mt-6 border-t border-line pt-[22px]">
            <div className="text-center px-[15px] py-1">
              <h4>Wheeze</h4>
              <div className={ring} style={{ background: "conic-gradient(var(--color-primary) 0 82%,#e4eeea 82%)" }}>
                <strong className="[grid-area:1/1] text-[23px] z-[1]">82%</strong>
              </div>
              <small>Confidence</small>
            </div>
            <div className="text-center px-[15px] py-1 border-l border-line">
              <h4>Crackle</h4>
              <div className={ring} style={{ background: "conic-gradient(var(--color-blue) 0 61%,#e4ebe2 61%)" }}>
                <strong className="[grid-area:1/1] text-[23px] z-[1]">61%</strong>
              </div>
              <small>Confidence</small>
            </div>
          </div>
          <p className="text-[11px] text-muted mt-3.5">
            Confidence bukan peluang diagnosis. Interpretasi membutuhkan peninjauan tenaga medis.
          </p>
        </div>
        <div className={cn(card, cardPad)}>
          <h3>Severity Skrining</h3>
          <Empty
            icon={CircleHelp}
            title="Belum ada hasil skrining"
            text="Hasil severity akan ditampilkan setelah tersedia."
            action={<Pill tone="off">Belum tersedia</Pill>}
          />
        </div>
      </div>
      <div className={cn(card, cardPad)}>
        <div className="flex items-center justify-between gap-3 mb-5 *:min-w-0">
          <div>
            <h3>Tren Frekuensi Napas</h3>
            <small>7 hari terakhir</small>
          </div>
          <Pill>7 hari</Pill>
        </div>
        <VitalChart vital="rr" trend />
        <div className="flex flex-wrap gap-[18px] mt-3 text-[11px] text-muted">
          <LegendItem>Data frekuensi napas</LegendItem>
          <LegendItem>Garis tren</LegendItem>
        </div>
      </div>
    </div>
  );
}

export function AlertsTab({ id }: { id: string }) {
  const p = usePatient(id);
  const list = alerts.filter((a) => a.patient === p.id);
  return (
    <>
      <Notice>Acknowledge menandai alert sudah ditinjau. Tindakan ini tidak berarti kondisi pasien telah pulih.</Notice>
      <div className={cn(card, cardPad, "mt-6")}>
        <div className="flex items-center justify-between gap-3 mb-5 *:min-w-0">
          <h3>Riwayat Alert Pasien</h3>
        </div>
        {list.length ? (
          list.map((a) => <AlertItem key={a.id} alert={a} clinical />)
        ) : (
          <Empty icon={Bell} title="Belum ada alert" text="Alert pasien akan ditampilkan di sini." />
        )}
      </div>
    </>
  );
}

// TODO_CLINICAL_VALUE: ambang HR/SpO₂/RR sengaja tidak diberi nilai default — wajib diisi
// tenaga medis sesuai rencana pemantauan (lihat CLAUDE.md, larangan mengisi angka klinis).
export function ThresholdsTab({ id }: { id: string }) {
  const p = usePatient(id);
  const saved = useDemo((d) => d.thresholds?.[p.id]);
  return <ThresholdsForm key={p.id + JSON.stringify(saved ?? {})} patientId={p.id} saved={saved ?? {}} />;
}

function ThresholdsForm({ patientId, saved }: { patientId: string; saved: Record<string, string> }) {
  const { toast } = useFeedback();
  const [errors, setErrors] = useState<FieldErrors>({});
  const [valid, setValid] = useState(() => thresholdErrors(saved) === null);
  const read = (form: HTMLFormElement) => Object.fromEntries(new FormData(form)) as Record<string, string>;

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const v = read(event.currentTarget);
    const next = thresholdErrors(v);
    if (next) return setErrors(next);
    setErrors({});
    updateDemo((d) => ({ ...d, thresholds: { ...d.thresholds, [patientId]: v } }));
    toast("Konfigurasi berhasil disimpan.");
  }

  const num = (name: (typeof thresholdKeys)[number], label: string, hint?: string) => (
    <Field name={name} label={label} type="number" defaultValue={saved[name]} hint={hint} required error={errors[name]} />
  );

  return (
    <div className={stack}>
      <section className={cn(card, cardPad)}>
        <h3 className="mb-5">Konfigurasi Ambang Vital</h3>
        <form noValidate onSubmit={submit} onInput={(e) => setValid(thresholdErrors(read(e.currentTarget)) === null)}>
          <div className={formGrid}>
            {num("hrmin", "HR minimum (bpm)", "Isi sesuai rencana pemantauan")}
            {num("hrmax", "HR maksimum (bpm)", "Harus lebih besar dari minimum")}
            {num("spo2min", "SpO₂ batas bawah (%)", "Nilai 1–100")}
            <div />
            {num("rrmin", "RR minimum (napas/menit)")}
            {num("rrmax", "RR maksimum (napas/menit)", "Harus lebih besar dari minimum")}
          </div>
          <h3 className="mt-6 mb-5">Rencana Tindakan Pasien</h3>
          <div className="block min-w-0">
            <label htmlFor="actionplan" className="block font-medium text-[12px] mb-[7px]">
              Arahan tenaga medis
            </label>
            <textarea
              id="actionplan"
              name="actionplan"
              defaultValue={saved.actionplan}
              placeholder="Tulis rencana tindakan individual pasien..."
              className={cn(inputClass, "min-h-[115px] resize-y")}
            />
          </div>
          <div role="alert" />
          <button type="submit" disabled={!valid} className={cn(btn({ variant: "primary" }), "mt-6")}>
            <Icon icon={Save} />
            Simpan Konfigurasi
          </button>
          <p className="text-[11px] text-muted mt-[5px]">Lengkapi angka yang valid untuk mengaktifkan tombol simpan.</p>
        </form>
      </section>
    </div>
  );
}
