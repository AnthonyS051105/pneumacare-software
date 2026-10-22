// Logika murni daftar pasien tenaga medis.

import type { ClinicianPatient } from "@/lib/clinicianApi";
import type { PatientStatus } from "@/lib/demo-data";
import { dayKey } from "@/lib/format";

/** Interval polling (ms). Parameter operasional UI, bukan nilai klinis. */
export const POLL_MS = { list: 15_000, vitals: 5_000, alerts: 15_000 } as const;

/** Event untuk memuat ulang daftar pasien setelah modal "Tambah Pasien" berhasil. */
export const CLINICIAN_RELOAD_EVENT = "pneuma:clinician-reload";

/** Event agar ClinicianGuard memuat ulang nama di sidebar setelah profil disimpan. */
export const CLINICIAN_PROFILE_EVENT = "pneuma:clinician-profile";

/**
 * Status tampilan. Alert yang belum ditinjau didahulukan dari status perangkat supaya
 * urgensi tidak tersembunyi hanya karena rompi sedang offline (UIUX_FLOW.md §4.1).
 * Level 1 (informasi) sengaja tidak menaikkan status — tampil lebih tenang dari level 2/3.
 */
export function patientStatus(p: Pick<ClinicianPatient, "open_alert_level" | "device">): PatientStatus {
  if (p.open_alert_level === 3) return "urgent";
  if (p.open_alert_level === 2) return "warn";
  if (!p.device || p.device.status !== "online") return "off";
  return "stable";
}

/** Usia (tahun penuh) dari "YYYY-MM-DD"; null bila tidak ada / tidak valid. */
export function ageFrom(dateOfBirth: string | null, now: Date = new Date()): number | null {
  if (!dateOfBirth || !/^\d{4}-\d{2}-\d{2}$/.test(dateOfBirth)) return null;
  const [y, m, d] = dateOfBirth.split("-").map(Number);
  const [ny, nm, nd] = dayKey(now).split("-").map(Number);
  const age = ny - y - (nm < m || (nm === m && nd < d) ? 1 : 0);
  return age >= 0 && age < 150 ? age : null;
}
