"use client";

import { useFeedback } from "@/components/providers/Feedback";
import { chartGrid } from "@/components/portal/layout";
import { ChartIcon } from "@/components/portal/VitalIcon";
import { CircleCheck, Download, Icon, TriangleAlert } from "@/components/ui/Icon";
import { btn, card, cardPad, cn, LegendItem, segmentButton, segments } from "@/components/ui/primitives";
import { VitalChart } from "@/components/ui/VitalChart";
import { values, vitalKeys } from "@/lib/demo-data";
import { useUi, type UiState } from "@/lib/demo-store";

const RANGES: UiState["historyRange"][] = ["24h", "7 hari", "30 hari"];
const DATE_LABEL = {
  "24h": "10 Oktober 2026",
  "7 hari": "4–10 Oktober 2026",
  "30 hari": "11 September–10 Oktober 2026",
};
const DAYS = ["Min, 4", "Sen, 5", "Sel, 6", "Rab, 7", "Kam, 8", "Jum, 9", "Sab, 10"];

function exportCsv() {
  const rows = ["waktu,hr_bpm,spo2_persen,rr_napas_per_menit,sumber"];
  values.hr.series.forEach((hr, j) =>
    rows.push(
      `${String(j * 2).padStart(2, "0")}:00,${j === 6 ? "" : hr},${j === 6 ? "" : values.spo2.series[j]},${j === 6 ? "" : values.rr.series[j]},simulasi`,
    ),
  );
  const url = URL.createObjectURL(new Blob([rows.join("\n")], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = "PNEUMACARE-data-simulasi.csv";
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export function HistoryView() {
  const [range, setRange] = useUi("historyRange");
  const { toast } = useFeedback();
  return (
    <>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5 *:min-w-0">
        <div className={segments}>
          {RANGES.map((t) => (
            <button key={t} type="button" className={segmentButton(range === t)} onClick={() => setRange(t)}>
              {t === "24h" ? "24 jam" : t}
            </button>
          ))}
        </div>
        <button
          type="button"
          className={btn({ small: true })}
          onClick={() => {
            exportCsv();
            toast("Data pemantauan diekspor sebagai CSV.");
          }}
        >
          <Icon icon={Download} />
          Ekspor data 24 jam (CSV)
        </button>
      </div>
      <div className={cn(chartGrid, "mt-6")}>
        {vitalKeys.map((k) => (
          <div key={k} className={cn(card, cardPad)}>
            <div className="flex items-center justify-between gap-3 mb-5 *:min-w-0">
              <div className="flex items-center gap-3 *:min-w-0">
                <ChartIcon vital={k} />
                <h3>{values[k].label}</h3>
              </div>
              <small>{DATE_LABEL[range]}</small>
            </div>
            <VitalChart vital={k} gap range={range} variant="grid" />
            <div className="flex flex-wrap gap-[18px] mt-3 text-[11px] text-muted">
              <LegendItem color={k === "hr" ? "rose" : k === "spo2" ? "blue" : "primary"}>
                {values[k].label} ({values[k].unit})
              </LegendItem>
              <small>Jeda menunjukkan data yang tidak tersedia</small>
            </div>
          </div>
        ))}
        <div className={cn(card, cardPad)}>
          <h3>Ringkasan kondisi 7 hari</h3>
          <p className="text-muted">Ringkasan contoh dari data pemantauan yang tersedia.</p>
          <div className="grid grid-cols-[repeat(7,1fr)] gap-[7px] mt-[22px] max-md:grid-cols-[repeat(4,1fr)]">
            {DAYS.map((t, j) => (
              <div
                key={t}
                className={cn(
                  "py-3 px-[3px] border rounded-[4px] text-center text-[10px] max-md:py-2.5 max-md:px-1",
                  j === 2 ? "bg-[#faf2e0] text-amber border-[#ece0c5]" : "bg-[#f0f5ed] text-[#36634b] border-[#dfe8dc]",
                )}
              >
                <b>{t}</b>
                <br />
                <Icon icon={j === 2 ? TriangleAlert : CircleCheck} className="size-[17px] my-[9px]" />
                <br />
                {j === 2 ? "Perlu perhatian" : "Stabil"}
              </div>
            ))}
          </div>
        </div>
      </div>
    </>
  );
}
