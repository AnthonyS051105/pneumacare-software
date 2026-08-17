type PredictedClass = "none" | "crackle" | "wheeze" | "both";

const CLASS_LABEL: Record<PredictedClass, string> = {
  none: "Tidak terdeteksi",
  crackle: "Crackle terdeteksi",
  wheeze: "Wheeze terdeteksi",
  both: "Wheeze & crackle terdeteksi",
};

const CLASS_ICON_CLASS: Record<PredictedClass, string> = {
  none: "text-status-success bg-status-success/10",
  crackle: "text-status-warning bg-status-warning/10",
  wheeze: "text-status-warning bg-status-warning/10",
  both: "text-status-error bg-status-error/10",
};

type ClassificationResultCardProps = {
  predictedClass: PredictedClass;
  confidence: number;
  timestampLabel: string;
};

export function ClassificationResultCard({
  predictedClass,
  confidence,
  timestampLabel,
}: ClassificationResultCardProps) {
  return (
    <section className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-5 shadow-[0_4px_16px_rgba(0,0,0,0.04)]">
      <div className="mb-3 flex items-center gap-3">
        <div
          className={`flex h-8 w-8 items-center justify-center rounded-full ${CLASS_ICON_CLASS[predictedClass]}`}
        >
          <span className="material-symbols-outlined text-sm">graphic_eq</span>
        </div>
        <h3 className="text-base font-semibold">Hasil Analisis Suara Napas Terbaru</h3>
      </div>
      <p className="mb-1 text-lg font-bold text-on-surface">{CLASS_LABEL[predictedClass]}</p>
      <p className="text-sm text-on-surface-variant">
        Keyakinan model {Math.round(confidence * 100)}% &middot; {timestampLabel}
      </p>
      <p className="mt-3 text-xs text-on-surface-variant">
        Hasil skrining otomatis, BUKAN diagnosis medis. Selalu konsultasikan dengan tenaga
        kesehatan.
      </p>
    </section>
  );
}
