"use client";

import { useEffect, useState } from "react";
import { PatientSidebar } from "@/components/patient/PatientSidebar";
import { PatientTopBar } from "@/components/patient/PatientTopBar";
import { PatientBottomNav } from "@/components/patient/PatientBottomNav";
import { StatusHeroCard, type StatusLevel } from "@/components/patient/StatusHeroCard";
import { DeviceStatusStrip } from "@/components/patient/DeviceStatusStrip";
import { VitalSummaryCard } from "@/components/patient/VitalSummaryCard";
import { WearComplianceCard } from "@/components/patient/WearComplianceCard";
import { QuickLinks } from "@/components/patient/QuickLinks";
import { LoadingState } from "@/components/patient/shared/LoadingState";
import { ErrorState } from "@/components/patient/shared/ErrorState";
import { ApiError } from "@/lib/api";
import { formatShortId } from "@/lib/format";
import { fetchPatientSummary, type PatientSummary } from "@/lib/patientApi";

// status_label backend sudah persis "stable"/"attention"/"urgent" (StatusLevel) —
// lihat ringkasan sesi penyambungan Fase 5 soal ini disamakan dengan Tony.
const STATUS_LABEL_TO_LEVEL: Record<PatientSummary["status_label"], StatusLevel> = {
  stable: "stable",
  attention: "attention",
  urgent: "urgent",
};

function formatRelativeTime(isoTimestamp: string | null): string {
  if (!isoTimestamp) return "Belum ada data";
  const diffMs = Date.now() - new Date(isoTimestamp).getTime();
  const diffMinutes = Math.round(diffMs / 60000);
  if (diffMinutes < 1) return "Baru saja";
  if (diffMinutes < 60) return `${diffMinutes} menit yang lalu`;
  const diffHours = Math.round(diffMinutes / 60);
  return `${diffHours} jam yang lalu`;
}

function formatVitalRange(range: { min: number | null; max: number | null } | undefined, unit: string): string {
  if (!range || range.min === null || range.max === null) return "Belum ada data hari ini";
  if (range.min === range.max) return `hari ini ${range.min}${unit}`;
  return `hari ini ${range.min}–${range.max}${unit}`;
}

export default function PatientHomePage() {
  const [summary, setSummary] = useState<PatientSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadSummary() {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchPatientSummary();
      setSummary(data);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Gagal memuat data. Periksa koneksi Anda dan coba lagi."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadSummary();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-background p-6">
        <LoadingState label="Memuat ringkasan kondisi Anda..." />
      </div>
    );
  }

  if (error || !summary) {
    return (
      <div className="min-h-screen bg-background p-6">
        <ErrorState message={error ?? "Data tidak ditemukan."} onRetry={loadSummary} />
      </div>
    );
  }

  const vitalCards = [
    {
      label: "Detak Jantung",
      icon: "favorite",
      iconBgClass: "bg-error-container/50",
      iconColorClass: "text-status-error",
      value: summary.latest_vitals.hr,
      unit: "bpm",
      rangeLabel: formatVitalRange(summary.today_range?.hr, " bpm"),
    },
    {
      label: "Oksigen (SpO2)",
      icon: "air",
      iconBgClass: "bg-accent-blue/10",
      iconColorClass: "text-accent-blue",
      value: summary.latest_vitals.spo2,
      unit: "%",
      rangeLabel: formatVitalRange(summary.today_range?.spo2, "%"),
    },
    {
      label: "Laju Napas",
      icon: "waves",
      iconBgClass: "bg-tertiary-container/30",
      iconColorClass: "text-tertiary",
      value: summary.latest_vitals.rr,
      unit: "/mnt",
      rangeLabel: formatVitalRange(summary.today_range?.rr, " /mnt"),
    },
  ];

  return (
    <div className="min-h-screen bg-background pb-24 md:pb-0">
      <PatientSidebar
        patientName={summary.patient_name}
        patientId={formatShortId(summary.patient_id)}
        statusLabel={summary.status_label}
        activeHref="/patient/home"
      />
      <PatientTopBar patientName={summary.patient_name} />

      <main className="mx-auto flex max-w-5xl flex-col gap-6 p-4 md:ml-sidebar-width md:p-6 lg:p-8">
        <StatusHeroCard
          level={STATUS_LABEL_TO_LEVEL[summary.status_label]}
          lastUpdatedLabel={formatRelativeTime(summary.latest_vitals.timestamp)}
        />

        <DeviceStatusStrip
          connected={summary.device_connected}
          signalLabel={summary.device_connected ? "Vest terhubung dengan baik" : "Vest tidak terhubung"}
          batteryPercent={null}
        />

        <section>
          <h3 className="mb-4 text-xl font-bold">Ringkasan Hari Ini</h3>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {vitalCards.map((vital) => (
              <VitalSummaryCard
                key={vital.label}
                label={vital.label}
                icon={vital.icon}
                iconBgClass={vital.iconBgClass}
                iconColorClass={vital.iconColorClass}
                value={vital.value ?? 0}
                unit={vital.unit}
                rangeLabel={vital.value === null ? "Belum ada data" : vital.rangeLabel}
              />
            ))}
          </div>
        </section>

        {summary.wear_compliance_today_hours !== null && (
          <WearComplianceCard hoursWorn={summary.wear_compliance_today_hours} targetHours={8} />
        )}

        <QuickLinks />

        <p className="text-center text-xs text-on-surface-variant">
          Data Simulasi &mdash; belum terhubung ke perangkat fisik.
        </p>
      </main>

      <PatientBottomNav activeHref="/patient/home" />
    </div>
  );
}
