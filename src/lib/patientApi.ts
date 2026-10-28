import { apiFetch } from "@/lib/api";

// Tipe respons mengikuti struktur aktual dari backend/api/patient_routes.py
// (SDD_SOFTWARE.md §4.3). Field yang TIDAK sesuai asumsi UI awal dilaporkan
// terpisah ke Tony — lihat ringkasan sesi penyambungan Fase 5.

export type VitalRange = { min: number | null; max: number | null };

export type DeviceInfo = {
  device_id: string;
  status: "online" | "offline";
  battery_percent: number | null;
  last_seen_at: string | null;
  signal_quality_ppg: "good" | "fair" | "poor" | null;
  signal_quality_audio: Record<string, "good" | "fair" | "poor"> | null;
};

export type PatientSummary = {
  patient_id: string;
  patient_name: string;
  status_label: "stable" | "attention" | "urgent";
  device_connected: boolean;
  device: DeviceInfo | null;
  latest_vitals: {
    hr: number | null;
    spo2: number | null;
    rr: number | null;
    timestamp: string | null;
  };
  today_range: { hr: VitalRange; spo2: VitalRange; rr: VitalRange } | null;
  wear_compliance_today_hours: number | null;
  latest_classification: {
    predicted_class: "normal" | "abnormal";
    confidence: number;
    timestamp: string;
  } | null;
};

export function fetchPatientSummary(): Promise<PatientSummary> {
  return apiFetch<PatientSummary>("/patient/me/summary");
}

export type TimeRange = "24h" | "7d" | "30d";

export type VitalReadingPoint = {
  hr: number | null;
  spo2: number | null;
  rr: number | null;
  timestamp: string;
};

export type VitalStat = { current: number | null; avg: number | null; min: number | null; max: number | null };

export type PatientHistory = {
  readings: VitalReadingPoint[];
  stats: { hr: VitalStat; spo2: VitalStat; rr: VitalStat } | Record<string, never>;
  wear_compliance_by_day: { date: string; hours: number }[];
  pattern_insight: string | null;
};

export function fetchPatientHistory(range: TimeRange): Promise<PatientHistory> {
  return apiFetch<PatientHistory>(`/patient/me/history?range=${range}`);
}

export type PatientAlert = {
  id: string;
  created_at: string;
  acknowledged: boolean;
  level: number; // 1 | 2 | 3
  level_label: string;
  messages: string[];
};

export function fetchPatientAlerts(): Promise<PatientAlert[]> {
  return apiFetch<PatientAlert[]>("/patient/me/alerts");
}

export type PatientProfile = {
  email: string;
  full_name: string;
  patient_name: string | null;
  date_of_birth: string | null;
  device_paired: boolean;
  device: DeviceInfo | null;
  clinician: { full_name: string; specialization: string | null; institution: string | null } | null;
};

export function fetchPatientProfile(): Promise<PatientProfile> {
  return apiFetch<PatientProfile>("/patient/me/profile");
}

export type ProfileUpdate = {
  full_name?: string;
  date_of_birth?: string | null;
  current_password?: string;
  new_password?: string;
};

export function updatePatientProfile(update: ProfileUpdate): Promise<{ status: "ok" }> {
  return apiFetch("/patient/me/profile", { method: "PUT", body: JSON.stringify(update) });
}

export function repairDevice(pairingCode: string): Promise<{ status: "ok"; device_id: string }> {
  return apiFetch("/patient/me/device/repair", {
    method: "POST",
    body: JSON.stringify({ pairing_code: pairingCode }),
  });
}
