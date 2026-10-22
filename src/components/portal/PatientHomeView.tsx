"use client";

import Image from "next/image";
import Link from "next/link";
import carePatient from "@/assets/care-patient.png";
import { AlertItem } from "@/components/portal/AlertItem";
import { Connection } from "@/components/portal/Connection";
import { notificationsCard, stack, split } from "@/components/portal/layout";
import { Metric, metricsGrid } from "@/components/portal/Metric";
import { CareTeamPanel, VitalSwitcherCard } from "@/components/portal/PatientHomeWidgets";
import { Topbar } from "@/components/portal/Shell";
import { usePatientData } from "@/components/providers/PatientData";
import { ArrowRight, Bell, Check, CircleAlert, Icon, Info, TriangleAlert } from "@/components/ui/Icon";
import { cn, Empty } from "@/components/ui/primitives";
import { vitalKeys } from "@/lib/demo-data";
import { formatClockWib, parseApiDate } from "@/lib/format";
import { toAlertView } from "@/lib/patientAlerts";
import type { PatientSummary } from "@/lib/patientApi";
import { usePatientHistory } from "@/lib/usePatientHistory";
import { BUCKET_MS, GAP_BUCKETS, RANGE_MS, seriesFor } from "@/lib/vitals";



// Teks status memakai bahasa awam (FR-SW-065) dan sengaja tidak menyiratkan diagnosis.
const STATUS: Record<PatientSummary["status_label"], { title: string; text: string; tone: string; icon: typeof Check; iconTone: string }> = {
  stable: {
    title: "Tidak ada peringatan aktif",
    text: "Pembacaan terbaru Anda tersaji di bawah ini.",
    tone: "bg-[#e8f5f0] border-[#d7eae3] text-[#466554]",
    icon: Check,
    iconTone: "bg-primary text-white",
  },
  attention: {
    title: "Ada pemberitahuan yang perlu diperhatikan",
    text: "Tinjau notifikasi terbaru Anda di bawah ini.",
    tone: "bg-[#faf2e0] border-[#ece0c5] text-[#805c21]",
    icon: TriangleAlert,
    iconTone: "bg-amber text-white",
  },
  urgent: {
    title: "Segera hubungi tenaga medis Anda",
    text: "Ada pemberitahuan penting yang belum ditinjau. Ikuti arahan tenaga medis Anda.",
    tone: "bg-[#fae9e6] border-[#eacdc9] text-red",
    icon: CircleAlert,
    iconTone: "bg-red text-white",
  },
};

const NO_DATA: (typeof STATUS)[PatientSummary["status_label"]] = {
  title: "Belum ada data pemantauan",
  text: "Pastikan rompi Anda terpasang dan terhubung.",
  tone: "bg-[#edf2ee] border-[#dce5de] text-[#476355]",
  icon: Info,
  iconTone: "bg-[#87a18e] text-white",
};

export function PatientHomeView() {
  const { summary, profile, alerts } = usePatientData();
  const history = usePatientHistory("24h");
  const latest = summary.latest_vitals;
  const updatedAt = latest.timestamp ? formatClockWib(parseApiDate(latest.timestamp)) : null;
  // Tanpa data sama sekali, "tidak ada peringatan" bukan kabar baik — jangan tampil sebagai centang hijau.
  const status = summary.status_label === "stable" && !updatedAt ? NO_DATA : STATUS[summary.status_label];
  const ready = history.status === "ready" ? history : null;
  const domain: [number, number] | undefined = ready ? [ready.asOf - RANGE_MS["24h"], ready.asOf] : undefined;
  const recent = alerts.slice(0, 2).map((a) => toAlertView(a));

  return (
    <>
      <Topbar role="patient" greeting subtitle="Pantau kondisi Anda dan lanjutkan hari dengan lebih tenang." />
      <div className={stack}>
        <section className={cn("flex items-center gap-[13px] border rounded-[6px] px-5 py-4 max-md:p-3.5 max-md:gap-2.5", status.tone)}>
          <div className={cn("grid place-items-center size-7 rounded-full shrink-0 max-md:hidden", status.iconTone)}>
            <Icon icon={status.icon} className="size-[17px]" />
          </div>
          <div className="max-md:min-w-0 max-md:flex-1">
            <h2 className="text-[16px] tracking-normal max-md:text-[14px] max-md:leading-[1.4] text-ink">{status.title}</h2>
            <p className="text-[12px] mt-0.5 max-md:text-[11px] max-md:leading-[1.6]">
              {status.text}
            </p>
          </div>
          {updatedAt && (
            <span className="ml-auto text-[12px] text-right max-2xl:hidden">
              Terakhir diperbarui
              <br />
              {updatedAt}
            </span>
          )}
          <div className="w-[120px] h-[84px] flex-[0_0_120px] overflow-hidden [mask-image:linear-gradient(to_right,transparent,#000_14%,#000_90%,transparent)] max-2xl:w-[98px] max-2xl:h-[76px] max-2xl:basis-[98px] max-md:w-[82px] max-md:h-[72px] max-md:basis-[82px] max-md:ml-auto">
            <Image
              src={carePatient}
              alt="Pasien melakukan pemantauan dari rumah"
              sizes="120px"
              className="w-full h-full object-contain"
            />
          </div>
        </section>
        <div className={metricsGrid}>
          {vitalKeys.map((k) => {
            const raw = latest[k];
            return (
              <Metric
                key={k}
                vital={k}
                unknown={raw === null}
                val={raw === null ? undefined : Math.round(raw)}
                updatedAt={updatedAt}
                points={ready ? seriesFor(ready.data.readings, k, "24h", (iso) => parseApiDate(iso).getTime()) : []}
                domain={domain}
                gapMs={BUCKET_MS["24h"] * GAP_BUCKETS}
              />
            );
          })}
        </div>
        <div className={split}>
          <VitalSwitcherCard history={history} />
          <CareTeamPanel clinician={profile.clinician} />
        </div>
        <section className={notificationsCard}>
          <div className="flex items-center justify-between gap-3 *:min-w-0 max-md:flex-wrap">
            <h3 className="max-md:text-[16px]">Notifikasi terbaru</h3>
            <Link href="/patient/alerts" className="flex items-center gap-3 max-md:text-[12px] max-md:gap-2 max-md:min-h-11">
              Lihat semua <Icon icon={ArrowRight} />
            </Link>
          </div>
          {recent.length ? (
            recent.map((a) => <AlertItem key={a.id} alert={a} />)
          ) : (
            <Empty icon={Bell} title="Belum ada notifikasi" text="Pemberitahuan pemantauan Anda akan muncul di sini." />
          )}
        </section>
        <div className="mt-1">
          <Connection device={summary.device} />
        </div>
      </div>
    </>
  );
}
