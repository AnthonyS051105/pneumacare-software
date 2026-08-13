export function QuickLinks() {
  return (
    <section className="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <a
        href="/patient/history"
        className="flex items-center justify-center gap-2 rounded-lg bg-primary py-3 px-4 text-on-primary text-base font-semibold shadow-sm transition-colors hover:bg-primary-shade"
      >
        <span className="material-symbols-outlined text-sm">bar_chart</span>
        Lihat Riwayat Lengkap
      </a>
      <a
        href="/patient/alerts"
        className="flex items-center justify-center gap-2 rounded-lg border border-outline-variant/50 bg-surface-container py-3 px-4 text-primary text-base font-semibold shadow-sm transition-colors hover:bg-surface-variant"
      >
        <span className="material-symbols-outlined text-sm">notifications</span>
        Pusat Notifikasi
      </a>
    </section>
  );
}
