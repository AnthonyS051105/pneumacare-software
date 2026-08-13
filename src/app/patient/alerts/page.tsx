"use client";

import { useMemo, useState } from "react";
import { PatientSidebar } from "@/components/patient/PatientSidebar";
import { PatientTopBar } from "@/components/patient/PatientTopBar";
import { PatientBottomNav } from "@/components/patient/PatientBottomNav";
import { MonthlySummaryStrip } from "@/components/patient/alerts/MonthlySummaryStrip";
import {
  AlertFilterTabs,
  type AlertFilter,
} from "@/components/patient/alerts/AlertFilterTabs";
import { AlertDateGroup } from "@/components/patient/alerts/AlertDateGroup";
import { AlertsEmptyState } from "@/components/patient/alerts/AlertsEmptyState";
import type { AlertItemData } from "@/components/patient/alerts/AlertListItem";

// TODO_NATHANAEL_CONFIRM: data dummy untuk demo — belum terhubung ke tabel `alerts` sungguhan.
const DUMMY_PATIENT = {
  name: "Samantha W.",
  patientId: "9821",
  statusLabel: "Stable",
};

// TODO_CLINICAL_VALUE: transformasi bahasa teknis -> awam masih contoh statis, belum ada fungsi mapping backend (lihat UIUX_FLOW.md §3.3, §9).
const DUMMY_GROUPS: { label: string; alerts: AlertItemData[] }[] = [
  {
    label: "Hari Ini",
    alerts: [
      {
        id: "a1",
        level: "warning",
        message:
          "Kadar oksigen Anda sempat rendah, namun sudah kembali normal.",
        timeLabel: "08:42",
        isRead: false,
      },
      {
        id: "a2",
        level: "info",
        message: "Perangkat Anda terhubung kembali setelah sempat terputus.",
        timeLabel: "07:15",
        isRead: false,
      },
    ],
  },
  {
    label: "Kemarin",
    alerts: [
      {
        id: "a3",
        level: "info",
        message: "Detak jantung Anda berada dalam rentang normal sepanjang hari.",
        timeLabel: "21:03",
        isRead: true,
      },
    ],
  },
  {
    label: "Minggu Ini",
    alerts: [
      {
        id: "a4",
        level: "urgent",
        message:
          "Laju napas Anda berada di luar rentang normal. Tenaga medis Anda telah diberi tahu.",
        timeLabel: "Senin, 19:20",
        isRead: true,
      },
      {
        id: "a5",
        level: "warning",
        message: "Pemakaian vest hari ini di bawah target Anda.",
        timeLabel: "Senin, 21:00",
        isRead: true,
      },
    ],
  },
];

export default function PatientAlertsPage() {
  const [filter, setFilter] = useState<AlertFilter>("all");

  const unreadCount = useMemo(
    () =>
      DUMMY_GROUPS.reduce(
        (total, group) =>
          total + group.alerts.filter((alert) => !alert.isRead).length,
        0
      ),
    []
  );

  const totalThisMonth = useMemo(
    () => DUMMY_GROUPS.reduce((total, group) => total + group.alerts.length, 0),
    []
  );

  const visibleGroups = useMemo(
    () =>
      DUMMY_GROUPS.map((group) => ({
        label: group.label,
        alerts:
          filter === "unread"
            ? group.alerts.filter((alert) => !alert.isRead)
            : group.alerts,
      })).filter((group) => group.alerts.length > 0),
    [filter]
  );

  const isEmpty = visibleGroups.length === 0;

  return (
    <div className="min-h-screen bg-background pb-24 md:pb-0">
      <PatientSidebar
        patientName={DUMMY_PATIENT.name}
        patientId={DUMMY_PATIENT.patientId}
        statusLabel={DUMMY_PATIENT.statusLabel}
        activeHref="/patient/alerts"
      />
      <PatientTopBar patientName={DUMMY_PATIENT.name} />

      <main className="mx-auto flex max-w-5xl flex-col gap-6 p-4 md:ml-sidebar-width md:p-6 lg:p-8">
        <header>
          <h2 className="text-2xl font-bold text-on-surface">Notifikasi</h2>
          <p className="text-sm text-on-surface-variant mt-1">
            Riwayat pemberitahuan terkait kondisi kesehatan Anda.
          </p>
        </header>

        <MonthlySummaryStrip
          totalThisMonth={totalThisMonth}
          trendLabel="Lebih sedikit dibanding bulan lalu 👍"
        />

        <AlertFilterTabs
          value={filter}
          onChange={setFilter}
          unreadCount={unreadCount}
        />

        {isEmpty ? (
          <AlertsEmptyState
            message={
              filter === "unread"
                ? "Semua notifikasi sudah dibaca"
                : "Belum ada notifikasi"
            }
          />
        ) : (
          <div className="flex flex-col gap-6">
            {visibleGroups.map((group) => (
              <AlertDateGroup
                key={group.label}
                label={group.label}
                alerts={group.alerts}
              />
            ))}
          </div>
        )}

        <p className="text-center text-xs text-on-surface-variant">
          Data Simulasi &mdash; belum terhubung ke perangkat fisik.
        </p>
      </main>

      <PatientBottomNav activeHref="/patient/alerts" />
    </div>
  );
}
