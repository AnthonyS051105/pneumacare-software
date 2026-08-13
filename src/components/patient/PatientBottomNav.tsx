const navItems = [
  { label: "Beranda", icon: "home", href: "/patient/home" },
  { label: "Riwayat", icon: "history", href: "/patient/history" },
  { label: "Notifikasi", icon: "notifications", href: "/patient/alerts" },
  { label: "Profil", icon: "person", href: "/patient/profile" },
];

type PatientBottomNavProps = {
  activeHref?: string;
};

export function PatientBottomNav({
  activeHref = "/patient/home",
}: PatientBottomNavProps) {
  return (
    <nav className="md:hidden fixed bottom-0 left-0 z-50 flex w-full items-center justify-around px-2 py-2 bg-surface-container shadow-[0_-8px_32px_rgba(0,0,0,0.08)] rounded-t-xl">
      {navItems.map((item) => {
        const isActive = item.href === activeHref;
        return (
          <a
            key={item.href}
            href={item.href}
            className={
              isActive
                ? "flex flex-col items-center justify-center bg-primary-container text-on-primary-container rounded-full px-6 py-1 transition-transform duration-300"
                : "flex flex-col items-center justify-center text-on-surface-variant px-4 py-1 hover:text-primary transition-colors duration-300"
            }
          >
            <span
              className="material-symbols-outlined"
              style={isActive ? { fontVariationSettings: "'FILL' 1" } : undefined}
            >
              {item.icon}
            </span>
            <span className="text-xs font-medium mt-1">{item.label}</span>
          </a>
        );
      })}
    </nav>
  );
}
