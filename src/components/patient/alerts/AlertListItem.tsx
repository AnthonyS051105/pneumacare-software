"use client";

import { useState } from "react";

export type AlertLevel = "info" | "warning" | "urgent";

const LEVEL_STYLE: Record<
  AlertLevel,
  { icon: string; iconBgClass: string; iconColorClass: string; tip: string }
> = {
  info: {
    icon: "check_circle",
    iconBgClass: "bg-status-success/10",
    iconColorClass: "text-status-success",
    tip: "Tidak perlu tindakan khusus. Terus pantau kondisi Anda seperti biasa.",
  },
  warning: {
    icon: "warning",
    iconBgClass: "bg-status-warning/10",
    iconColorClass: "text-status-warning",
    tip: "Istirahat sejenak dan pantau kembali dalam beberapa jam. Bila keluhan berlanjut, hubungi dokter Anda.",
  },
  urgent: {
    icon: "error",
    iconBgClass: "bg-status-error/10",
    iconColorClass: "text-status-error",
    tip: "Segera hubungi tenaga medis Anda atau layanan darurat terdekat.",
  },
};

export type AlertItemData = {
  id: string;
  level: AlertLevel;
  message: string;
  timeLabel: string;
  isRead: boolean;
};

type AlertListItemProps = {
  alert: AlertItemData;
};

export function AlertListItem({ alert }: AlertListItemProps) {
  const [expanded, setExpanded] = useState(false);
  const style = LEVEL_STYLE[alert.level];

  return (
    <div
      className={`rounded-lg border border-outline-variant/30 bg-surface-container-lowest shadow-[0_4px_16px_rgba(0,0,0,0.04)] transition-colors ${
        !alert.isRead ? "border-l-4 border-l-primary" : ""
      }`}
    >
      <button
        type="button"
        onClick={() => setExpanded((prev) => !prev)}
        aria-expanded={expanded}
        className="w-full flex items-start gap-3 p-4 text-left"
      >
        <div
          className={`w-10 h-10 rounded-full flex items-center justify-center shrink-0 ${style.iconBgClass} ${style.iconColorClass}`}
        >
          <span className="material-symbols-outlined">{style.icon}</span>
        </div>
        <div className="min-w-0 flex-1">
          <div className="flex items-center gap-2">
            <p
              className={`text-sm ${
                !alert.isRead
                  ? "font-semibold text-on-surface"
                  : "font-medium text-on-surface-variant"
              }`}
            >
              {alert.message}
            </p>
            {!alert.isRead && (
              <span className="w-2 h-2 rounded-full bg-primary shrink-0" aria-label="Belum dibaca" />
            )}
          </div>
          <p className="text-xs text-on-surface-variant mt-1">{alert.timeLabel}</p>
        </div>
        <span
          className="material-symbols-outlined text-on-surface-variant shrink-0 transition-transform duration-200"
          style={{ transform: expanded ? "rotate(180deg)" : undefined }}
        >
          expand_more
        </span>
      </button>

      {expanded && (
        <div className="px-4 pb-4 pl-[3.75rem]">
          <div className="rounded-md bg-surface-container p-3">
            <p className="text-xs font-semibold text-on-surface-variant mb-1">
              Apa yang bisa Anda lakukan
            </p>
            <p className="text-sm text-on-surface">{style.tip}</p>
          </div>
        </div>
      )}
    </div>
  );
}
