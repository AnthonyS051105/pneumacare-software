"use client";

import { AlertItem } from "@/components/portal/AlertItem";
import { notificationsCard, toolbar, toolbarSelect } from "@/components/portal/layout";
import { Bell } from "@/components/ui/Icon";
import { btn, cn, Empty, Notice } from "@/components/ui/primitives";
import { acknowledgeAlert, fetchAlertCenter, fetchPatients, type ClinicianAlert } from "@/lib/clinicianApi";
import { toClinicalAlertView } from "@/lib/clinicianAlerts";
import { POLL_MS } from "@/lib/clinicianPatients";
import { useUi, type UiState } from "@/lib/demo-store";
import { dayKey, parseApiDate } from "@/lib/format";
import { errorMessage, useApi } from "@/lib/useApi";

type FilterKey = "alertLevel" | "alertPatient" | "alertAck" | "alertDate";

const LEVEL_FILTER: Record<string, number> = { urgent: 3, warn: 2, info: 1 };
const DAY_MS = 24 * 60 * 60 * 1000;

function FilterSelect({ name, label, options }: { name: FilterKey; label: string; options: [string, string][] }) {
  const [value, setValue] = useUi(name);
  return (
    <select
      aria-label={label}
      value={value}
      onChange={(e) => setValue(e.target.value as UiState[FilterKey])}
      className={toolbarSelect}
    >
      {options.map(([k, t]) => (
        <option key={k} value={k}>
          {t}
        </option>
      ))}
    </select>
  );
}

/** Filter murni atas daftar alert (level, pasien, peninjauan, hari WIB). */
export function filterAlerts(
  list: ClinicianAlert[],
  f: { level: string; patient: string; ack: string; date: string },
  now: Date,
): ClinicianAlert[] {
  const today = dayKey(now);
  const yesterday = dayKey(new Date(now.getTime() - DAY_MS));
  return list.filter((a) => {
    const day = dayKey(parseApiDate(a.created_at));
    return (
      (f.date === "all" || (f.date === "today" ? day === today : day === yesterday)) &&
      (f.level === "all" || a.level === LEVEL_FILTER[f.level]) &&
      (f.patient === "all" || a.patient_id === f.patient) &&
      (f.ack === "all" || (a.acknowledged ? f.ack === "yes" : f.ack === "no"))
    );
  });
}

export function ClinicianAlertsView() {
  const [level] = useUi("alertLevel");
  const [patient] = useUi("alertPatient");
  const [ack] = useUi("alertAck");
  const [date] = useUi("alertDate");
  const alerts = useApi(fetchAlertCenter, "alert-center", { pollMs: POLL_MS.alerts });
  const patients = useApi(fetchPatients, "alert-center-patients");

  const patientOptions: [string, string][] =
    patients.status === "ready" ? patients.data.map((p): [string, string] => [p.id, p.name]) : [];
  const filters: [FilterKey, string, [string, string][]][] = [
    ["alertLevel", "Filter level", [["all", "Semua level"], ["urgent", "Urgent (level 3)"], ["warn", "Warning (level 2)"], ["info", "Info (level 1)"]]],
    ["alertPatient", "Filter pasien", [["all", "Semua pasien"], ...patientOptions]],
    ["alertAck", "Status peninjauan", [["all", "Semua peninjauan"], ["no", "Belum ditinjau"], ["yes", "Sudah ditinjau"]]],
    ["alertDate", "Tanggal alert", [["all", "Semua tanggal"], ["today", "Hari ini"], ["yesterday", "Kemarin"]]],
  ];

  async function onAcknowledge(id: string) {
    try {
      await acknowledgeAlert(id);
    } catch (error) {
      throw new Error(errorMessage(error));
    }
    if (alerts.status === "ready") alerts.setData((list) => list.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)));
  }

  const now = alerts.status === "ready" ? new Date(alerts.at) : null;
  const list = alerts.status === "ready" && now ? filterAlerts(alerts.data, { level, patient, ack, date }, now) : [];

  return (
    <>
      <Notice>Tinjau alert berdasarkan prioritas. Acknowledge mencatat peninjauan, bukan pemulihan kondisi pasien.</Notice>
      <div className={cn(toolbar, "mt-6")}>
        {filters.map(([name, label, options]) => (
          <FilterSelect key={name} name={name} label={label} options={options} />
        ))}
      </div>
      <div className={notificationsCard}>
        {alerts.status === "loading" && (
          <p role="status" className="py-10 text-center text-muted text-[13px]">
            Memuat alert…
          </p>
        )}
        {alerts.status === "error" && (
          <div role="alert">
            <Notice type="error">{alerts.message}</Notice>
            <button type="button" className={cn(btn({ small: true }), "mt-3")} onClick={alerts.reload}>
              Coba lagi
            </button>
          </div>
        )}
        {alerts.status === "ready" &&
          (list.length ? (
            list.map((a) => (
              <AlertItem key={a.id} alert={toClinicalAlertView(a, now ?? undefined)} clinical onAcknowledge={onAcknowledge} />
            ))
          ) : (
            <Empty
              icon={Bell}
              title={alerts.data.length ? "Tidak ada alert sesuai filter" : "Belum ada alert"}
              text={
                alerts.data.length
                  ? "Ubah filter untuk melihat pemberitahuan lainnya."
                  : "Alert dari pasien dalam pemantauan Anda akan muncul di sini."
              }
            />
          ))}
      </div>
    </>
  );
}
