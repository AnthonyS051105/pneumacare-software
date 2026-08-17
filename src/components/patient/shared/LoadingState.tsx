// Skeleton loading generik — dipakai di Patient Home/History/Alerts saat fetch
// awal masih berjalan. Mengikuti UIUX_FLOW.md §7 soal loading/error state harus
// jelas, bukan halaman kosong tanpa penjelasan.

export function LoadingState({ label = "Memuat data..." }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-10 text-center">
      <span className="material-symbols-outlined animate-spin text-3xl text-primary">
        progress_activity
      </span>
      <p className="text-sm text-on-surface-variant">{label}</p>
    </div>
  );
}
