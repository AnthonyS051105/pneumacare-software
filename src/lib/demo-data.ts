// Fixture data simulasi — disalin apa adanya dari PNEUMACARE_Final_UI/PNEUMACARE/app.js.
// Semua angka & identitas BUKAN data pasien sungguhan. Saat integrasi backend, ganti
// sumber di file ini dengan hasil REST API (lihat src/lib/api.ts & src/lib/patientApi.ts)
// tanpa mengubah komponen tampilan.

export type PatientStatus = "urgent" | "warn" | "stable" | "off";

export type Patient = {
  id: string;
  name: string;
  age: number | null;
  device: string;
  hr: number | null;
  spo2: number | null;
  rr: number | null;
  status: PatientStatus;
  online: boolean;
  email?: string;
};

export type AlertLevel = "urgent" | "warn" | "info";

export type Alert = {
  id: string;
  patient: string;
  title: string;
  plain: string;
  detail: string;
  time: string;
  level: AlertLevel;
  resolved: boolean;
  ack?: boolean;
};

export type VitalKey = "hr" | "spo2" | "rr";

export type Vital = {
  label: string;
  technical: string;
  value: number;
  unit: string;
  color: string;
  icon: "heart" | "droplets" | "wind";
  series: number[];
  min: number;
  max: number;
};

export const patients: Patient[] = [
  { id: "ahmad", name: "Ahmad Hidayat", age: 67, device: "PC-006", hr: 102, spo2: 89, rr: 27, status: "urgent", online: true },
  { id: "siti", name: "Siti Aminah", age: 61, device: "PC-004", hr: 88, spo2: 92, rr: 23, status: "warn", online: true },
  { id: "budi", name: "Budi Santoso", age: 64, device: "PC-001", hr: 78, spo2: 96, rr: 18, status: "stable", online: true },
  { id: "dewi", name: "Dewi Lestari", age: 58, device: "PC-003", hr: null, spo2: null, rr: null, status: "off", online: false },
  { id: "rudi", name: "Rudi Hartono", age: 65, device: "PC-002", hr: 81, spo2: 95, rr: 19, status: "stable", online: true },
  { id: "maya", name: "Maya Sari", age: 59, device: "PC-005", hr: 84, spo2: 94, rr: 21, status: "warn", online: true },
];

export const alerts: Alert[] = [
  { id: "a1", patient: "ahmad", title: "SpO₂ di bawah ambang", plain: "Kadar oksigen sempat rendah", detail: "SpO₂ 89% < ambang pemantauan 92%. Perlu peninjauan tenaga medis.", time: "Hari ini, 09.28 WIB", level: "urgent", resolved: false },
  { id: "a2", patient: "budi", title: "SpO₂ melewati ambang", plain: "Kadar oksigen sempat rendah", detail: "SpO₂ 91% < ambang pemantauan 92% pada 09.05 WIB. Nilai terbaru 96% pada 09.30 WIB.", time: "Hari ini, 09.05 WIB", level: "warn", resolved: true },
  { id: "a3", patient: "siti", title: "Frekuensi napas meningkat", plain: "Frekuensi napas sempat meningkat", detail: "RR 23 napas/menit melewati rentang pemantauan. Perlu peninjauan tenaga medis.", time: "Hari ini, 08.45 WIB", level: "warn", resolved: false },
  { id: "a4", patient: "budi", title: "Koneksi perangkat pulih", plain: "Rompi kembali terhubung", detail: "Koneksi kembali tersedia pada 07.20 WIB. Data selama koneksi terputus tidak ditampilkan sebagai nilai terkini.", time: "Hari ini, 07.20 WIB", level: "info", resolved: true },
  { id: "a5", patient: "budi", title: "Alert oksigen telah ditinjau", plain: "Pemberitahuan sebelumnya telah ditinjau", detail: "Tenaga medis telah meninjau pemberitahuan kemarin. Peninjauan tidak menentukan kondisi terkini.", time: "Kemarin, 16.42 WIB", level: "urgent", resolved: true, ack: true },
];

export const vitalKeys: VitalKey[] = ["hr", "spo2", "rr"];

export const values: Record<VitalKey, Vital> = {
  hr: { label: "Detak jantung", technical: "Heart Rate", value: 78, unit: "bpm", color: "#b75b66", icon: "heart", series: [77, 76, 79, 78, 80, 77, 76, 78, 79, 77, 78, 78], min: 65, max: 90 },
  spo2: { label: "Kadar oksigen", technical: "SpO₂", value: 96, unit: "%", color: "#477eab", icon: "droplets", series: [96, 97, 96, 96, 95, 96, 97, 96, 96, 95, 96, 96], min: 90, max: 100 },
  rr: { label: "Laju napas", technical: "Respiratory Rate", value: 18, unit: "napas/menit", color: "#23746b", icon: "wind", series: [18, 17, 18, 19, 18, 18, 17, 18, 19, 18, 18, 18], min: 12, max: 24 },
};

/** Pasien yang sedang login di portal pasien (fixture). */
export const CURRENT_PATIENT_ID = "budi";

export const DEMO_PASSWORD = "Pneuma123!";
export const DEMO_PATIENT_EMAIL = "budi@example.com";
export const DEMO_CLINICIAN_EMAIL = "nadia@example.com";
export const VALID_PAIR_CODES = ["PC-4821", "PC-001"];

export const statusOrder: Record<PatientStatus, number> = { urgent: 0, warn: 1, off: 2, stable: 3 };
