"use client";

import { AlertItem } from "@/components/portal/AlertItem";
import { notificationsCard, toolbar, toolbarSelect } from "@/components/portal/layout";
import { Bell } from "@/components/ui/Icon";
import { cn, Empty, Notice } from "@/components/ui/primitives";
import { alerts, patients } from "@/lib/demo-data";
import { useDemo, useUi, type UiState } from "@/lib/demo-store";

type FilterKey = "alertLevel" | "alertPatient" | "alertAck" | "alertDate";

const FILTERS: [FilterKey, string, [string, string][]][] = [
  ["alertLevel", "Semua level", [["all", "Semua level"], ["urgent", "Urgent"], ["warn", "Warning"], ["info", "Info"]]],
  ["alertPatient", "Semua pasien", [["all", "Semua pasien"], ...patients.map((p): [string, string] => [p.id, p.name])]],
  ["alertAck", "Status peninjauan", [["all", "Semua peninjauan"], ["no", "Belum ditinjau"], ["yes", "Sudah ditinjau"]]],
  ["alertDate", "Tanggal alert", [["2026-10-10", "Hari ini, 10 Oktober"], ["2026-10-09", "Kemarin, 9 Oktober"], ["all", "Semua tanggal"]]],
];

const SELECT_ID: Record<FilterKey, string> = {
  alertLevel: "alert-level",
  alertPatient: "alert-patient",
  alertAck: "alert-ack",
  alertDate: "alert-date",
};

function FilterSelect({ name, label, options }: { name: FilterKey; label: string; options: [string, string][] }) {
  const [value, setValue] = useUi(name);
  return (
    <select
      id={SELECT_ID[name]}
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

export function ClinicianAlertsView() {
  const [level] = useUi("alertLevel");
  const [patient] = useUi("alertPatient");
  const [ackFilter] = useUi("alertAck");
  const [date] = useUi("alertDate");
  const ackList = useDemo((d) => d.ack);
  const list = alerts.filter(
    (a) =>
      (date === "all" || (date === "2026-10-09" ? a.time.startsWith("Kemarin") : a.time.startsWith("Hari ini"))) &&
      (level === "all" || a.level === level) &&
      (patient === "all" || a.patient === patient) &&
      (ackFilter === "all" || ((a.ack || ackList.includes(a.id)) ? ackFilter === "yes" : ackFilter === "no")),
  );
  return (
    <>
      <Notice>Tinjau alert berdasarkan prioritas. Acknowledge mencatat peninjauan, bukan pemulihan kondisi pasien.</Notice>
      <div className={cn(toolbar, "mt-6")}>
        {FILTERS.map(([name, label, options]) => (
          <FilterSelect key={name} name={name} label={label} options={options} />
        ))}
      </div>
      <div className={notificationsCard}>
        {list.length ? (
          list.map((a) => <AlertItem key={a.id} alert={a} clinical />)
        ) : (
          <Empty icon={Bell} title="Tidak ada alert sesuai filter" text="Ubah filter untuk melihat pemberitahuan lainnya." />
        )}
      </div>
    </>
  );
}
