type MonthlySummaryStripProps = {
  totalThisMonth: number;
  trendLabel: string;
};

export function MonthlySummaryStrip({
  totalThisMonth,
  trendLabel,
}: MonthlySummaryStripProps) {
  return (
    <section className="flex items-center gap-4 rounded-lg border border-outline-variant/30 bg-surface-container-lowest p-4 shadow-[0_4px_16px_rgba(0,0,0,0.04)]">
      <div className="w-12 h-12 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container shrink-0">
        <span className="material-symbols-outlined">calendar_month</span>
      </div>
      <div className="min-w-0">
        <p className="text-base font-semibold text-on-surface">
          {totalThisMonth} notifikasi bulan ini
        </p>
        <p className="text-sm text-on-surface-variant truncate">
          {trendLabel}
        </p>
      </div>
    </section>
  );
}
