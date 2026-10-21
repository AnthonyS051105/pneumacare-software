import type { ReactNode } from "react";
import { Brand } from "@/components/ui/primitives";

export const galleryMain = "block max-w-[1200px] m-auto pt-[42px] px-7 pb-[70px] max-md:pt-7 max-md:px-[18px] max-md:pb-[60px]";
export const grid2 = "grid min-w-0 grid-cols-2 gap-[22px] max-md:grid-cols-[1fr] max-md:gap-4";
export const grid3 = "grid min-w-0 grid-cols-3 gap-[22px] max-md:grid-cols-[1fr] max-md:gap-4";

export function LabHeader({ title, description }: { title: string; description: string }) {
  return (
    <header className="mb-5">
      <Brand />
      <h1 className="mt-6 max-w-[26ch] max-md:text-[27px]">{title}</h1>
      <p className="text-muted">{description}</p>
    </header>
  );
}

export function LabMain({ children }: { children: ReactNode }) {
  return (
    <main className={galleryMain} id="main-content">
      {children}
    </main>
  );
}
