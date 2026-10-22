"use client";

import { useFeedback } from "@/components/providers/Feedback";
import { chartGrid } from "@/components/portal/layout";
import { ChartIcon } from "@/components/portal/VitalIcon";
import { Download, Icon, WifiOff } from "@/components/ui/Icon";
import { btn, card, cardPad, cn, Empty, LegendItem, Notice, segmentButton, segments } from "@/components/ui/primitives";
import { VitalChart } from "@/components/ui/VitalChart";
import { values, vitalKeys } from "@/lib/demo-data";
import { useUi, type UiState } from "@/lib/demo-store";
import { formatClock, formatDayMonth, formatFullDate, parseApiDate } from "@/lib/format";
import type { PatientHistory, TimeRange } from "@/lib/patientApi";
import { usePatientHistory } from "@/lib/usePatientHistory";
import { BUCKET_MS, GAP_BUCKETS, RANGE_MS, seriesFor, tickLabels } from "@/lib/vitals";

const RANGES: UiState["historyRange"][] = ["24h", "7 hari", "30 hari"];
const RANGE_TO_API: Record<UiState["historyRange"], TimeRange> = { "24h": "24h", "7 hari": "7d", "30 hari": "30d" };
const toMs = (iso: string) => parseApiDate(iso).getTime();

function dateLabel(range: TimeRange, asOf: number) {
  const end = new Date(asOf);
  if (range === "24h") return formatFullDate(end);
  const start = new Date(asOf - RANGE_MS[range]);
  return `${formatDayMonth(start)} – ${formatFullDate(end)}`;
}

const csvCell = (value: number | null) => (value === null ? "" : String(value));

function exportCsv(history: PatientHistory, range: TimeRange) {
  const rows = ["waktu_wib,hr_bpm,spo2_persen,rr_napas_per_menit"];
  for (const r of history.readings) {
    const d = parseApiDate(r.timestamp);
    rows.push(`${formatDayMonth(d)} ${formatClock(d)},${csvCell(r.hr)},${csvCell(r.spo2)},${csvCell(r.rr)}`);
  }
  const url = URL.createObjectURL(new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `PNEUMACARE-riwayat-${range}.csv`;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

const fmt = (n: number | null | undefined) => (n === null || n === undefined ? "—" : String(Math.round(n)));

export function HistoryView() {
  const [uiRange, setRange] = useUi("historyRange");
  const range = RANGE_TO_API[uiRange];
  const history = usePatientHistory(range);
  const { toast } = useFeedback();
  const ready = history.status === "ready" ? history : null;

  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5 *:min-w-0">
        <div className={segments}>
          {RANGES.map((t) => (
            <button key={t} type="button" className={segmentButton(uiRange === t)} onClick={() => setRange(t)}>
              {t === "24h" ? "24 jam" : t}
            </button>
          ))}
        </div>
        <button
          type="button"
          className={btn({ small: true })}
          disabled={!ready || ready.data.readings.length === 0}
          onClick={() => {
            if (!ready) return;
            exportCsv(ready.data, range);
            toast("Data pemantauan diekspor sebagai CSV.");
          }}
        >
          <Icon icon={Download} />
          Ekspor data {uiRange === "24h" ? "24 jam" : uiRange} (CSV)
        </button>
      </div>

      {history.status === "loading" && (
        <p role="status" className="py-16 text-center text-muted text-[13px]">
          Memuat riwayat…
        </p>
      )}
      {history.status === "error" && (
        <div role="alert">
          <Notice type="error">{history.message}</Notice>
          <button type="button" className={cn(btn(), "mt-4")} onClick={history.retry}>
            Coba lagi
          </button>
        </div>
      )}

      {ready && <HistoryBody data={ready.data} range={range} asOf={ready.asOf} />}
    </>
  );
}

function HistoryBody({ data, range, asOf }: { data: PatientHistory; range: TimeRange; asOf: number }) {
  const domain: [number, number] = [asOf - RANGE_MS[range], asOf];
  const labels = tickLabels(domain[0], domain[1], range);
  const stats = "hr" in data.stats ? data.stats : null;

  return (
    <div className={cn(chartGrid, "mt-6")}>
      {vitalKeys.map((k) => (
        <div key={k} className={cn(card, cardPad)}>
          <div className="flex items-center justify-between gap-3 mb-5 *:min-w-0">
            <div className="flex items-center gap-3 *:min-w-0">
              <ChartIcon vital={k} />
              <h3>{values[k].label}</h3>
            </div>
            <small>{dateLabel(range, asOf)}</small>
          </div>
          <VitalChart
            vital={k}
            variant="grid"
            points={seriesFor(data.readings, k, range, toMs)}
            domain={domain}
            gapMs={BUCKET_MS[range] * GAP_BUCKETS}
            labels={labels}
          />
          <div className="flex flex-wrap gap-[18px] mt-3 text-[11px] text-muted">
            <LegendItem color={k === "hr" ? "rose" : k === "spo2" ? "blue" : "primary"}>
              {values[k].label} ({values[k].unit})
            </LegendItem>
            <small>Jeda menunjukkan data yang tidak tersedia</small>
          </div>
          {stats && (
            <p className="text-[12px] text-muted mt-3">
              Rata-rata <b>{fmt(stats[k].avg)}</b> · Terendah <b>{fmt(stats[k].min)}</b> · Tertinggi{" "}
              <b>{fmt(stats[k].max)}</b>
            </p>
          )}
        </div>
      ))}
      <div className={cn(card, cardPad)}>
        <h3>Pemakaian rompi per hari</h3>
        <p className="text-muted">Lama rompi terhubung pada tiap hari di rentang ini.</p>
        {data.wear_compliance_by_day.length ? (
          <div className="grid grid-cols-[repeat(7,1fr)] gap-[7px] mt-[22px] max-md:grid-cols-[repeat(4,1fr)]">
            {data.wear_compliance_by_day.map((d) => (
              <div
                key={d.date}
                className="py-3 px-[3px] border rounded-[4px] text-center text-[10px] max-md:py-2.5 max-md:px-1 bg-[#f0f5ed] text-[#36634b] border-[#dfe8dc]"
              >
                <b>{formatDayMonth(parseApiDate(`${d.date}T12:00:00+07:00`))}</b>
                <br />
                <span className="block my-[9px] text-[14px] font-semibold">{d.hours.toFixed(1)} jam</span>
              </div>
            ))}
          </div>
        ) : (
          <Empty icon={WifiOff} title="Belum ada data pemakaian" text="Data muncul setelah rompi terhubung." />
        )}
        {data.pattern_insight && <Notice className="mt-5">{data.pattern_insight}</Notice>}
      </div>
    </div>
  );
}
