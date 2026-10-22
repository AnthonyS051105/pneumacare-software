"use client";

import Image from "next/image";
import Link from "next/link";
import careClinician from "@/assets/care-clinician.png";
import { ModalButton } from "@/components/providers/Feedback";
import { ChevronRight, CircleAlert, Icon, Plus, Search, TriangleAlert, Users, WifiOff } from "@/components/ui/Icon";
import { useEffect } from "react";
import { Avatar, btn, card, cn, Empty, Notice, Pill, type PillTone } from "@/components/ui/primitives";
import { fetchPatients, type ClinicianPatient } from "@/lib/clinicianApi";
import { ageFrom, CLINICIAN_RELOAD_EVENT, patientStatus, POLL_MS } from "@/lib/clinicianPatients";
import { statusOrder, type PatientStatus } from "@/lib/demo-data";
import { useUi } from "@/lib/demo-store";
import { formatClockWib, parseApiDate } from "@/lib/format";
import { toolbar, toolbarSelect } from "@/components/portal/layout";
import { detailHref } from "@/lib/routes";
import { useApi } from "@/lib/useApi";

type Row = ClinicianPatient & { status: PatientStatus; online: boolean };

const round = (v: number | null) => (v === null ? "N/A" : String(Math.round(v)));


const SUMMARY_ICON_COLOR: Record<PillTone, string> = {
  "": "text-[#237769]",
  urgent: "text-red",
  warn: "text-amber",
  off: "text-[#5f6e65]",
};

const STATUS_LABEL = { urgent: "Urgent", warn: "Warning", off: "Belum diketahui", stable: "Stabil" };

const td =
  "px-4 py-[19px] border-b border-line align-middle tabular-nums group-last/row:border-b-0 max-md:block max-md:p-0 max-md:border-0 max-md:min-w-0 max-md:before:content-[attr(data-label)] max-md:before:block max-md:before:text-[10px] max-md:before:text-muted max-md:before:mb-1";
const th = "text-left bg-[#f3f8f6] text-[#627464] text-[11px] font-medium px-4 py-3.5 whitespace-nowrap";

export function ClinicianPatientsView() {
  const [filter, setFilter] = useUi("patientFilter");
  const [search, setSearch] = useUi("searchText");
  const [sort, setSort] = useUi("sortOrder");
  const state = useApi(fetchPatients, "patients", { pollMs: POLL_MS.list });
  const { reload } = state;

  useEffect(() => {
    window.addEventListener(CLINICIAN_RELOAD_EVENT, reload);
    return () => window.removeEventListener(CLINICIAN_RELOAD_EVENT, reload);
  }, [reload]);

  const all: Row[] =
    state.status === "ready"
      ? state.data.map((p) => ({ ...p, status: patientStatus(p), online: p.device?.status === "online" }))
      : [];
  const list = all
    .filter(
      (p) =>
        (filter === "all" || p.status === filter) &&
        [p.name, p.device?.device_id ?? "", p.email ?? "", p.id].join(" ").toLowerCase().includes(search.toLowerCase()),
    )
    // Urutan prioritas: status, lalu level alert terbuka (urutan backend, FR-SW-057), lalu nama.
    .sort((a, b) =>
      sort === "name"
        ? a.name.localeCompare(b.name)
        : statusOrder[a.status] - statusOrder[b.status] || a.name.localeCompare(b.name),
    );

  const summary: [string, number, typeof Users, PillTone][] = [
    ["Total pasien", all.length, Users, ""],
    ["Perlu perhatian", all.filter((p) => p.status === "urgent").length, CircleAlert, "urgent"],
    ["Peringatan", all.filter((p) => p.status === "warn").length, TriangleAlert, "warn"],
    ["Perangkat offline", all.filter((p) => !p.online).length, WifiOff, "off"],
  ];

  return (
    <>
      <section className="grid grid-cols-[minmax(0,1fr)_144px] gap-5 items-center mb-7 max-2xl:grid-cols-[minmax(0,1fr)] max-md:mb-[22px]">
        <div className="grid min-w-0 grid-cols-4 gap-0 bg-white border border-line rounded-[8px] overflow-hidden max-tb:grid-cols-2">
          {summary.map(([title, count, icon, tone]) => {
            const key = tone || "all";
            const selected = filter === key;
            return (
              <button
                key={title}
                type="button"
                aria-pressed={selected}
                onClick={() => setFilter(key)}
                className={cn(
                  "min-w-0 p-6 text-left text-ink border-0 border-r border-line last:border-r-0 transition-[background,box-shadow] duration-180 ease-[ease] max-2xl:p-[17px] max-tb:border-b max-tb:nth-2:border-r-0 max-tb:nth-[n+3]:border-b-0 max-xs:p-[15px]",
                  selected ? "bg-[#edf7f3] shadow-[inset_0_-3px_var(--color-primary)]" : "bg-white hover:bg-[#f2f9f6]",
                )}
              >
                <span className="flex items-start justify-between gap-2.5 text-[12px] *:min-w-0 max-md:text-[11px]">
                  <span>{title}</span>
                  <span
                    className={cn(
                      "inline-flex items-center gap-1.5 text-[11px] font-semibold rounded-[4px] whitespace-nowrap leading-[1.6] bg-transparent p-0",
                      SUMMARY_ICON_COLOR[tone],
                    )}
                  >
                    <Icon icon={icon} />
                  </span>
                </span>
                <span className="block text-[32px] leading-[1.3] font-medium mt-2.5 tracking-[-1px] tabular-nums max-md:text-[28px]">
                  {count}
                </span>
                <span className="block text-[11px] text-muted mt-[5px] max-md:text-[10px]">
                  {tone ? "Lihat pasien" : "Dalam pemantauan"}
                </span>
              </button>
            );
          })}
        </div>
        <div className="h-[130px] bg-mint rounded-[12px] overflow-hidden max-2xl:hidden">
          <Image
            src={careClinician}
            alt="Tenaga medis meninjau pemantauan pasien"
            sizes="144px"
            className="w-full h-full object-contain"
          />
        </div>
      </section>

      <div className="flex items-center justify-between gap-3 mb-5 *:min-w-0">
        <h3>Daftar Pasien</h3>
        <ModalButton kind="add" className={btn({ variant: "primary", small: true })}>
          <Icon icon={Plus} />
          Tambah Pasien
        </ModalButton>
      </div>
      <div className={toolbar}>
        <div className="block relative flex-1 min-w-[190px] max-md:basis-full">
          <Icon icon={Search} className="absolute left-[13px] top-[13px] text-muted size-[18px]" />
          <input
            id="patient-search"
            aria-label="Cari pasien"
            placeholder="Cari nama, email, atau ID perangkat..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full border border-[#cdd8cf] rounded-[5px] py-[11px] pr-3 pl-10 bg-white text-ink min-h-[45px] leading-[1.5]"
          />
        </div>
        <select
          id="patient-filter"
          aria-label="Filter status"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          className={toolbarSelect}
        >
          <option value="all">Semua status</option>
          <option value="urgent">Urgent</option>
          <option value="warn">Warning</option>
          <option value="stable">Stabil</option>
          <option value="off">Offline</option>
        </select>
        <select
          id="patient-sort"
          aria-label="Urutkan pasien"
          value={sort}
          onChange={(e) => setSort(e.target.value as "priority" | "name")}
          className={toolbarSelect}
        >
          <option value="priority">Prioritas perhatian</option>
          <option value="name">Nama A–Z</option>
        </select>
      </div>

      {state.status === "error" && (
        <div role="alert" className="mb-5">
          <Notice type="error">{state.message}</Notice>
          <button type="button" className={cn(btn({ small: true }), "mt-3")} onClick={state.reload}>
            Coba lagi
          </button>
        </div>
      )}
      <div className={cn(card, "p-0 overflow-hidden max-2xl:p-5 max-md:p-0")}>
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-[12px] max-md:block">
            <thead className="max-md:hidden">
              <tr>
                <th className={th}>Pasien</th>
                <th className={th}>HR (bpm)</th>
                <th className={th}>SpO₂ (%)</th>
                <th className={th}>RR (/menit)</th>
                <th className={th}>Status</th>
                <th className={th}>Perangkat</th>
                <th className={th}>Pembaruan</th>
                <th className={th}></th>
              </tr>
            </thead>
            <tbody className="max-md:block">
              {list.map((p) => (
                <tr
                  key={p.id}
                  className="group/row hover:bg-[#fafbf8] max-md:grid max-md:grid-cols-3 max-md:gap-3.5 max-md:p-5 max-md:border-b max-md:border-line max-xs:grid-cols-[1fr_1fr]"
                >
                  <td data-label="Pasien" className={cn(td, "max-md:col-span-full max-md:mb-1 max-md:before:hidden")}>
                    <div className="flex items-center gap-2.5 font-medium min-w-[160px] max-md:min-w-0">
                      <Avatar name={p.name} />
                      <div>
                        <Link href={detailHref(p.id)} className="font-semibold">
                          {p.name}
                        </Link>
                        <small className="block text-[10px] mt-[3px]">
                          {(() => {
                            const age = ageFrom(p.date_of_birth);
                            return age !== null ? age + " tahun, " : "";
                          })()}
                          {p.device?.device_id ?? "Belum ada rompi"}
                        </small>
                      </div>
                    </div>
                  </td>
                  <td data-label="HR (bpm)" className={td}>
                    {p.online ? round(p.latest_vitals.hr) : "N/A"}
                  </td>
                  <td data-label="SpO₂ (%)" className={td}>
                    {p.online ? round(p.latest_vitals.spo2) : "N/A"}
                  </td>
                  <td data-label="RR (/menit)" className={td}>
                    {p.online ? round(p.latest_vitals.rr) : "N/A"}
                  </td>
                  <td data-label="Status" className={td}>
                    <Pill tone={p.status === "stable" ? "" : p.status} className="max-md:text-[10px]">
                      {STATUS_LABEL[p.status]}
                    </Pill>
                  </td>
                  <td data-label="Perangkat" className={td}>
                    <Pill tone={p.online ? "" : "off"} className="max-md:text-[10px]">
                      {p.online ? "Online" : "Offline"}
                    </Pill>
                  </td>
                  <td data-label="Pembaruan" className={td}>
                    {p.latest_vitals.timestamp ? formatClockWib(parseApiDate(p.latest_vitals.timestamp)) : "—"}
                    <small className="block text-[10px] mt-[3px]">
                      {!p.latest_vitals.timestamp
                        ? "Belum ada data"
                        : p.online
                          ? "Data terkini"
                          : "Nilai terkini tidak tersedia"}
                    </small>
                  </td>
                  <td className={cn(td, "max-md:self-end max-md:text-right")}>
                    <Link
                      href={detailHref(p.id)}
                      aria-label={`Lihat detail ${p.name}`}
                      className={btn({ variant: "ghost", small: true })}
                    >
                      <Icon icon={ChevronRight} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {state.status === "loading" && (
            <p role="status" className="py-10 text-center text-muted text-[13px]">
              Memuat daftar pasien…
            </p>
          )}
          {state.status === "ready" && !all.length && (
            <Empty
              icon={Users}
              title="Belum ada pasien"
              text="Tambahkan pasien memakai email akun pasien yang sudah terdaftar."
            />
          )}
          {state.status === "ready" && all.length > 0 && !list.length && (
            <Empty icon={Search} title="Pasien tidak ditemukan" text="Coba nama atau filter yang berbeda." />
          )}
        </div>
      </div>
    </>
  );
}
