"use client";

import Link from "next/link";
import { ArrowRight, Icon } from "@/components/ui/Icon";
import { Avatar, btn, card, cardPad, cn, segmentButton, segments } from "@/components/ui/primitives";
import { VitalChart } from "@/components/ui/VitalChart";
import { values, vitalKeys } from "@/lib/demo-data";
import { useUi } from "@/lib/demo-store";
import type { HistoryState } from "@/lib/usePatientHistory";
import type { PatientProfile } from "@/lib/patientApi";
import { BUCKET_MS, GAP_BUCKETS, RANGE_MS, seriesFor, tickLabels } from "@/lib/vitals";
import { parseApiDate } from "@/lib/format";

const TAB_LABEL = { hr: "HR", spo2: "SpO₂", rr: "RR" } as const;

/** Kartu "Perubahan kondisi Anda" dengan pilihan HR/SpO₂/RR. */
export function VitalSwitcherCard({ history }: { history: HistoryState }) {
  const [metricTab, setMetricTab] = useUi("metricTab");
  const v = values[metricTab];
  const ready = history.status === "ready" ? history : null;
  const domain: [number, number] | undefined = ready ? [ready.asOf - RANGE_MS["24h"], ready.asOf] : undefined;
  return (
    <section className={cn(card, cardPad)}>
      <div className="flex flex-wrap items-center justify-between gap-3 mb-5 *:min-w-0">
        <div>
          <h3>Perubahan kondisi Anda</h3>
          <small>24 jam terakhir</small>
        </div>
        <div className={segments} aria-label="Pilih tanda vital">
          {vitalKeys.map((k) => (
            <button
              key={k}
              type="button"
              aria-pressed={metricTab === k}
              className={segmentButton(metricTab === k)}
              onClick={() => setMetricTab(k)}
            >
              {TAB_LABEL[k]}
            </button>
          ))}
        </div>
      </div>
      {history.status === "error" ? (
        <div role="alert" className="py-10 text-center text-muted text-[13px]">
          {history.message}{" "}
          <button type="button" className="underline text-navy" onClick={history.retry}>
            Coba lagi
          </button>
        </div>
      ) : ready && domain ? (
        <VitalChart
          vital={metricTab}
          points={seriesFor(ready.data.readings, metricTab, "24h", (iso) => parseApiDate(iso).getTime())}
          domain={domain}
          gapMs={BUCKET_MS["24h"] * GAP_BUCKETS}
          labels={tickLabels(domain[0], domain[1], "24h")}
        />
      ) : (
        <p role="status" className="py-10 text-center text-muted text-[13px]">
          Memuat grafik…
        </p>
      )}
      <div className="flex flex-wrap items-center justify-between gap-3 mt-6 *:min-w-0">
        <small>
          {v.label} ({v.unit})
        </small>
        <Link href="/patient/history" className={btn({ variant: "ghost", small: true })}>
          Lihat riwayat lengkap <Icon icon={ArrowRight} />
        </Link>
      </div>
    </section>
  );
}

/** Panel tenaga medis pendamping (nama mengikuti profil klinisi tersimpan). */
export function CareTeamPanel({ clinician }: { clinician: PatientProfile["clinician"] }) {
  if (!clinician) {
    return (
      <section className={cn(card, cardPad, "self-start flex flex-col gap-[18px]")} aria-labelledby="care-team-title">
        <h3 id="care-team-title" className="leading-[1.4]">
          Tenaga medis pendamping
        </h3>
        <p className="text-[13px] text-muted leading-[1.7]">
          Anda belum memiliki tenaga medis pendamping. Penugasan dikelola oleh pengelola layanan.
        </p>
      </section>
    );
  }
  const name = clinician.full_name;
  return (
    <section className={cn(card, cardPad, "self-start flex flex-col gap-[18px]")} aria-labelledby="care-team-title">
      <h3 id="care-team-title" className="leading-[1.4]">
        Tenaga medis pendamping
      </h3>
      <div className="flex items-center gap-[13px] *:min-w-0">
        <Avatar name={name} size="team" clinical />
        <div>
          <h4 className="text-[16px] leading-[1.4]">{name}</h4>
          <small className="block text-[11px] leading-[1.7] mt-1">
            {clinician.specialization ?? "Tenaga medis"}
            {clinician.institution && (
              <>
                <br />
                {clinician.institution}
              </>
            )}
          </small>
        </div>
      </div>
      <p className="text-[13px] text-muted leading-[1.7]">
        Pendamping Anda meninjau perubahan kondisi. Tetap ikuti rencana pemantauan yang telah disepakati.
      </p>
      <Link
        href="/patient/profile"
        className="inline-flex items-center justify-between gap-[9px] min-h-11 pt-3.5 border-t border-line text-left whitespace-normal font-semibold text-[12px] leading-[1.4] text-navy hover:text-primary hover:underline hover:underline-offset-4"
      >
        Lihat informasi pendamping <Icon icon={ArrowRight} />
      </Link>
    </section>
  );
}
