"use client";

import Link from "next/link";
import { ArrowRight, Icon } from "@/components/ui/Icon";
import { Avatar, btn, card, cardPad, cn, segmentButton, segments } from "@/components/ui/primitives";
import { VitalChart } from "@/components/ui/VitalChart";
import { values, vitalKeys } from "@/lib/demo-data";
import { useDemo, useUi } from "@/lib/demo-store";

const TAB_LABEL = { hr: "HR", spo2: "SpO₂", rr: "RR" } as const;

/** Kartu "Perubahan kondisi Anda" dengan pilihan HR/SpO₂/RR. */
export function VitalSwitcherCard() {
  const [metricTab, setMetricTab] = useUi("metricTab");
  const v = values[metricTab];
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
      <VitalChart vital={metricTab} />
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
export function CareTeamPanel() {
  const name = useDemo((d) => d.clinician.name);
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
            Dokter Spesialis Paru
            <br />
            RS Akademik UGM
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
