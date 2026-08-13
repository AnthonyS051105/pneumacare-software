export type StatusLevel = "stable" | "attention" | "urgent";

const STATUS_COPY: Record<
  StatusLevel,
  { title: string; description: string; badgeColor: string }
> = {
  stable: {
    title: "Kondisi Anda Stabil",
    description:
      "Semua parameter kesehatan Anda terpantau normal pagi ini. Teruskan kebiasaan baik Anda!",
    badgeColor: "bg-status-success",
  },
  attention: {
    title: "Perlu Diperhatikan",
    description:
      "Ada beberapa parameter yang berada di luar rentang biasa Anda. Pantau terus kondisi Anda.",
    badgeColor: "bg-status-warning",
  },
  urgent: {
    title: "Segera Hubungi Dokter",
    description:
      "Kondisi Anda memerlukan perhatian medis. Tenaga medis Anda telah diberi tahu.",
    badgeColor: "bg-status-error",
  },
};

type StatusHeroCardProps = {
  level: StatusLevel;
  lastUpdatedLabel: string;
};

export function StatusHeroCard({ level, lastUpdatedLabel }: StatusHeroCardProps) {
  const copy = STATUS_COPY[level];

  return (
    <section className="relative overflow-hidden rounded-3xl bg-secondary-fixed p-6 md:p-8 shadow-[0_8px_32px_rgba(0,0,0,0.08)] flex flex-col md:flex-row items-center gap-6">
      <div className="flex-1 z-10 w-full">
        <div className="inline-flex items-center gap-2 bg-white/60 px-3 py-1 rounded-full mb-4">
          <span className={`w-2 h-2 rounded-full ${copy.badgeColor}`} />
          <span className="text-sm font-medium text-on-surface">
            Update: {lastUpdatedLabel}
          </span>
        </div>
        <h2 className="text-2xl md:text-3xl font-bold text-on-secondary-fixed mb-2">
          {copy.title}
        </h2>
        <p className="text-base md:text-lg text-on-secondary-fixed/80 max-w-md">
          {copy.description}
        </p>
      </div>
      <div className="w-full md:w-1/3 h-40 md:h-full relative flex items-center justify-center z-10">
        <span
          className="material-symbols-outlined text-primary/70"
          style={{ fontSize: "96px" }}
          aria-hidden
        >
          pulmonology
        </span>
      </div>
      <div className="absolute -bottom-24 -right-24 w-64 h-64 bg-primary-container/20 rounded-full blur-3xl z-0" />
    </section>
  );
}
