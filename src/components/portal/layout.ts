import { card, cn } from "@/components/ui/primitives";

// Kelas tata letak bersama area dashboard (padanan .stack, .split, .mt, dst. di referensi).

export const stack = "grid min-w-0 gap-[22px] max-md:gap-4";
export const split =
  "grid gap-[22px] grid-cols-[minmax(0,2.25fr)_minmax(260px,1fr)] max-2xl:grid-cols-[minmax(0,1.7fr)_minmax(235px,1fr)] max-tb:grid-cols-[1fr]";
export const row = "flex items-center gap-3 *:min-w-0";
export const rowBetween = "flex items-center justify-between gap-3 *:min-w-0";
export const notificationsCard = cn(card, "p-6 max-2xl:p-5 max-md:p-[18px]");
export const chartGrid = "grid min-w-0 grid-cols-2 gap-[22px] max-tb:grid-cols-[1fr]";
export const formGrid = "grid grid-cols-2 gap-5 max-md:grid-cols-[1fr]";
export const toolbar = "flex flex-wrap items-center gap-3 mb-5 max-md:gap-2.5";
export const toolbarSelect =
  "border border-line rounded-[5px] py-[11px] pr-[30px] pl-3 bg-white text-ink min-h-[45px] text-[12px] max-md:flex-1 max-md:min-w-0 max-md:max-w-full max-md:pr-5";
