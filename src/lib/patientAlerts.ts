import type { Alert, AlertLevel } from "@/lib/demo-data";
import { formatEventTime } from "@/lib/format";
import type { PatientAlert } from "@/lib/patientApi";

const LEVEL: Record<number, AlertLevel> = { 1: "info", 2: "warn", 3: "urgent" };

const FALLBACK_MESSAGE = "Pemberitahuan ini tercatat untuk membantu pemantauan Anda.";

/** Bentuk respons API alert pasien -> bentuk yang dipakai AlertItem. */
export function toAlertView(a: PatientAlert, now: Date = new Date()): Alert {
  const [first, ...rest] = a.messages;
  return {
    id: a.id,
    patient: "",
    title: a.level_label,
    plain: first ?? a.level_label,
    detail: a.messages.join(" "),
    message: rest.length ? rest.join(" ") : FALLBACK_MESSAGE,
    time: formatEventTime(a.created_at, now),
    level: LEVEL[a.level] ?? "info",
    resolved: false,
    ack: a.acknowledged,
  };
}
