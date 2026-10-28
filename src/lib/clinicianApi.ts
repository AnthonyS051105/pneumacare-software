import { apiFetch } from "@/lib/api";
import type { DeviceInfo, TimeRange, VitalReadingPoint } from "@/lib/patientApi";

// Mengikuti backend/api/clinician_routes.py & backend/api/routes.py (SDD_SOFTWARE.md §4.2).

export type ClinicianPatient = {
  id: string;
  name: string;
  email: string | null;
  date_of_birth: string | null;
  latest_alert_level: number | null;
  latest_alert_acknowledged: boolean | null;
  /** Level tertinggi di antara alert yang BELUM ditinjau (null = tidak ada). */
  open_alert_level: number | null;
  device: DeviceInfo | null;
  latest_vitals: { hr: number | null; spo2: number | null; rr: number | null; timestamp: string | null };
};

export type AlertTrigger = {
  type: "vital_threshold" | "trend_slope" | string;
  parameter?: string;
  value?: number | null;
  threshold?: number | string | null;
  severity?: "breach" | "near" | null;
  slope?: number;
};

export type ClinicianAlert = {
  id: string;
  device_id: string;
  patient_id: string;
  patient_name: string | null;
  level: number;
  triggers: AlertTrigger[];
  created_at: string;
  acknowledged: boolean;
  acknowledged_by: string | null;
  acknowledged_at: string | null;
};

export type Classification = {
  channel_id: number;
  segment_start: string;
  segment_end: string;
  predicted_class: "normal" | "abnormal";
  confidence: number;
  probabilities: Partial<Record<"normal" | "abnormal", number>> | null;
  model_version: string;
  severity_class: string | null;
} | null;

export type TrendInfo = { window_start: string; window_end: string; slope: number; significant: boolean } | null;

export type ClassificationHistory = {
  range: TimeRange;
  start: string;
  end: string;
  bucket_seconds: number;
  buckets: {
    bucket_start: string;
    total: number;
    normal: number;
    abnormal: number;
    abnormal_ratio: number | null;
  }[];
};

export type Thresholds = {
  hr_min: number | null;
  hr_max: number | null;
  spo2_min: number | null;
  rr_min: number | null;
  rr_max: number | null;
  trend_significance_threshold: number | null;
  updated_by: string | null;
  updated_at: string | null;
  action_plan: string;
};

export type ClinicianProfile = {
  id: string;
  email: string;
  full_name: string;
  specialization: string | null;
  institution: string | null;
  str_sip_number: string | null;
};

/** Backend menyimpan waktu sebagai UTC tanpa zona; kirim batas waktu dalam UTC eksplisit. */
const iso = (date: Date) => date.toISOString();

export const fetchPatients = () => apiFetch<ClinicianPatient[]>("/patients");
export const fetchPatient = (id: string) => apiFetch<ClinicianPatient>(`/patients/${encodeURIComponent(id)}`);
export const addPatient = (email: string) =>
  apiFetch<ClinicianPatient>("/patients", { method: "POST", body: JSON.stringify({ email }) });

export const fetchVitalsHistory = (id: string, from: Date, to: Date) =>
  apiFetch<VitalReadingPoint[]>(
    `/patients/${encodeURIComponent(id)}/vitals/history?from=${encodeURIComponent(iso(from))}&to=${encodeURIComponent(iso(to))}`,
  );
export const fetchClassification = (id: string) =>
  apiFetch<Classification>(`/patients/${encodeURIComponent(id)}/classification/latest`);
export const fetchTrend = (id: string) => apiFetch<TrendInfo>(`/patients/${encodeURIComponent(id)}/trend`);
export const fetchClassificationHistory = (id: string, range: TimeRange) =>
  apiFetch<ClassificationHistory>(`/patients/${encodeURIComponent(id)}/classification/history?range=${range}`);

export const fetchPatientAlerts = (id: string) => apiFetch<ClinicianAlert[]>(`/patients/${encodeURIComponent(id)}/alerts`);
export const fetchAlertCenter = () => apiFetch<ClinicianAlert[]>("/clinician/alerts");
export const acknowledgeAlert = (alertId: string) =>
  apiFetch<{ alert_id: string; acknowledged: boolean; acknowledged_at: string }>(
    `/alerts/${encodeURIComponent(alertId)}/acknowledge`,
    { method: "POST" },
  );

export const fetchThresholds = (id: string) => apiFetch<Thresholds>(`/patients/${encodeURIComponent(id)}/thresholds`);
export const updateThresholds = (id: string, body: Partial<Omit<Thresholds, "updated_by" | "updated_at">>) =>
  apiFetch<Thresholds>(`/patients/${encodeURIComponent(id)}/thresholds`, { method: "PUT", body: JSON.stringify(body) });

export const fetchClinicianProfile = () => apiFetch<ClinicianProfile>("/clinician/profile");
export const updateClinicianProfile = (
  body: Partial<Pick<ClinicianProfile, "full_name" | "specialization" | "institution" | "str_sip_number">> & {
    current_password?: string;
    new_password?: string;
  },
) => apiFetch<ClinicianProfile>("/clinician/profile", { method: "PUT", body: JSON.stringify(body) });
