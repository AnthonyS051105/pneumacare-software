"use client";

import { useEffect, useState } from "react";
import { PatientSidebar } from "@/components/patient/PatientSidebar";
import { PatientTopBar } from "@/components/patient/PatientTopBar";
import { PatientBottomNav } from "@/components/patient/PatientBottomNav";
import {
  TimeRangeFilter,
  type TimeRange,
} from "@/components/patient/history/TimeRangeFilter";
import { VitalTrendCard } from "@/components/patient/history/VitalTrendCard";
import { PatternInsightCard } from "@/components/patient/history/PatternInsightCard";
import { WearComplianceChartCard } from "@/components/patient/history/WearComplianceChartCard";
import { LoadingState } from "@/components/patient/shared/LoadingState";
import { ErrorState } from "@/components/patient/shared/ErrorState";
import { ApiError } from "@/lib/api";
import { formatShortId } from "@/lib/format";
import { fetchPatientHistory, fetchPatientSummary, type PatientHistory } from "@/lib/patientApi";
import { buildLinePath } from "@/lib/chartPath";

const RANGE_PERIOD_LABEL: Record<TimeRange, string> = {
  "24h": "24 jam",
  "7d": "7 hari",
  "30d": "30 hari",
};

// Label hari Indonesia singkat, dipetakan dari getDay() (0=Minggu..6=Sabtu) —
// dipakai WearComplianceChartCard yang butuh field `day` bertipe string singkat.
const DAY_LABELS = ["Min", "Sen", "Sel", "Rab", "Kam", "Jum", "Sab"];

function formatStat(value: number | null, unit: string): string {
  return value === null ? "-" : `${value}${unit}`;
}

export default function PatientHistoryPage() {
  const [range, setRange] = useState<TimeRange>("24h");
  const [patientName, setPatientName] = useState<string>("");
  const [patientId, setPatientId] = useState<string>("");
  const [statusLabel, setStatusLabel] = useState<string>("stable");
  const [history, setHistory] = useState<PatientHistory | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData(selectedRange: TimeRange) {
    setLoading(true);
    setError(null);
    try {
      const [summaryData, historyData] = await Promise.all([
        fetchPatientSummary(),
        fetchPatientHistory(selectedRange),
      ]);
      setPatientName(summaryData.patient_name);
      setPatientId(formatShortId(summaryData.patient_id));
      setStatusLabel(summaryData.status_label);
      setHistory(historyData);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Gagal memuat riwayat vital. Periksa koneksi Anda dan coba lagi."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData(range);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [range]);

  const wearComplianceDays =
    history?.wear_compliance_by_day.map((day) => {
      const date = new Date(day.date);
      const isToday = new Date().toDateString() === date.toDateString();
      return {
        day: DAY_LABELS[date.getDay()],
        hours: day.hours,
        isBest: false,
        isHighlighted: isToday,
      };
    }) ?? [];

  if (wearComplianceDays.length > 0) {
    const maxHours = Math.max(...wearComplianceDays.map((d) => d.hours));
    const bestDay = wearComplianceDays.find((d) => d.hours === maxHours);
    if (bestDay) bestDay.isBest = true;
  }

  return (
    <div className="min-h-screen bg-background pb-24 md:pb-0">
      <PatientSidebar
        patientName={patientName || "Memuat..."}
        patientId={patientId}
        statusLabel={statusLabel}
        activeHref="/patient/history"
      />
      <PatientTopBar patientName={patientName || "Memuat..."} />

      <main className="mx-auto flex max-w-5xl flex-col gap-6 p-4 md:ml-sidebar-width md:p-6 lg:p-8">
        <header>
          <h2 className="text-2xl font-bold text-on-surface">Riwayat Vital</h2>
          <p className="text-sm text-on-surface-variant mt-1">
            Pantau perkembangan kondisi kesehatan Anda.
          </p>
        </header>

        <TimeRangeFilter value={range} onChange={setRange} />

        {loading ? (
          <LoadingState label="Memuat riwayat vital..." />
        ) : error || !history ? (
          <ErrorState message={error ?? "Data tidak ditemukan."} onRetry={() => loadData(range)} />
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            <div className="lg:col-span-8 flex flex-col gap-6">
              <VitalTrendCard
                title="Detak Jantung (HR)"
                unitLabel="BPM (Denyut per Menit)"
                icon="favorite"
                iconColorClass="text-status-warning"
                stats={[
                  { label: "Saat ini", value: formatStat(history.stats.hr?.current ?? null, ""), emphasize: true },
                  { label: "Rata-rata", value: formatStat(history.stats.hr?.avg ?? null, "") },
                  { label: "Min", value: formatStat(history.stats.hr?.min ?? null, "") },
                  { label: "Max", value: formatStat(history.stats.hr?.max ?? null, "") },
                ]}
                chartPath={buildLinePath(history.readings.map((r) => r.hr))}
                chartColor="var(--color-primary-container)"
              />

              <VitalTrendCard
                title="Saturasi Oksigen (SpO2)"
                unitLabel="Persentase (%)"
                icon="water_drop"
                iconColorClass="text-accent-blue"
                stats={[
                  { label: "Saat ini", value: formatStat(history.stats.spo2?.current ?? null, "%"), emphasize: true },
                  { label: "Rata-rata", value: formatStat(history.stats.spo2?.avg ?? null, "%") },
                ]}
                chartPath={buildLinePath(history.readings.map((r) => r.spo2), { height: 30 })}
                chartColor="var(--color-accent-blue)"
                chartViewBox="0 0 100 30"
                chartHeightClass="h-32"
              />
            </div>

            <div className="lg:col-span-4 flex flex-col gap-6">
              {history.pattern_insight && (
                <PatternInsightCard
                  periodLabel={RANGE_PERIOD_LABEL[range]}
                  insightText={history.pattern_insight}
                />
              )}

              {wearComplianceDays.length > 0 && (
                <WearComplianceChartCard targetHours={8} days={wearComplianceDays} />
              )}

              <button
                type="button"
                className="w-full py-3 px-4 rounded-lg border-2 border-outline/30 text-on-surface-variant text-sm font-semibold flex items-center justify-center gap-2 hover:bg-surface-container-low hover:border-outline/50 transition-all"
              >
                <span className="material-symbols-outlined">download</span>
                Unduh Laporan
              </button>
            </div>
          </div>
        )}

        <p className="text-center text-xs text-on-surface-variant">
          Data Simulasi &mdash; belum terhubung ke perangkat fisik.
        </p>
      </main>

      <PatientBottomNav activeHref="/patient/history" />
    </div>
  );
}
