type VitalSummaryCardProps = {
  label: string;
  icon: string;
  iconBgClass: string;
  iconColorClass: string;
  value: number;
  unit: string;
  rangeLabel: string;
};

export function VitalSummaryCard({
  label,
  icon,
  iconBgClass,
  iconColorClass,
  value,
  unit,
  rangeLabel,
}: VitalSummaryCardProps) {
  return (
    <div className="flex flex-col justify-between rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-5 shadow-[0_4px_16px_rgba(0,0,0,0.04)] transition-shadow hover:shadow-[0_8px_24px_rgba(0,0,0,0.08)]">
      <div className="flex items-center gap-2 mb-4">
        <div
          className={`w-8 h-8 rounded-full flex items-center justify-center ${iconBgClass} ${iconColorClass}`}
        >
          <span className="material-symbols-outlined text-sm">{icon}</span>
        </div>
        <span className="text-base font-semibold">{label}</span>
      </div>
      <div>
        <div className="flex items-baseline gap-1">
          <span className="text-5xl font-bold tabular-nums leading-tight">
            {value}
          </span>
          <span className="text-base text-on-surface-variant">{unit}</span>
        </div>
        <p className="text-sm text-on-surface-variant mt-1">{rangeLabel}</p>
      </div>
    </div>
  );
}
