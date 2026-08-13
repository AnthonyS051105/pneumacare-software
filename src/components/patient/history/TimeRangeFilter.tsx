"use client";

const RANGE_OPTIONS = [
  { value: "24h", label: "24 Jam" },
  { value: "7d", label: "7 Hari" },
  { value: "30d", label: "30 Hari" },
] as const;

export type TimeRange = (typeof RANGE_OPTIONS)[number]["value"];

type TimeRangeFilterProps = {
  value: TimeRange;
  onChange: (value: TimeRange) => void;
};

export function TimeRangeFilter({ value, onChange }: TimeRangeFilterProps) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 -mx-4 px-4 md:mx-0 md:px-0 scrollbar-hide">
      {RANGE_OPTIONS.map((option) => {
        const isActive = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={
              isActive
                ? "shrink-0 px-4 py-2 rounded-full bg-primary-container text-on-primary-container text-sm font-semibold transition-colors"
                : "shrink-0 px-4 py-2 rounded-full bg-surface-container text-on-surface-variant text-sm font-semibold border border-outline-variant/30 hover:bg-surface-container-high transition-colors"
            }
          >
            {option.label}
          </button>
        );
      })}
    </div>
  );
}
