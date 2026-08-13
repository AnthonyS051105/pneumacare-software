"use client";

import { useState } from "react";
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

// TODO_NATHANAEL_CONFIRM: data dummy untuk demo — belum terhubung ke readings_vital sungguhan.
const DUMMY_PATIENT = {
  name: "Samantha W.",
  patientId: "9821",
  statusLabel: "Stable",
};

// TODO_CLINICAL_VALUE: rentang normal HR/SpO2 pada chart masih placeholder visual, belum divalidasi klinis.
const RANGE_PERIOD_LABEL: Record<TimeRange, string> = {
  "24h": "24 jam",
  "7d": "7 hari",
  "30d": "30 hari",
};

export default function PatientHistoryPage() {
  const [range, setRange] = useState<TimeRange>("24h");

  return (
    <div className="min-h-screen bg-background pb-24 md:pb-0">
      <PatientSidebar
        patientName={DUMMY_PATIENT.name}
        patientId={DUMMY_PATIENT.patientId}
        statusLabel={DUMMY_PATIENT.statusLabel}
        activeHref="/patient/history"
      />
      <PatientTopBar patientName={DUMMY_PATIENT.name} />

      <main className="mx-auto flex max-w-5xl flex-col gap-6 p-4 md:ml-sidebar-width md:p-6 lg:p-8">
        <header>
          <h2 className="text-2xl font-bold text-on-surface">Riwayat Vital</h2>
          <p className="text-sm text-on-surface-variant mt-1">
            Pantau perkembangan kondisi kesehatan Anda.
          </p>
        </header>

        <TimeRangeFilter value={range} onChange={setRange} />

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-8 flex flex-col gap-6">
            <VitalTrendCard
              title="Detak Jantung (HR)"
              unitLabel="BPM (Denyut per Menit)"
              icon="favorite"
              iconColorClass="text-status-warning"
              stats={[
                { label: "Saat ini", value: "72", emphasize: true },
                { label: "Rata-rata", value: "75" },
                { label: "Min", value: "68" },
                { label: "Max", value: "92" },
              ]}
              chartPath="M0,35 Q10,32 20,38 T40,25 T60,30 T80,15 T100,28"
              chartColor="var(--color-primary-container)"
              yAxisLabels={["120", "80", "40"]}
              xAxisLabels={["00:00", "06:00", "12:00", "18:00", "Sekarang"]}
              alertMarker={{ cx: 80, cy: 15 }}
            />

            <VitalTrendCard
              title="Saturasi Oksigen (SpO2)"
              unitLabel="Persentase (%)"
              icon="water_drop"
              iconColorClass="text-accent-blue"
              stats={[
                { label: "Saat ini", value: "98%", emphasize: true },
                { label: "Rata-rata", value: "97%" },
              ]}
              chartPath="M0,10 L20,12 L40,8 L60,11 L80,5 L100,9"
              chartColor="var(--color-accent-blue)"
              chartViewBox="0 0 100 30"
              chartHeightClass="h-32"
            />
          </div>

          <div className="lg:col-span-4 flex flex-col gap-6">
            <PatternInsightCard
              periodLabel={RANGE_PERIOD_LABEL[range]}
              insightText="Detak jantung Anda paling stabil di pagi hari antara pukul 06:00 - 09:00."
            />

            <WearComplianceChartCard
              targetHours={8}
              days={[
                { day: "Sen", hours: 4.8 },
                { day: "Sel", hours: 6.4 },
                { day: "Rab", hours: 8, isBest: true },
                { day: "Kam", hours: 3.2 },
                { day: "Jum", hours: 5.6, isHighlighted: true },
              ]}
            />

            <button
              type="button"
              className="w-full py-3 px-4 rounded-lg border-2 border-outline/30 text-on-surface-variant text-sm font-semibold flex items-center justify-center gap-2 hover:bg-surface-container-low hover:border-outline/50 transition-all"
            >
              <span className="material-symbols-outlined">download</span>
              Unduh Laporan
            </button>
          </div>
        </div>

        <p className="text-center text-xs text-on-surface-variant">
          Data Simulasi &mdash; belum terhubung ke perangkat fisik.
        </p>
      </main>

      <PatientBottomNav activeHref="/patient/history" />
    </div>
  );
}
