type DayCompliance = {
  day: string;
  hours: number;
  isBest?: boolean;
  isHighlighted?: boolean;
};

type WearComplianceChartCardProps = {
  targetHours: number;
  days: DayCompliance[];
};

export function WearComplianceChartCard({
  targetHours,
  days,
}: WearComplianceChartCardProps) {
  const maxHours = Math.max(targetHours, ...days.map((d) => d.hours));

  return (
    <div className="rounded-3xl bg-surface-container-lowest p-5 md:p-6 shadow-[0_8px_32px_rgba(0,0,0,0.04)] border border-outline-variant/20">
      <h3 className="text-lg font-bold text-on-surface mb-1">
        Kepatuhan Pemakaian
      </h3>
      <p className="text-xs text-on-surface-variant mb-4">
        Target: {targetHours} Jam / Hari
      </p>
      <div className="flex items-end gap-2 h-32 mt-4">
        {days.map((d) => {
          const heightPercent = Math.min(
            100,
            Math.round((d.hours / maxHours) * 100)
          );
          return (
            <div
              key={d.day}
              className="flex-1 flex flex-col items-center gap-1 h-full"
            >
              <div className="w-full flex-1 flex items-end">
                <div
                  className={`w-full rounded-t-sm relative ${
                    d.isBest ? "bg-primary-container" : "bg-primary/20"
                  }`}
                  style={{ height: `${heightPercent}%` }}
                >
                  {d.isHighlighted && (
                    <div className="absolute -top-6 left-1/2 -translate-x-1/2 bg-surface-container-high text-on-surface px-2 py-0.5 rounded text-xs font-bold tabular-nums shadow-sm whitespace-nowrap">
                      {d.hours}j
                    </div>
                  )}
                </div>
              </div>
              <span
                className={`text-xs ${
                  d.isHighlighted
                    ? "font-bold text-on-surface"
                    : "text-on-surface-variant/70"
                }`}
              >
                {d.day}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
