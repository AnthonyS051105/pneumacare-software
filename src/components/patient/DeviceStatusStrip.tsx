type DeviceStatusStripProps = {
  connected: boolean;
  signalLabel: string;
  batteryPercent: number | null;
};

export function DeviceStatusStrip({
  connected,
  signalLabel,
  batteryPercent,
}: DeviceStatusStripProps) {
  return (
    <section className="flex items-center justify-between rounded-lg border border-outline-variant/30 bg-surface-container-lowest p-4 shadow-[0_4px_16px_rgba(0,0,0,0.04)]">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-10 h-10 rounded-full bg-tertiary-container/30 flex items-center justify-center text-tertiary shrink-0">
          <span className="material-symbols-outlined">sensors</span>
        </div>
        <div className="min-w-0">
          <h3 className="text-base font-semibold truncate">
            {connected ? "Vest Terhubung" : "Vest Terputus"}
          </h3>
          <p className="text-sm text-on-surface-variant flex items-center gap-1">
            <span
              className={`w-1.5 h-1.5 rounded-full inline-block ${
                connected ? "bg-status-success" : "bg-status-error"
              }`}
            />
            {signalLabel}
          </p>
        </div>
      </div>
      {/* TODO_NATHANAEL_CONFIRM: battery_percent bergantung verifikasi firmware ESP32 (lihat UIUX_FLOW.md §7 poin 7) */}
      {batteryPercent !== null && (
        <div className="flex items-center gap-2 text-on-surface shrink-0">
          <span className="text-base font-semibold tabular-nums">
            {batteryPercent}%
          </span>
          <span className="material-symbols-outlined text-status-success">
            battery_5_bar
          </span>
        </div>
      )}
    </section>
  );
}
