type PatientTopBarProps = {
  patientName: string;
};

export function PatientTopBar({ patientName }: PatientTopBarProps) {
  const initials = patientName
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <header className="md:hidden sticky top-0 z-30 w-full bg-surface">
      <div className="flex items-center justify-between px-4 py-4 w-full">
        <button
          type="button"
          aria-label="Buka menu"
          className="text-on-surface-variant rounded-full p-2 hover:bg-surface-variant/20 active:opacity-70 transition-opacity"
        >
          <span className="material-symbols-outlined text-2xl">menu</span>
        </button>
        <h1 className="text-xl font-bold text-primary tracking-tight">
          PNEUMACARE
        </h1>
        <button
          type="button"
          aria-label="Profil"
          className="rounded-full p-2 hover:bg-surface-variant/20 active:opacity-70 transition-opacity"
        >
          <div className="w-8 h-8 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center font-bold text-sm">
            {initials}
          </div>
        </button>
      </div>
    </header>
  );
}
