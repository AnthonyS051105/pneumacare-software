"use client";

import { useState } from "react";
import { Icon, RotateCw } from "@/components/ui/Icon";
import { btn, cn, Notice } from "@/components/ui/primitives";

/** Kartu "Gagal Memuat Data" dengan simulasi muat ulang. */
export function RetryState({ className }: { className: string }) {
  const [state, setState] = useState<"error" | "loading" | "done">("error");
  return (
    <section className={className} id="retry-state">
      {state === "error" && (
        <>
          <h3>06: Gagal Memuat Data</h3>
          <div className="mt-6">
            <Notice type="error">
              Koneksi ke layanan data gagal. Data contoh tersimpan dapat dilihat dengan waktu pembaruan yang jelas.
            </Notice>
          </div>
          <p className="text-muted mt-6">Data cache simulasi: 09.10 WIB, Bukan data terkini</p>
          <button
            type="button"
            className={cn(btn(), "mt-6")}
            onClick={() => {
              setState("loading");
              setTimeout(() => setState("done"), 900);
            }}
          >
            <Icon icon={RotateCw} />
            Coba lagi
          </button>
        </>
      )}
      {state === "loading" && (
        <>
          <h3>Memuat ulang data…</h3>
          <div className="bg-[#e8eee6] rounded-[4px] h-[110px] animate-shimmer mt-6" />
        </>
      )}
      {state === "done" && (
        <>
          <h3>Data contoh tersedia</h3>
          <Notice>Data cache simulasi berhasil dimuat. Pembaruan terakhir 09.10 WIB; bukan kondisi terkini.</Notice>
          <p className="text-muted mt-6">HR 78 bpm, SpO₂ 96%, RR 18 napas/menit</p>
        </>
      )}
    </section>
  );
}
