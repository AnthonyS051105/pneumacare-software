type AlertsEmptyStateProps = {
  message: string;
};

export function AlertsEmptyState({ message }: AlertsEmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-outline-variant/50 bg-surface-container-lowest py-16 px-4 text-center">
      <div className="w-16 h-16 rounded-full bg-secondary-container flex items-center justify-center text-on-secondary-container">
        <span className="material-symbols-outlined" style={{ fontSize: "32px" }}>
          notifications_off
        </span>
      </div>
      <p className="text-base font-semibold text-on-surface">{message}</p>
      <p className="text-sm text-on-surface-variant max-w-xs">
        Notifikasi akan muncul di sini bila ada hal yang perlu Anda ketahui.
      </p>
    </div>
  );
}
