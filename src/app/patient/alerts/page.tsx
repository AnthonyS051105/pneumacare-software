"use client";

import { useEffect, useMemo, useState } from "react";
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
import type { AlertItemData, AlertLevel } from "@/components/patient/alerts/AlertListItem";
import { LoadingState } from "@/components/patient/shared/LoadingState";
import { ErrorState } from "@/components/patient/shared/ErrorState";
import { ApiError } from "@/lib/api";
import { formatShortId } from "@/lib/format";
import { fetchPatientAlerts, fetchPatientSummary, type PatientAlert } from "@/lib/patientApi";

// Pemetaan level backend (1/2/3) -> AlertLevel UI (info/warning/urgent), DIKONFIRMASI
// Tony: level 1 (near-threshold) -> "info" (styling hijau/sukses yang sudah ada di
// AlertListItem.tsx, karena near-threshold = kondisi masih aman, sekadar FYI).
const BACKEND_LEVEL_TO_UI: Record<number, AlertLevel> = {
  1: "info",
  2: "warning",
  3: "urgent",
};

function toDateGroupLabel(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfYesterday = new Date(startOfToday);
  startOfYesterday.setDate(startOfYesterday.getDate() - 1);
  const startOfWeek = new Date(startOfToday);
  startOfWeek.setDate(startOfWeek.getDate() - 7);

  if (date >= startOfToday) return "Hari Ini";
  if (date >= startOfYesterday) return "Kemarin";
  if (date >= startOfWeek) return "Minggu Ini";
  return "Lebih Lama";
}

function formatTimeLabel(isoTimestamp: string): string {
  const date = new Date(isoTimestamp);
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const time = date.toLocaleTimeString("id-ID", { hour: "2-digit", minute: "2-digit" });
  if (date >= startOfToday) return time;
  const dayName = date.toLocaleDateString("id-ID", { weekday: "long" });
  return `${dayName}, ${time}`;
}

function toAlertItemData(alert: PatientAlert): AlertItemData {
  return {
    id: alert.id,
    level: BACKEND_LEVEL_TO_UI[alert.level] ?? "info",
    message: alert.messages.join(" "),
    timeLabel: formatTimeLabel(alert.created_at),
    // Backend tidak punya konsep "dibaca" untuk pasien (hanya `acknowledged`, yang
    // menurut UIUX_FLOW.md §3.3 justru BUKAN wewenang pasien) — dipetakan sementara
    // dari `!acknowledged` sebagai proksi, lihat catatan perbedaan field di ringkasan sesi.
    isRead: alert.acknowledged,
  };
}

const GROUP_ORDER = ["Hari Ini", "Kemarin", "Minggu Ini", "Lebih Lama"];

export default function PatientAlertsPage() {
  const [filter, setFilter] = useState<AlertFilter>("all");
  const [patientName, setPatientName] = useState("");
  const [patientId, setPatientId] = useState("");
  const [statusLabel, setStatusLabel] = useState("stable");
  const [alerts, setAlerts] = useState<PatientAlert[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  async function loadData() {
    setLoading(true);
    setError(null);
    try {
      const [summaryData, alertsData] = await Promise.all([
        fetchPatientSummary(),
        fetchPatientAlerts(),
      ]);
      setPatientName(summaryData.patient_name);
      setPatientId(formatShortId(summaryData.patient_id));
      setStatusLabel(summaryData.status_label);
      setAlerts(alertsData);
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Gagal memuat notifikasi. Periksa koneksi Anda dan coba lagi."
      );
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadData();
  }, []);

  const items = useMemo(() => (alerts ?? []).map(toAlertItemData), [alerts]);

  const groupedByLabel = useMemo(() => {
    const groups = new Map<string, AlertItemData[]>();
    for (const item of items) {
      const alertData = (alerts ?? []).find((a) => a.id === item.id);
      if (!alertData) continue;
      const label = toDateGroupLabel(alertData.created_at);
      if (!groups.has(label)) groups.set(label, []);
      groups.get(label)!.push(item);
    }
    return GROUP_ORDER.map((label) => ({ label, alerts: groups.get(label) ?? [] })).filter(
      (group) => group.alerts.length > 0
    );
  }, [items, alerts]);

  const unreadCount = useMemo(() => items.filter((item) => !item.isRead).length, [items]);
  const totalThisMonth = useMemo(() => {
    const now = new Date();
    return (alerts ?? []).filter((a) => {
      const date = new Date(a.created_at);
      return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
    }).length;
  }, [alerts]);

  const visibleGroups = useMemo(
    () =>
      groupedByLabel
        .map((group) => ({
          label: group.label,
          alerts: filter === "unread" ? group.alerts.filter((a) => !a.isRead) : group.alerts,
        }))
        .filter((group) => group.alerts.length > 0),
    [groupedByLabel, filter]
  );

  const isEmpty = visibleGroups.length === 0;

  return (
    <div className="min-h-screen bg-background pb-24 md:pb-0">
      <PatientSidebar
        patientName={patientName || "Memuat..."}
        patientId={patientId}
        statusLabel={statusLabel}
        activeHref="/patient/alerts"
      />
      <PatientTopBar patientName={patientName || "Memuat..."} />

      <main className="mx-auto flex max-w-5xl flex-col gap-6 p-4 md:ml-sidebar-width md:p-6 lg:p-8">
        <header>
          <h2 className="text-2xl font-bold text-on-surface">Notifikasi</h2>
          <p className="text-sm text-on-surface-variant mt-1">
            Riwayat pemberitahuan terkait kondisi kesehatan Anda.
          </p>
        </header>

        {loading ? (
          <LoadingState label="Memuat notifikasi..." />
        ) : error || alerts === null ? (
          <ErrorState message={error ?? "Data tidak ditemukan."} onRetry={loadData} />
        ) : (
          <>
            <MonthlySummaryStrip
              totalThisMonth={totalThisMonth}
              trendLabel="Perbandingan dengan bulan lalu belum tersedia"
            />

            <AlertFilterTabs value={filter} onChange={setFilter} unreadCount={unreadCount} />

            {isEmpty ? (
              <AlertsEmptyState
                message={filter === "unread" ? "Semua notifikasi sudah dibaca" : "Belum ada notifikasi"}
              />
            ) : (
              <div className="flex flex-col gap-6">
                {visibleGroups.map((group) => (
                  <AlertDateGroup key={group.label} label={group.label} alerts={group.alerts} />
                ))}
              </div>
            )}
          </>
        )}

        <p className="text-center text-xs text-on-surface-variant">
          Data Simulasi &mdash; belum terhubung ke perangkat fisik.
        </p>
      </main>

      <PatientBottomNav activeHref="/patient/alerts" />
    </div>
  );
}
