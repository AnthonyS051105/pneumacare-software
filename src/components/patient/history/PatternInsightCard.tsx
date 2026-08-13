type PatternInsightCardProps = {
  periodLabel: string;
  insightText: string;
};

export function PatternInsightCard({
  periodLabel,
  insightText,
}: PatternInsightCardProps) {
  return (
    <div className="rounded-3xl bg-secondary-fixed/50 p-5 md:p-6 border border-secondary-fixed-dim/30">
      <h3 className="text-lg font-bold text-on-secondary-fixed mb-2 flex items-center gap-2">
        <span className="material-symbols-outlined">insights</span>
        Catatan Pola
      </h3>
      <p className="text-sm text-on-surface-variant mb-4">
        Berdasarkan data {periodLabel} terakhir, kami melihat tren berikut:
      </p>
      <div className="bg-surface-container-lowest/80 rounded-xl p-4 flex items-start gap-3 shadow-sm">
        <span className="material-symbols-outlined text-primary mt-0.5">
          check_circle
        </span>
        <p className="text-sm text-on-surface">{insightText}</p>
      </div>
    </div>
  );
}
