type StatItem = {
  label: string;
  value: string;
  emphasize?: boolean;
};

type VitalTrendCardProps = {
  title: string;
  unitLabel: string;
  icon: string;
  iconColorClass: string;
  stats: StatItem[];
  chartPath: string;
  chartColor: string;
  chartViewBox?: string;
  yAxisLabels?: string[];
  xAxisLabels?: string[];
  alertMarker?: { cx: number; cy: number };
  chartHeightClass?: string;
};

export function VitalTrendCard({
  title,
  unitLabel,
  icon,
  iconColorClass,
  stats,
  chartPath,
  chartColor,
  chartViewBox = "0 0 100 50",
  yAxisLabels,
  xAxisLabels,
  alertMarker,
  chartHeightClass = "h-48",
}: VitalTrendCardProps) {
  const hasAxisLabels = Boolean(yAxisLabels?.length);

  return (
    <div className="rounded-3xl bg-surface-container-lowest p-5 md:p-6 shadow-[0_8px_32px_rgba(0,0,0,0.04)] border border-outline-variant/20">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg md:text-xl font-bold text-on-surface flex items-center gap-2">
            <span
              className={`material-symbols-outlined ${iconColorClass}`}
              style={{ fontVariationSettings: "'FILL' 1" }}
            >
              {icon}
            </span>
            {title}
          </h3>
          <p className="text-sm text-on-surface-variant">{unitLabel}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-3 mb-5">
        {stats.map((stat) => (
          <div
            key={stat.label}
            className="bg-surface-container-low px-4 py-2 rounded-lg flex-1 min-w-[76px]"
          >
            <p className="text-xs text-on-surface-variant">{stat.label}</p>
            <p
              className={`tabular-nums text-on-surface ${
                stat.emphasize ? "text-2xl font-bold" : "text-lg font-bold"
              }`}
            >
              {stat.value}
            </p>
          </div>
        ))}
      </div>

      <div
        className={`${chartHeightClass} w-full relative ${
          hasAxisLabels ? "border-b border-outline-variant/30 pt-4" : ""
        } flex items-end`}
      >
        {hasAxisLabels && yAxisLabels && (
          <div className="absolute left-0 top-0 h-full flex flex-col justify-between text-xs text-on-surface-variant/50 tabular-nums pb-6">
            {yAxisLabels.map((label) => (
              <span key={label}>{label}</span>
            ))}
          </div>
        )}

        <div className="absolute left-8 right-0 bottom-6 h-[40%] bg-primary-container/10 rounded-sm -z-10 border-t border-b border-primary-container/20" />

        <div
          className={hasAxisLabels ? "w-full h-full ml-8 relative" : "w-full h-full relative"}
        >
          <svg
            className="w-full h-full overflow-visible"
            viewBox={chartViewBox}
            preserveAspectRatio="none"
          >
            <path
              d={chartPath}
              fill="none"
              stroke={chartColor}
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth="2"
            />
            {alertMarker && (
              <>
                <circle
                  className="animate-pulse"
                  cx={alertMarker.cx}
                  cy={alertMarker.cy}
                  r="3"
                  fill="var(--color-status-warning)"
                />
                <circle cx={alertMarker.cx} cy={alertMarker.cy} r="1.5" fill="#ffffff" />
              </>
            )}
          </svg>
        </div>

        {xAxisLabels && (
          <div className="absolute bottom-0 left-8 right-0 flex justify-between text-xs text-on-surface-variant/50 pt-2 border-t border-outline-variant/20">
            {xAxisLabels.map((label) => (
              <span key={label}>{label}</span>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
