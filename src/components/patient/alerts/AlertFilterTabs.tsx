"use client";

const FILTER_OPTIONS = [
  { value: "all", label: "Semua" },
  { value: "unread", label: "Belum Dibaca" },
] as const;

export type AlertFilter = (typeof FILTER_OPTIONS)[number]["value"];

type AlertFilterTabsProps = {
  value: AlertFilter;
  onChange: (value: AlertFilter) => void;
  unreadCount: number;
};

export function AlertFilterTabs({
  value,
  onChange,
  unreadCount,
}: AlertFilterTabsProps) {
  return (
    <div className="flex gap-2 overflow-x-auto pb-1 -mx-4 px-4 md:mx-0 md:px-0 scrollbar-hide">
      {FILTER_OPTIONS.map((option) => {
        const isActive = option.value === value;
        return (
          <button
            key={option.value}
            type="button"
            onClick={() => onChange(option.value)}
            className={
              isActive
                ? "shrink-0 px-4 py-2 rounded-full bg-primary-container text-on-primary-container text-sm font-semibold transition-colors flex items-center gap-2"
                : "shrink-0 px-4 py-2 rounded-full bg-surface-container text-on-surface-variant text-sm font-semibold border border-outline-variant/30 hover:bg-surface-container-high transition-colors flex items-center gap-2"
            }
          >
            {option.label}
            {option.value === "unread" && unreadCount > 0 && (
              <span
                className={
                  isActive
                    ? "inline-flex items-center justify-center min-w-5 h-5 px-1 rounded-full bg-on-primary-container/20 text-xs font-bold"
                    : "inline-flex items-center justify-center min-w-5 h-5 px-1 rounded-full bg-status-error text-white text-xs font-bold"
                }
              >
                {unreadCount}
              </span>
            )}
          </button>
        );
      })}
    </div>
  );
}
