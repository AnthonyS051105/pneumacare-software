// Alert untuk tenaga medis: detail trigger teknis apa adanya (FR-SW-054), bukan bahasa awam.
// Murni (tanpa I/O).

import type { Alert, AlertLevel } from "@/lib/demo-data";
import type { AlertTrigger, ClinicianAlert } from "@/lib/clinicianApi";
import { formatEventTime } from "@/lib/format";

const PARAM: Record<string, { label: string; unit: string }> = {
  hr: { label: "HR", unit: " bpm" },
  spo2: { label: "SpO₂", unit: "%" },
  rr: { label: "RR", unit: " napas/menit" },
  abnormal_frequency: { label: "frekuensi abnormal", unit: "" },
};

const LEVEL: Record<number, AlertLevel> = { 1: "info", 2: "warn", 3: "urgent" };

function param(name: string | undefined, type?: string) {
  if (!name) return type === "trend_slope" ? PARAM.abnormal_frequency : { label: "parameter", unit: "" };
  return PARAM[name] ?? { label: name, unit: "" };
}

const num = (v: unknown) => (typeof v === "number" ? String(Math.round(v * 100) / 100) : v == null ? "—" : String(v));

/** "SpO₂ 91% < ambang 92%" / "HR 118 bpm mendekati ambang 120 bpm" / "Tren frekuensi abnormal naik (slope 0.14; ambang 0.05)". */
export function triggerText(t: AlertTrigger): string {
  const { label, unit } = param(t.parameter, t.type);
  if (t.type === "vital_threshold") {
    // Trigger lama/tidak lengkap tanpa angka: jangan tampilkan "—%" yang membingungkan.
    if (t.value == null) return `${label} ${t.severity === "near" ? "mendekati" : "melewati"} ambang`;
    const value = `${num(t.value)}${unit}`;
    const threshold = `${num(t.threshold)}${typeof t.threshold === "number" ? unit : ""}`;
    if (t.severity === "near") return `${label} ${value} mendekati ambang ${threshold}`;
    const op =
      typeof t.value === "number" && typeof t.threshold === "number" ? (t.value < t.threshold ? "<" : ">") : "melewati";
    return `${label} ${value} ${op} ambang ${threshold}`;
  }
  if (t.type === "trend_slope") {
    const slope = t.slope ?? t.value;
    if (slope == null) return `Tren ${label} naik signifikan`;
    return `Tren ${label} naik (slope ${num(slope)}; ambang signifikansi ${num(t.threshold)})`;
  }
  return `${label}: ${num(t.value)}`;
}

/** Judul ringkas. Level 3 dibedakan antara eskalasi tren persisten dan multi-trigger (kontrak §5.1). */
export function alertTitle(a: Pick<ClinicianAlert, "level" | "triggers">): string {
  const [first] = a.triggers;
  if (a.level === 3) {
    if (a.triggers.length >= 2) return "Multi-parameter kritis";
    if (first?.type === "trend_slope") return "Tren memburuk konsisten";
    return "Alert kritis";
  }
  if (!first) return a.level === 1 ? "Informasi pemantauan" : "Peringatan pemantauan";
  const { label } = param(first.parameter, first.type);
  if (first.type === "trend_slope") return `Tren ${label} signifikan`;
  if (first.severity === "near") return `${label} mendekati ambang`;
  return `${label} melewati ambang`;
}

export function toClinicalAlertView(a: ClinicianAlert, now: Date = new Date()): Alert {
  const detail = a.triggers.length ? a.triggers.map(triggerText).join("; ") + "." : "Tidak ada detail trigger.";
  const title = alertTitle(a);
  return {
    id: a.id,
    patient: a.patient_id,
    patientName: a.patient_name ?? undefined,
    title,
    plain: title,
    detail,
    time: formatEventTime(a.created_at, now),
    level: LEVEL[a.level] ?? "info",
    resolved: false,
    ack: a.acknowledged,
  };
}
