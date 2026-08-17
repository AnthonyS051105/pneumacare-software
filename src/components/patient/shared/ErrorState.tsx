// Error state generik — dipakai saat fetch ke backend gagal (network error,
// belum login/sesi kedaluwarsa, 404, dsb). UIUX_FLOW.md §7: pesan harus jelas,
// bukan halaman kosong. Tombol "Coba Lagi" opsional via onRetry.

type ErrorStateProps = {
  message: string;
  onRetry?: () => void;
};

export function ErrorState({ message, onRetry }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-status-error/30 bg-status-error/5 p-10 text-center">
      <span className="material-symbols-outlined text-3xl text-status-error">
        error
      </span>
      <p className="text-sm text-on-surface">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="rounded-full bg-status-error/10 px-4 py-2 text-sm font-semibold text-status-error hover:bg-status-error/20 transition-colors"
        >
          Coba Lagi
        </button>
      )}
    </div>
  );
}
