"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useFeedback } from "@/components/providers/Feedback";
import { Bell, ChartNoAxesCombined, House, Icon, LogOut, UserRound, Users } from "@/components/ui/Icon";
import { Avatar, Brand, cn } from "@/components/ui/primitives";
import { useDemo } from "@/lib/demo-store";

export type PortalRole = "patient" | "clinician";

const ROUTES = {
  clinician: [
    ["/clinician/patients", Users, "Pasien"],
    ["/clinician/alerts", Bell, "Pusat Notifikasi"],
    ["/clinician/profile", UserRound, "Profil"],
  ],
  patient: [
    ["/patient/home", House, "Beranda"],
    ["/patient/history", ChartNoAxesCombined, "Riwayat"],
    ["/patient/alerts", Bell, "Notifikasi"],
    ["/patient/profile", UserRound, "Profil"],
  ],
} as const;

function useActive() {
  const pathname = usePathname();
  return (route: string) => (route === "/clinician/patients" ? pathname.startsWith(route) : pathname === route);
}

function useUser(role: PortalRole) {
  return useDemo((d) => (role === "clinician" ? d.clinician.name : d.patient.name));
}

export function SkipLink() {
  return (
    <a href="#main-content" className="fixed left-[15px] -top-20 z-200 bg-navy text-white px-[18px] py-2.5 focus:top-3">
      Langsung ke konten
    </a>
  );
}

export function Sidebar({ role }: { role: PortalRole }) {
  const isActive = useActive();
  const name = useUser(role);
  const { openModal } = useFeedback();
  const clinician = role === "clinician";
  return (
    <aside className="fixed inset-y-0 left-0 z-20 flex flex-col w-[232px] bg-white border-r border-line pt-8 px-5 pb-5 max-2xl:w-[200px] max-2xl:py-7 max-2xl:px-[15px] max-md:hidden">
      <Brand />
      <p className="mt-4 ml-1 text-[10px] tracking-[1.6px] text-muted uppercase">
        Portal {clinician ? "tenaga medis" : "pasien"}
      </p>
      <nav aria-label="Navigasi utama" className="mt-10 -mx-2 grid gap-1.5">
        {ROUTES[role].map(([href, icon, label]) => {
          const active = isActive(href);
          return (
            <Link
              key={href}
              href={href}
              aria-current={active ? "page" : undefined}
              className={cn(
                "relative flex items-center gap-[13px] px-3.5 py-3 rounded-[5px] min-h-[46px] hover:no-underline",
                active
                  ? "bg-[#e6f3ef] text-navy font-semibold before:content-[''] before:absolute before:left-0 before:top-[13px] before:bottom-[13px] before:w-[3px] before:bg-primary"
                  : "text-[#56675e] hover:bg-[#f3f8f6]",
              )}
            >
              <Icon icon={icon} />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto pt-[22px] border-t border-line">
        <Link href={`/${role}/profile`} className="flex gap-2.5 items-center mb-[15px]">
          <Avatar name={name} clinical={clinician} />
          <div>
            <strong className="block text-[12px] max-w-[130px] overflow-hidden text-ellipsis">{name}</strong>
            <small className="block text-[11px]">{clinician ? "Tenaga medis" : "Pasien"}</small>
          </div>
        </Link>
        <button
          type="button"
          onClick={() => openModal("logout")}
          className="inline-flex items-center justify-start gap-[9px] w-full min-h-10 py-2 pr-2 pl-0 rounded-[8px] border border-transparent bg-transparent text-muted font-semibold text-[13px] leading-[1.4] transition-[background,border-color] duration-180 ease-[ease] hover:bg-[#f0f7f4] hover:border-[#9caea4]"
        >
          <Icon icon={LogOut} />
          Keluar dari akun
        </button>
      </div>
    </aside>
  );
}

export function BottomNav({ role }: { role: PortalRole }) {
  const isActive = useActive();
  return (
    <nav
      aria-label="Navigasi mobile"
      className="hidden max-md:flex fixed bottom-0 inset-x-0 z-30 justify-around bg-white border-t border-line pt-2.5 px-2 pb-[max(10px,env(safe-area-inset-bottom))]"
    >
      {ROUTES[role].map(([href, icon, label]) => {
        const active = isActive(href);
        return (
          <Link
            key={href}
            href={href}
            aria-current={active ? "page" : undefined}
            className={cn(
              "flex flex-col items-center gap-[5px] px-2.5 py-0.5 min-w-[65px] text-[10px]",
              active ? "text-teal font-semibold" : "text-[#657666]",
            )}
          >
            <Icon icon={icon} />
            <span>{role === "clinician" && label === "Pusat Notifikasi" ? "Notifikasi" : label}</span>
          </Link>
        );
      })}
    </nav>
  );
}

export function Topbar({
  role,
  title,
  subtitle,
  greeting = false,
}: {
  role: PortalRole;
  title?: string;
  subtitle: string;
  /** Beranda pasien: judul berupa sapaan dari nama pasien tersimpan. */
  greeting?: boolean;
}) {
  const name = useUser(role);
  const heading = greeting
    ? "Selamat pagi, " + (name === "Budi Santoso" ? "Pak Budi" : name.split(" ")[0])
    : title;
  return (
    <header className="flex justify-between items-center gap-5 mb-7 max-md:mb-6 max-md:items-start max-md:gap-3">
      <div className="min-w-0">
        <h1 className="max-2xl:text-[27px] max-md:text-[25px] max-xs:text-[23px]">{heading}</h1>
        <p className="mt-2 text-muted text-[13px] max-md:text-[12px] max-md:max-w-[40ch]">{subtitle}</p>
      </div>
      <div className="flex items-center gap-[15px] shrink-0 max-2xl:gap-2.5">
        <Link
          href={`/${role}/alerts`}
          aria-label="Buka notifikasi"
          className="relative grid place-items-center size-[42px] rounded-[6px] border border-line bg-white max-md:size-[38px]"
        >
          <Icon icon={Bell} />
        </Link>
        <Avatar name={name} clinical={role === "clinician"} className="max-tb:hidden" />
      </div>
    </header>
  );
}
