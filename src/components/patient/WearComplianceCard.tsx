type WearComplianceCardProps = {
  hoursWorn: number;
  targetHours: number;
};

export function WearComplianceCard({
  hoursWorn,
  targetHours,
}: WearComplianceCardProps) {
  const progressPercent = Math.min(
    100,
    Math.round((hoursWorn / targetHours) * 100)
  );

  return (
    <section className="rounded-xl border border-outline-variant/30 bg-surface-container-lowest p-5 shadow-[0_4px_16px_rgba(0,0,0,0.04)]">
      <div className="flex items-center gap-3 mb-3">
        <span className="material-symbols-outlined text-primary">schedule</span>
        <h3 className="text-base font-semibold">Pemakaian Vest Hari Ini</h3>
      </div>
      <p className="text-base text-on-surface-variant mb-4">
        Anda memakai vest{" "}
        <strong className="text-on-surface tabular-nums">{hoursWorn}</strong>{" "}
        dari {targetHours} jam target hari ini 👍
      </p>
      <div className="w-full h-3 rounded-full bg-surface-variant mb-2">
        <div
          className="h-3 rounded-full bg-primary"
          style={{ width: `${progressPercent}%` }}
        />
      </div>
      <div className="flex justify-between text-sm text-on-surface-variant">
        <span>0 jam</span>
        <span>Target: {targetHours} jam</span>
      </div>
    </section>
  );
}
