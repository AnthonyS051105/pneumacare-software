"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { createContext, useContext, useState, type FormEvent, type ReactNode } from "react";
import { useFeedback } from "@/components/providers/Feedback";
import { AlertItem } from "@/components/portal/AlertItem";
import { connectionBar } from "@/components/portal/Connection";
import { chartGrid, formGrid, split, stack } from "@/components/portal/layout";
import { Metric, metricsGrid } from "@/components/portal/Metric";
import { Field, inputClass } from "@/components/ui/Field";
import { ArrowLeft, AudioLines, BatteryMedium, Bell, CircleHelp, Clock3, Icon, Save, Signal, Users } from "@/components/ui/Icon";
import { Avatar, btn, card, cardPad, cn, Empty, LegendItem, Notice, Pill } from "@/components/ui/primitives";
import { VitalChart } from "@/components/ui/VitalChart";
import { ApiError } from "@/lib/api";
import {
  acknowledgeAlert,
  fetchPatient,
  fetchPatientAlerts,
  fetchSeverity,
  fetchThresholds,
  fetchTrend,
  fetchVitalsHistory,
  fetchWheezeCrackleHistory,
  updateThresholds,
  type ClinicianPatient,
  type Thresholds,
  type WheezeCrackleHistory,
} from "@/lib/clinicianApi";
import { toClinicalAlertView } from "@/lib/clinicianAlerts";
import { ageFrom, patientStatus, POLL_MS } from "@/lib/clinicianPatients";
import { values, vitalKeys } from "@/lib/demo-data";
import { formatClockWib, formatEventTime, parseApiDate } from "@/lib/format";
import { detailHref, type DetailTab } from "@/lib/routes";
import { errorMessage, useApi, type ApiState } from "@/lib/useApi";
import { thresholdErrors, thresholdKeys, type FieldErrors } from "@/lib/validation";
import { BUCKET_MS, GAP_BUCKETS, RANGE_MS, seriesFor, tickLabels } from "@/lib/vitals";

/* ---------- Data pasien (dimuat sekali per halaman detail, di-polling untuk vital terbaru) ---------- */

type PatientCtx = { patient: ClinicianPatient; reload: () => void };
const PatientContext = createContext<PatientCtx | null>(null);

function usePatientCtx(): PatientCtx {
  const ctx = useContext(PatientContext);
  if (!ctx) throw new Error("Komponen detail pasien harus berada di dalam <ClinicianPatientProvider>");
  return ctx;
}

export function ClinicianPatientProvider({ id, children }: { id: string; children: ReactNode }) {
  const state = useApi(() => fetchPatient(id), `patient:${id}`, { pollMs: POLL_MS.vitals });
  if (state.status === "loading") {
    return (
      <p role="status" className="py-16 text-center text-muted text-[13px]">
        Memuat data pasien…
      </p>
    );
  }
  if (state.status === "error") {
    return state.httpStatus === 404 ? (
      <div className={cn(card, cardPad)}>
        <Empty
          icon={Users}
          title="Pasien tidak ditemukan"
          text="Pasien ini tidak ada atau tidak berada dalam daftar pemantauan Anda."
          action={
            <Link href="/clinician/patients" className={btn()}>
              Kembali ke daftar pasien
            </Link>
          }
        />
      </div>
    ) : (
      <ErrorBlock message={state.message} retry={state.reload} />
    );
  }
  return (
    <PatientContext.Provider value={{ patient: state.data, reload: state.reload }}>{children}</PatientContext.Provider>
  );
}

function ErrorBlock({ message, retry }: { message: string; retry: () => void }) {
  return (
    <div role="alert">
      <Notice type="error">{message}</Notice>
      <button type="button" className={cn(btn({ small: true }), "mt-3")} onClick={retry}>
        Coba lagi
      </button>
    </div>
  );
}

function Loading({ text = "Memuat…" }: { text?: string }) {
  return (
    <p role="status" className="py-10 text-center text-muted text-[13px]">
      {text}
    </p>
  );
}

/** Render konten berdasarkan status `useApi`. */
function Async<T>({ state, children, label }: { state: ApiState<T>; children: (data: T) => ReactNode; label?: string }) {
  if (state.status === "loading") return <Loading text={label} />;
  if (state.status === "error") return <ErrorBlock message={state.message} retry={state.reload} />;
  return <>{children(state.data)}</>;
}

const TABS: [DetailTab, string][] = [
  ["vitals", "Vital Real-time"],
  ["trends", "Tren & Severity"],
  ["alerts", "Riwayat Alert"],
  ["thresholds", "Konfigurasi Ambang"],
];

const clock = (iso: string | null | undefined) => (iso ? formatClockWib(parseApiDate(iso)) : null);

export function DetailHeader() {
  const { patient: p } = usePatientCtx();
  const pathname = usePathname();
  const online = p.device?.status === "online";
  const age = ageFrom(p.date_of_birth);
  const lastSeen = clock(p.device?.last_seen_at) ?? clock(p.latest_vitals.timestamp);
  return (
    <>
      <Link href="/clinician/patients" className="flex items-center gap-3 text-muted mb-5">
        <Icon icon={ArrowLeft} /> Kembali ke daftar pasien
      </Link>
      <div className={cn(card, "flex flex-wrap items-center gap-4 p-[22px] max-md:gap-3")}>
        <div className="flex items-center gap-3 *:min-w-0 max-md:flex-wrap">
          <Avatar name={p.name} size="lg" />
          <div>
            <h2 className="text-[21px]">{p.name}</h2>
            <p className="text-muted text-[12px] [overflow-wrap:anywhere]">
              {age !== null ? age + " tahun" : "Usia belum tersedia"}
              {p.email ? `, ${p.email}` : ""} ({p.device?.device_id ?? "belum ada rompi"})
            </p>
          </div>
        </div>
        <div className="ml-auto max-md:ml-0">
          <Pill tone={online ? "" : "off"} className="mt-2">
            {!p.device ? "Belum ada rompi" : online ? "Perangkat terhubung" : "Perangkat offline"}
          </Pill>
          {lastSeen && (
            <p className="text-[12px]">
              <small>Terakhir terhubung {lastSeen}</small>
            </p>
          )}
        </div>
      </div>
      <nav
        aria-label="Detail pasien"
        className="flex gap-7 mt-5 mb-6 border-b border-line overflow-x-auto max-md:gap-[22px] max-md:my-5"
      >
        {TABS.map(([tab, label]) => {
          const href = detailHref(p.id, tab);
          const active = pathname === href;
          return (
            <Link
              key={tab}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "whitespace-nowrap px-0.5 py-3 border-b-2 text-[13px] max-md:text-[12px] max-md:py-[11px] max-md:min-h-11",
                active ? "border-primary text-navy font-semibold" : "border-transparent text-muted font-medium",
              )}
            >
              {label}
            </Link>
          );
        })}
      </nav>
    </>
  );
}

/* ---------- Vital real-time ---------- */

const SIGNAL_LABEL = { good: "baik", fair: "cukup", poor: "lemah" } as const;
const toMs = (iso: string) => parseApiDate(iso).getTime();

export function VitalsTab() {
  const { patient: p } = usePatientCtx();
  const online = p.device?.status === "online";
  const latest = p.latest_vitals;
  const updatedAt = clock(latest.timestamp);
  const history = useApi(
    () => {
      const now = new Date();
      return fetchVitalsHistory(p.id, new Date(now.getTime() - RANGE_MS["24h"]), now);
    },
    `vitals-history:${p.id}`,
    { pollMs: 60_000 },
  );
  const ready = history.status === "ready" ? history : null;
  const domain: [number, number] | undefined = ready ? [ready.at - RANGE_MS["24h"], ready.at] : undefined;
  const battery = p.device?.battery_percent;

  return (
    <div className={stack}>
      {!p.device ? (
        <Notice type="warn">Pasien belum memiliki rompi terhubung. Belum ada data vital.</Notice>
      ) : (
        !online && (
          <Notice type="warn">
            Perangkat offline. Kondisi terkini belum diketahui. Nilai terakhir tidak ditampilkan sebagai pembacaan
            terkini.
          </Notice>
        )
      )}
      <div className={metricsGrid}>
        {vitalKeys.map((k) => {
          const raw = latest[k];
          return (
            <Metric
              key={k}
              vital={k}
              clinical
              unknown={!online || raw === null}
              val={raw === null ? undefined : Math.round(raw)}
              updatedAt={updatedAt}
              points={ready ? seriesFor(ready.data, k, "24h", toMs) : []}
              domain={domain}
              gapMs={BUCKET_MS["24h"] * GAP_BUCKETS}
            />
          );
        })}
      </div>
      <div className={chartGrid}>
        {vitalKeys.map((k) => (
          <div key={k} className={cn(card, cardPad)}>
            <div className="flex items-center justify-between gap-3 mb-5 *:min-w-0">
              <h3>{values[k].technical}</h3>
              <small>24 jam terakhir</small>
            </div>
            {history.status === "error" ? (
              <ErrorBlock message={history.message} retry={history.reload} />
            ) : ready && domain ? (
              <VitalChart
                vital={k}
                points={seriesFor(ready.data, k, "24h", toMs)}
                domain={domain}
                gapMs={BUCKET_MS["24h"] * GAP_BUCKETS}
                labels={tickLabels(domain[0], domain[1], "24h")}
              />
            ) : (
              <Loading text="Memuat grafik…" />
            )}
          </div>
        ))}
        <div className={cn(card, cardPad)}>
          <h3 className="mb-5">Kualitas Sinyal</h3>
          <dl className="grid grid-cols-[auto_1fr] gap-x-5 gap-y-3 text-[12px]">
            <dt className="text-muted">PPG</dt>
            <dd>
              {!online
                ? "Tidak tersedia (perangkat offline)"
                : p.device?.signal_quality_ppg
                  ? SIGNAL_LABEL[p.device.signal_quality_ppg]
                  : "Belum diukur"}
            </dd>
            <dt className="text-muted">Audio</dt>
            <dd>
              {online && p.device?.signal_quality_audio
                ? Object.entries(p.device.signal_quality_audio)
                    .map(([ch, q]) => `${ch}: ${SIGNAL_LABEL[q] ?? q}`)
                    .join(", ")
                : online
                  ? "Belum diukur"
                  : "Tidak tersedia"}
            </dd>
          </dl>
          {!p.device?.signal_quality_ppg && !p.device?.signal_quality_audio && (
            <p className="text-[11px] text-muted mt-5">
              Kualitas sinyal belum dikirim perangkat pada versi firmware ini, jadi belum dapat ditampilkan.
            </p>
          )}
        </div>
      </div>
      <div className={connectionBar}>
        <Icon icon={BatteryMedium} className="size-[17px] max-md:size-4" />
        {`Baterai ${battery != null ? Math.round(battery) + "%" : "—"} `}
        <Icon icon={Signal} className="size-[17px] max-md:size-4" />
        {online ? "Online " : "Offline "}
        <Icon icon={Clock3} className="size-[17px] max-md:size-4" />
        Pembaruan {updatedAt ?? "—"}
      </div>
    </div>
  );
}

/* ---------- Tren & hasil skrining Model A ---------- */

const CHANNELS = ["Posterior kiri atas", "Posterior kanan atas", "Posterior kiri bawah", "Posterior kanan bawah"];
const CLASS_LABEL = { none: "Tidak terdeteksi", crackle: "Crackle", wheeze: "Wheeze", both: "Wheeze + crackle" } as const;
const CLASS_ORDER = ["wheeze", "crackle", "both", "none"] as const;
const pct = (v: number | null | undefined) => (v == null ? "—" : `${Math.round(v * 100)}%`);

const ring =
  "grid place-items-center size-[95px] rounded-full my-[18px] mx-auto before:content-[''] before:size-[78px] before:bg-white before:rounded-full before:[grid-area:1/1]";

export function TrendsTab() {
  const { patient: p } = usePatientCtx();
  const severity = useApi(() => fetchSeverity(p.id), `severity:${p.id}`, { pollMs: POLL_MS.alerts });
  const trend = useApi(() => fetchTrend(p.id), `trend:${p.id}`, { pollMs: POLL_MS.alerts });
  const wc = useApi(() => fetchWheezeCrackleHistory(p.id, "7d"), `wc:${p.id}`, { pollMs: 5 * 60_000 });
  const rr = useApi(
    () => {
      const now = new Date();
      return fetchVitalsHistory(p.id, new Date(now.getTime() - RANGE_MS["7d"]), now);
    },
    `rr7:${p.id}`,
    { pollMs: 5 * 60_000 },
  );

  return (
    <div className={stack}>
      <Notice>
        Hasil skrining memerlukan peninjauan tenaga medis. Model wheeze/crackle ini adalah checkpoint pengembangan, belum
        divalidasi klinis.
      </Notice>
      <div className={split}>
        <div className={cn(card, cardPad)}>
          <h3>Analisis Suara Paru</h3>
          <p className="text-muted">Hasil segmen terbaru dari empat kanal posterior</p>
          <Async state={severity} label="Memuat hasil skrining…">
            {(c) =>
              !c ? (
                <Empty
                  icon={AudioLines}
                  title="Belum ada hasil analisis"
                  text="Hasil muncul setelah rompi mengirim audio dan model memprosesnya."
                />
              ) : (
                <>
                  <div className="grid min-w-0 grid-cols-4 gap-3 mt-6 max-2xl:grid-cols-2 max-md:grid-cols-[1fr_1fr] max-md:gap-4">
                    {CHANNELS.map((t, i) => (
                      <div
                        key={t}
                        className={cn(
                          "border-b py-4 px-1 text-center text-[11px]",
                          c.channel_id === i + 1 ? "border-primary bg-[#f2f9f6]" : "border-line",
                        )}
                      >
                        <Icon icon={AudioLines} className="text-primary mb-2" />
                        <br />
                        {t}
                        <br />
                        <small>{c.channel_id === i + 1 ? "Segmen terbaru" : "Kanal " + (i + 1)}</small>
                      </div>
                    ))}
                  </div>
                  <div className="grid grid-cols-[1fr_1fr] gap-0 mt-6 border-t border-line pt-[22px]">
                    <div className="text-center px-[15px] py-1">
                      <h4>Kelas terdeteksi</h4>
                      <div
                        className={ring}
                        style={{
                          background: `conic-gradient(var(--color-primary) 0 ${Math.round(c.wheeze_crackle_confidence * 100)}%,#e4eeea ${Math.round(c.wheeze_crackle_confidence * 100)}%)`,
                        }}
                      >
                        <strong className="[grid-area:1/1] text-[20px] z-[1]">{pct(c.wheeze_crackle_confidence)}</strong>
                      </div>
                      <strong className="text-[13px]">{CLASS_LABEL[c.wheeze_crackle_class] ?? c.wheeze_crackle_class}</strong>
                      <br />
                      <small>Confidence</small>
                    </div>
                    <div className="px-[15px] py-1 border-l border-line">
                      <h4 className="text-center mb-3">Probabilitas per kelas</h4>
                      {CLASS_ORDER.map((k) => {
                        const v = c.wheeze_crackle_probabilities?.[k];
                        return (
                          <div key={k} className="mb-2.5 text-[11px]">
                            <div className="flex justify-between">
                              <span>{CLASS_LABEL[k]}</span>
                              <b>{pct(v)}</b>
                            </div>
                            <div className="h-[5px] mt-1 rounded-[4px] bg-[#e5eeeb] overflow-hidden">
                              <span
                                className="block h-full rounded-[inherit] bg-[#398c80]"
                                style={{ width: `${Math.round((v ?? 0) * 100)}%` }}
                              />
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  <p className="text-[11px] text-muted mt-3.5">
                    Segmen {formatEventTime(c.segment_end)} · model {c.wheeze_crackle_model_version}. Confidence bukan
                    peluang diagnosis. Interpretasi membutuhkan peninjauan tenaga medis.
                  </p>
                </>
              )
            }
          </Async>
        </div>
        <div className={stack}>
          <div className={cn(card, cardPad)}>
            <h3>Severity Skrining</h3>
            <Empty
              icon={CircleHelp}
              title="Belum tersedia"
              text="Model severity (Model B) masih ditunda tim, sehingga belum ada hasil yang dapat ditampilkan."
              action={<Pill tone="off">Belum tersedia</Pill>}
            />
          </div>
          <div className={cn(card, cardPad)}>
            <h3>Tren Wheeze/Crackle Terbaru</h3>
            <Async state={trend} label="Memuat tren…">
              {(t) =>
                !t ? (
                  <p className="text-muted mt-3">Belum ada evaluasi tren untuk pasien ini.</p>
                ) : (
                  <div className="mt-3 text-[12px]">
                    <p>
                      Arah: <b>{t.slope > 0 ? "naik" : t.slope < 0 ? "turun" : "datar"}</b> (slope{" "}
                      {Math.round(t.slope * 1000) / 1000} per menit)
                    </p>
                    <div className="mt-3">
                      <Pill tone={t.significant ? "warn" : ""}>{t.significant ? "Signifikan" : "Tidak signifikan"}</Pill>
                    </div>
                    <p className="text-[11px] text-muted mt-3">
                      Jendela s.d. {formatEventTime(t.window_end)}. Ambang signifikansi masih parameter sementara, belum
                      dikonfirmasi tim model.
                    </p>
                  </div>
                )
              }
            </Async>
          </div>
        </div>
      </div>
      <div className={cn(card, cardPad)}>
        <div className="flex items-center justify-between gap-3 mb-5 *:min-w-0">
          <div>
            <h3>Frekuensi Wheeze/Crackle</h3>
            <small>Proporsi segmen berlabel wheeze, crackle, atau keduanya per 6 jam</small>
          </div>
          <Pill>7 hari</Pill>
        </div>
        <Async state={wc} label="Memuat riwayat…">
          {(data) => <RatioBars data={data} />}
        </Async>
      </div>
      <div className={cn(card, cardPad)}>
        <div className="flex items-center justify-between gap-3 mb-5 *:min-w-0">
          <div>
            <h3>Tren Frekuensi Napas</h3>
            <small>7 hari terakhir</small>
          </div>
          <Pill>7 hari</Pill>
        </div>
        <Async state={rr} label="Memuat grafik…">
          {(readings) => {
            // Di dalam <Async> status selalu "ready"; `at` = waktu data diambil (bukan Date.now saat render).
            const at = rr.status === "ready" ? rr.at : 0;
            const domain: [number, number] = [at - RANGE_MS["7d"], at];
            return (
              <VitalChart
                vital="rr"
                points={seriesFor(readings, "rr", "7d", toMs)}
                domain={domain}
                gapMs={BUCKET_MS["7d"] * GAP_BUCKETS}
                labels={tickLabels(domain[0], domain[1], "7d")}
              />
            );
          }}
        </Async>
        <div className="flex flex-wrap gap-[18px] mt-3 text-[11px] text-muted">
          <LegendItem>Laju napas (napas/menit), rata-rata per 2 jam</LegendItem>
          <small>Jeda menunjukkan data yang tidak tersedia</small>
        </div>
      </div>
    </div>
  );
}

/** Batang proporsi per bucket; bucket tanpa segmen dibiarkan kosong (bukan 0%). */
function RatioBars({ data }: { data: WheezeCrackleHistory }) {
  const total = data.buckets.reduce((sum, b) => sum + b.total, 0);
  if (!total) return <p className="py-10 text-center text-muted text-[13px]">Belum ada hasil klasifikasi pada periode ini.</p>;
  const w = 620;
  const h = 210;
  const left = 36;
  const right = w - 10;
  const top = 16;
  const bottom = 177;
  const slot = (right - left) / data.buckets.length;
  const start = parseApiDate(data.start).getTime();
  const end = parseApiDate(data.end).getTime();
  const labels = tickLabels(start, end, "7d");
  return (
    <svg
      className="block w-full h-auto overflow-visible aspect-[620/210] min-h-[130px]"
      viewBox={`0 0 ${w} ${h}`}
      preserveAspectRatio="none"
      role="img"
      aria-label="Grafik proporsi segmen wheeze/crackle per 6 jam, 7 hari terakhir"
    >
      {[0, 0.5, 1].map((r) => {
        const y = bottom - r * (bottom - top);
        return (
          <g key={r}>
            <line stroke="#e7ece7" x1={left} x2={right} y1={y} y2={y} />
            <text x="2" y={y + 4} fill="#68766b" fontSize="11" fontFamily="Arial, sans-serif">
              {Math.round(r * 100)}%
            </text>
          </g>
        );
      })}
      {data.buckets.map((b, i) =>
        b.abnormal_ratio === null ? null : (
          <rect
            key={b.bucket_start}
            x={left + i * slot + slot * 0.15}
            width={slot * 0.7}
            y={bottom - b.abnormal_ratio * (bottom - top)}
            height={Math.max(b.abnormal_ratio * (bottom - top), 1)}
            fill="var(--color-primary)"
            opacity=".8"
          >
            <title>{`${formatEventTime(b.bucket_start)}: ${Math.round(b.abnormal_ratio * 100)}% dari ${b.total} segmen`}</title>
          </rect>
        ),
      )}
      {labels.map((t, j) => (
        <text
          key={j}
          x={left + (j * (right - left)) / 6}
          y="202"
          textAnchor={j === 0 ? "start" : j === 6 ? "end" : "middle"}
          fill="#68766b"
          fontSize="11"
          fontFamily="Arial, sans-serif"
        >
          {t}
        </text>
      ))}
    </svg>
  );
}

/* ---------- Riwayat alert ---------- */

export function AlertsTab() {
  const { patient: p, reload } = usePatientCtx();
  const state = useApi(() => fetchPatientAlerts(p.id), `alerts:${p.id}`, { pollMs: POLL_MS.alerts });

  async function onAcknowledge(id: string) {
    try {
      await acknowledgeAlert(id);
    } catch (error) {
      throw new Error(errorMessage(error));
    }
    if (state.status === "ready") state.setData((list) => list.map((a) => (a.id === id ? { ...a, acknowledged: true } : a)));
    reload();
  }

  return (
    <>
      <Notice>Acknowledge menandai alert sudah ditinjau. Tindakan ini tidak berarti kondisi pasien telah pulih.</Notice>
      <div className={cn(card, cardPad, "mt-6")}>
        <div className="flex items-center justify-between gap-3 mb-5 *:min-w-0">
          <h3>Riwayat Alert Pasien</h3>
          <Pill tone={patientStatus(p) === "urgent" ? "urgent" : patientStatus(p) === "warn" ? "warn" : ""}>
            {p.open_alert_level ? "Ada alert belum ditinjau" : "Semua alert sudah ditinjau"}
          </Pill>
        </div>
        <Async state={state} label="Memuat alert…">
          {(list) =>
            list.length ? (
              list.map((a) => (
                <AlertItem key={a.id} alert={toClinicalAlertView({ ...a, patient_name: null })} clinical onAcknowledge={onAcknowledge} />
              ))
            ) : (
              <Empty icon={Bell} title="Belum ada alert" text="Alert pasien akan ditampilkan di sini." />
            )
          }
        </Async>
      </div>
    </>
  );
}

/* ---------- Konfigurasi ambang ---------- */

// TODO_CLINICAL_VALUE: ambang HR/SpO₂/RR sengaja tidak diberi nilai default — wajib diisi
// tenaga medis sesuai rencana pemantauan (lihat CLAUDE.md, larangan mengisi angka klinis).
const FORM_TO_API = {
  hrmin: "hr_min",
  hrmax: "hr_max",
  spo2min: "spo2_min",
  rrmin: "rr_min",
  rrmax: "rr_max",
} as const satisfies Record<(typeof thresholdKeys)[number], keyof Thresholds>;

function toForm(t: Thresholds): Record<string, string> {
  const form: Record<string, string> = { actionplan: t.action_plan ?? "" };
  for (const k of thresholdKeys) {
    const v = t[FORM_TO_API[k]];
    form[k] = v == null ? "" : String(v);
  }
  return form;
}

export function ThresholdsTab() {
  const { patient: p } = usePatientCtx();
  const state = useApi(() => fetchThresholds(p.id), `thresholds:${p.id}`);
  return (
    <Async state={state} label="Memuat konfigurasi…">
      {(t) => (
        <ThresholdsForm
          key={t.updated_at ?? "baru"}
          patientId={p.id}
          saved={t}
          onSaved={(next) => state.status === "ready" && state.setData(() => next)}
        />
      )}
    </Async>
  );
}

function ThresholdsForm({
  patientId,
  saved,
  onSaved,
}: {
  patientId: string;
  saved: Thresholds;
  onSaved: (t: Thresholds) => void;
}) {
  const { toast } = useFeedback();
  const initial = toForm(saved);
  const [errors, setErrors] = useState<FieldErrors>({});
  const [formError, setFormError] = useState("");
  const [saving, setSaving] = useState(false);
  const [valid, setValid] = useState(() => thresholdErrors(initial) === null);
  const read = (form: HTMLFormElement) => Object.fromEntries(new FormData(form)) as Record<string, string>;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (saving) return;
    const v = read(event.currentTarget);
    const next = thresholdErrors(v);
    setFormError("");
    if (next) return setErrors(next);
    setErrors({});
    setSaving(true);
    try {
      const body = Object.fromEntries(thresholdKeys.map((k) => [FORM_TO_API[k], Number(v[k])]));
      const result = await updateThresholds(patientId, { ...body, action_plan: v.actionplan ?? "" });
      onSaved(result);
      toast("Konfigurasi berhasil disimpan.");
    } catch (error) {
      setFormError(error instanceof ApiError ? error.message : errorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  const num = (name: (typeof thresholdKeys)[number], label: string, hint?: string) => (
    <Field name={name} label={label} type="number" defaultValue={initial[name]} hint={hint} required error={errors[name]} />
  );

  return (
    <div className={stack}>
      <section className={cn(card, cardPad)}>
        <h3 className="mb-2">Konfigurasi Ambang Vital</h3>
        <p className="text-[12px] text-muted mb-5">
          {saved.updated_at
            ? `Terakhir diubah ${formatEventTime(saved.updated_at)}.`
            : "Belum dikonfigurasi. Selama ambang kosong, sistem tidak membuat alert vital untuk pasien ini."}
        </p>
        <form noValidate onSubmit={submit} onInput={(e) => setValid(thresholdErrors(read(e.currentTarget)) === null)}>
          <div className={formGrid}>
            {num("hrmin", "HR minimum (bpm)", "Isi sesuai rencana pemantauan")}
            {num("hrmax", "HR maksimum (bpm)", "Harus lebih besar dari minimum")}
            {num("spo2min", "SpO₂ batas bawah (%)", "Nilai 1–100")}
            <div />
            {num("rrmin", "RR minimum (napas/menit)")}
            {num("rrmax", "RR maksimum (napas/menit)", "Harus lebih besar dari minimum")}
          </div>
          <h3 className="mt-6 mb-5">Rencana Tindakan Pasien</h3>
          <div className="block min-w-0">
            <label htmlFor="actionplan" className="block font-medium text-[12px] mb-[7px]">
              Arahan tenaga medis
            </label>
            <textarea
              id="actionplan"
              name="actionplan"
              defaultValue={initial.actionplan}
              placeholder="Tulis rencana tindakan individual pasien..."
              className={cn(inputClass, "min-h-[115px] resize-y")}
            />
          </div>
          <div role="alert">{formError && <Notice type="error">{formError}</Notice>}</div>
          <button type="submit" disabled={!valid || saving} className={cn(btn({ variant: "primary" }), "mt-6")}>
            <Icon icon={Save} />
            {saving ? "Menyimpan…" : "Simpan Konfigurasi"}
          </button>
          <p className="text-[11px] text-muted mt-[5px]">Lengkapi angka yang valid untuk mengaktifkan tombol simpan.</p>
        </form>
      </section>
    </div>
  );
}
