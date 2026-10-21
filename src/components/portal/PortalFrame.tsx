import type { ReactNode } from "react";
import { BottomNav, Sidebar, SkipLink, type PortalRole } from "@/components/portal/Shell";

/** Kerangka dashboard: sidebar (desktop), area kerja, dan navigasi bawah (mobile). */
export function PortalFrame({ role, children }: { role: PortalRole; children: ReactNode }) {
  return (
    <>
      <SkipLink />
      <Sidebar role={role} />
      <main
        id="main-content"
        tabIndex={-1}
        className="ml-[232px] min-h-screen min-w-0 max-w-[1720px] pt-9 pb-10 px-[clamp(22px,3vw,48px)] 3xl:py-11 3xl:px-[52px] max-2xl:ml-[200px] max-2xl:py-7 max-2xl:px-6 max-md:ml-0 max-md:pt-6 max-md:pb-[100px] max-md:px-[18px] max-xs:px-[13px]"
      >
        {children}
      </main>
      <BottomNav role={role} />
    </>
  );
}
