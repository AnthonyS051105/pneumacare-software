import type { Metadata } from "next";
import Link from "next/link";
import { ModalButton } from "@/components/providers/Feedback";
import { RetryState } from "@/components/lab/LabActions";
import { grid2, grid3, LabHeader, LabMain } from "@/components/lab/LabHeader";
import { Connection } from "@/components/portal/Connection";
import { stack } from "@/components/portal/layout";
import { Metric, metricsGrid } from "@/components/portal/Metric";
import { Bell, Search, Users } from "@/components/ui/Icon";
import { btn, card, cardPad, cn, Empty, Notice } from "@/components/ui/primitives";
import { VitalChart } from "@/components/ui/VitalChart";
import { vitalKeys } from "@/lib/demo-data";

export const metadata: Metadata = { title: "Kondisi Data & Koneksi" };

const cardCls = cn(card, cardPad);
const skeleton = "bg-[#e8eee6] rounded-[4px] animate-shimmer";

export default function StatesPage() {
  return (
    <LabMain>
      <LabHeader
        title="Kondisi Data & Koneksi"
        description="Lembar pelengkap 2, Data kosong, offline, gagal memuat, dan loading."
      />
      <div className={stack}>
        <section>
          <h3>01: Belum Ada Data Vital</h3>
          <p className="text-muted mb-5">Kondisi belum diketahui hingga data tersedia.</p>
          <div className={metricsGrid}>
            {vitalKeys.map((k) => (
              <Metric key={k} vital={k} unknown lab />
            ))}
          </div>
        </section>
        <section className={cardCls}>
          <h3 className="mb-5">02: Perangkat Offline</h3>
          <Connection offline />
          <div className="mt-6">
            <Notice type="warn">
              Kondisi terkini belum diketahui. Pembacaan terakhir: HR 78 bpm, SpO₂ 96%, RR 18 napas/menit pada 09.10
              WIB. Data tersebut bukan kondisi saat ini.
            </Notice>
          </div>
          <VitalChart vital="spo2" offline />
          <small className="font-mono text-[10px] pt-3.5">Garis berhenti ketika data tidak tersedia; tidak diinterpolasi.</small>
        </section>
        <div className={grid2}>
          <section className={cardCls}>
            <h3>03: Daftar Pasien Kosong</h3>
            <Empty
              icon={Users}
              title="Belum ada pasien"
              text="Tambahkan pasien untuk mulai pemantauan."
              action={
                <ModalButton kind="add" className={btn({ variant: "primary" })}>
                  Tambah Pasien
                </ModalButton>
              }
            />
          </section>
          <section className={cardCls}>
            <h3>04: Notifikasi Kosong</h3>
            <Empty icon={Bell} title="Belum ada notifikasi" text="Pemberitahuan akan ditampilkan saat tersedia." />
          </section>
          <section className={cardCls}>
            <h3>05: Pencarian Tanpa Hasil</h3>
            <Empty
              icon={Search}
              title="Pasien tidak ditemukan"
              text="Periksa kata kunci atau ubah filter."
              action={
                <Link href="/clinician/patients" className={btn()}>
                  Kembali ke daftar pasien
                </Link>
              }
            />
          </section>
          <RetryState className={cardCls} />
        </div>
        <section className={cardCls}>
          <h3 className="mb-5">07: Memuat Data</h3>
          <div className={grid3}>
            {[1, 2, 3].map((n) => (
              <div key={n} className={stack}>
                <div className={cn(skeleton, "h-5 w-[45%]")} />
                <div className={cn(skeleton, "h-[110px]")} />
                <div className={cn(skeleton, "h-5")} />
              </div>
            ))}
          </div>
          <p className="text-muted mt-6">Memuat pembacaan… Nilai nol tidak digunakan sebagai pengganti data.</p>
        </section>
      </div>
    </LabMain>
  );
}
