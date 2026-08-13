const navItems = [
  { label: "Beranda", icon: "home", href: "/patient/home" },
  { label: "Riwayat", icon: "history", href: "/patient/history" },
  { label: "Notifikasi", icon: "notifications", href: "/patient/alerts" },
  { label: "Profil", icon: "person", href: "/patient/profile" },
];

type PatientSidebarProps = {
  patientName: string;
  patientId: string;
  statusLabel: string;
  activeHref?: string;
};

export function PatientSidebar({
  patientName,
  patientId,
  statusLabel,
  activeHref = "/patient/home",
}: PatientSidebarProps) {
  const initials = patientName
    .split(" ")
    .map((part) => part[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <aside className="hidden md:flex w-sidebar-width h-full fixed left-0 top-0 flex-col gap-2 p-4 bg-surface-container-lowest border-r border-outline-variant z-40">
      <div className="flex items-center gap-3 px-4 py-6">
        <span className="material-symbols-outlined text-primary text-3xl">
          pulmonology
        </span>
        <span className="text-2xl font-bold text-primary tracking-tight">
          PNEUMACARE
        </span>
      </div>

      <div className="flex items-center gap-4 px-4 py-6 mb-4">
        <div className="w-12 h-12 rounded-full bg-primary-container text-on-primary-container flex items-center justify-center font-bold text-lg shrink-0">
          {initials}
        </div>
        <div className="min-w-0">
          <h3 className="text-lg font-bold truncate">{patientName}</h3>
          <p className="text-sm text-on-surface-variant">
            Patient ID: {patientId}
          </p>
          <p className="text-sm text-status-success">Status: {statusLabel}</p>
        </div>
      </div>

      <nav className="flex-1 flex flex-col gap-2">
        {navItems.map((item) => {
          const isActive = item.href === activeHref;
          return (
            <a
              key={item.href}
              href={item.href}
              className={
                isActive
                  ? "flex items-center gap-3 bg-secondary-container text-on-secondary-container rounded-xl px-4 py-3 border-l-4 border-primary transition-transform duration-200 active:scale-95"
                  : "flex items-center gap-3 text-on-surface-variant px-4 py-3 rounded-xl hover:bg-secondary-fixed/50 transition-colors duration-200 active:scale-95"
              }
            >
              <span
                className="material-symbols-outlined"
                style={isActive ? { fontVariationSettings: "'FILL' 1" } : undefined}
              >
                {item.icon}
              </span>
              <span className="text-base font-semibold">{item.label}</span>
            </a>
          );
        })}
      </nav>
    </aside>
  );
}
