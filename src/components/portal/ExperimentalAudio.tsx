"use client";

import { fetchAudioExperiment } from "@/lib/clinicianApi";
import { formatEventTime } from "@/lib/format";
import { useApi } from "@/lib/useApi";
import { card, cardPad, cn, Notice, Pill } from "@/components/ui/primitives";

/** Show provenance and the explicit prototype notification mode. */
export function ExperimentalAudio({ patientId }: { patientId: string }) {
  const state = useApi(() => fetchAudioExperiment(patientId), `audio-experiment:${patientId}`, { pollMs: 5000 });
  if (state.status === "loading") return null;
  if (state.status === "error") return <Notice>Hasil uji audio belum dapat dimuat.</Notice>;
  const data = state.data;
  if (!data.available) return null;
  const reviews = data.channels.filter((c) => c.data_origin === "measured" && c.review_signal);
  return (
    <section className={cn(card, cardPad)} aria-label="Hasil uji audio berkala">
      <h3>Uji audio berkala · 2 detik</h3>
      <p className="text-muted text-[13px]">
        {data.start_ms != null ? formatEventTime(new Date(data.start_ms).toISOString()) : "Waktu belum tersedia"}
        {" · "}Rekaman #{data.capture_id}
      </p>
      <div className="mt-4">
        <Notice>
          Prediksi eksperimental, belum tervalidasi klinis. Kanal salinan menguji pengiriman data;
          posisi mikrofon tersebut belum terukur. Hasil ini terpisah dari tren klinis.
          {data.patient_notifications_enabled
            ? " Notifikasi otomatis aktif: hasil abnormal berulang pada mikrofon yang sama dapat naik dari Info ke Warning dan Urgent."
            : " Notifikasi pasien dari rekaman ini nonaktif."}
        </Notice>
      </div>
      <div className="grid grid-cols-4 gap-3 mt-4 max-md:grid-cols-2">
        {data.channels.map((channel) => {
          const prediction = channel.experimental_classification;
          const notification = channel.patient_notification;
          return (
            <div key={channel.channel_id} className="border border-line rounded-xl p-3 text-[13px]">
              <strong>Kanal {channel.channel_id}</strong>
              <p className="text-muted">
                {channel.data_origin === "simulated" ? `Simulasi · salinan kanal ${channel.source_channel_id}` : "Pengukuran mikrofon"}
              </p>
              <p className="mt-2">
                {channel.data_origin === "simulated" ? "Dikecualikan dari klasifikasi" : prediction
                  ? `Prediksi ${prediction.predicted_class === "abnormal" ? "abnormal" : "normal"} · ${Math.round(prediction.confidence * 100)}%`
                  : channel.inference_status === "failed" ? "Inferensi gagal" : "Belum ada prediksi"}
              </p>
              {channel.patient_notification?.status === "created" && (
                <p className="mt-2 text-muted">Notifikasi pasien dibuat.</p>
              )}
              {channel.patient_notification?.status === "suppressed" && (
                <p className="mt-2 text-muted">Notifikasi serupa sudah tercatat.</p>
              )}
              {notification?.level != null && (
                <div className="mt-2">
                  <Pill tone={notification.level === 3 ? "urgent" : notification.level === 2 ? "warn" : ""}>
                    {notification.level === 3 ? "Urgent" : notification.level === 2 ? "Warning" : "Info"}
                  </Pill>
                </div>
              )}
              {notification?.consecutive_abnormal != null && (
                <p className="mt-2 text-muted">
                  {notification.consecutive_abnormal} hasil abnormal terbaru berturut-turut.
                </p>
              )}
            </div>
          );
        })}
      </div>
      {reviews.length > 0 && (
        <p role="status" className="mt-4 text-[13px] font-semibold">
          Perlu peninjauan rekaman: prediksi abnormal pada kanal {reviews.map((c) => c.channel_id).join(", ")}.
          {data.patient_notifications_enabled
            ? "Hasil mengikuti kebijakan notifikasi dan deduplikasi; ini belum merupakan diagnosis."
            : "Ini sinyal tinjau eksperimen; notifikasi pasien nonaktif."}
        </p>
      )}
    </section>
  );
}
