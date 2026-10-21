import Link from "next/link";
import type { ReactNode } from "react";
import { CircleAlert, Icon, Info, TriangleAlert } from "@/components/ui/Icon";
import type { IconNode } from "lucide";

export const cn = (...classes: (string | false | null | undefined)[]) => classes.filter(Boolean).join(" ");

/* ---------- Tombol (.btn) ---------- */

type BtnVariant = "default" | "primary" | "ghost" | "danger";

const btnBase =
  "inline-flex items-center justify-center gap-[9px] rounded-[8px] border font-semibold leading-[1.4] transition-[background,border-color] duration-180 ease-[ease] hover:no-underline";

const btnColors: Record<BtnVariant, string> = {
  default: "bg-white border-line text-navy hover:bg-[#f0f7f4] hover:border-[#9caea4]",
  primary: "bg-primary border-primary text-white hover:bg-navy hover:border-navy",
  ghost: "bg-transparent border-transparent text-navy hover:bg-[#f0f7f4] hover:border-[#9caea4]",
  danger: "bg-white border-[#dbbabe] text-red hover:bg-[#f0f7f4] hover:border-[#9caea4]",
};

export function btn({
  variant = "default",
  small = false,
  full = false,
}: { variant?: BtnVariant; small?: boolean; full?: boolean } = {}) {
  const size = small
    ? "px-3 py-2 min-h-[38px] text-[12px]"
    : variant === "ghost"
      ? "p-2 min-h-10 text-[13px]"
      : "px-[18px] py-[11px] min-h-11 text-[13px]";
  return cn(btnBase, btnColors[variant], size, full && "w-full");
}

/* ---------- Kartu (.card) ---------- */

export const card = "bg-white border border-line rounded-[12px] min-w-0";
export const cardPad = "p-6 max-2xl:p-5";

/* ---------- Brand ---------- */

export function Brand({ variant = "default" }: { variant?: "default" | "auth" | "header" }) {
  const header = variant === "header";
  return (
    <Link
      href="/"
      aria-label="PNEUMACARE beranda"
      className={cn(
        "inline-flex items-center font-bold whitespace-nowrap leading-[1.1] hover:no-underline",
        header
          ? "gap-[7px] max-2xl:gap-[5px] text-[25px] tracking-[.2px] text-[#0c3442] max-md:text-[22px]"
          : "gap-[7px] text-[18px] tracking-[.3px] text-teal max-2xl:gap-[5px] max-2xl:text-[15px]",
        variant === "auth" && "max-md:text-[17px]",
      )}
    >
      <svg
        viewBox="0 0 44 44"
        fill="none"
        aria-hidden="true"
        className={header ? "hidden" : "w-[29px] h-8 shrink-0 max-2xl:w-[25px]"}
      >
        <path
          d="M20 6v15l-7-8C8 15 4 22 4 30c0 5 3 8 7 8 5 0 8-4 8-9v-8M24 6v15l7-8c5 2 9 9 9 17 0 5-3 8-7 8-5 0-8-4-8-9v-8M15 23l7-5 7 5"
          stroke="currentColor"
          strokeWidth="3.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      <span>
        PNEUMA<span className={cn("font-normal", header && "text-[#14898e]")}>CARE</span>
      </span>
    </Link>
  );
}

/* ---------- Avatar inisial ---------- */

export function initials(name: string) {
  return String(name)
    .replace(/^dr\.\s*/i, "")
    .trim()
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0] || "")
    .join("")
    .toUpperCase();
}

const avatarSize = {
  md: "size-[38px] text-[12px]",
  lg: "size-[58px] text-[18px]",
  team: "size-12 text-[17px]",
};

export function Avatar({
  name,
  size = "md",
  clinical = false,
  className,
}: {
  name: string;
  size?: keyof typeof avatarSize;
  clinical?: boolean;
  className?: string;
}) {
  return (
    <span
      aria-label={name}
      className={cn(
        "inline-flex items-center justify-center shrink-0 border border-[#d5e6e1] rounded-full font-semibold leading-none",
        clinical ? "bg-[#eaf0f5] text-[#385b73]" : "bg-[#e5f1ed] text-navy",
        avatarSize[size],
        className,
      )}
    >
      {initials(name)}
    </span>
  );
}

/* ---------- Pill ---------- */

export type PillTone = "" | "warn" | "urgent" | "off";

export const pillTone: Record<PillTone, string> = {
  "": "bg-[#e7f5f0] text-[#237769]",
  warn: "bg-[#faf0da] text-amber",
  urgent: "bg-[#f9e8e7] text-red",
  off: "bg-[#eef0ed] text-[#5f6e65]",
};

export const pillBase =
  "inline-flex items-center gap-1.5 px-2 py-[3px] text-[11px] font-semibold rounded-[4px] whitespace-nowrap leading-[1.6]";

export function Pill({ tone = "", className, children }: { tone?: PillTone; className?: string; children: ReactNode }) {
  return <span className={cn(pillBase, pillTone[tone], className)}>{children}</span>;
}

/* ---------- Notice ---------- */

const noticeTone = {
  "": "bg-[#edf2ee] border-[#dce5de] text-[#476355]",
  warn: "bg-[#faf5e9] border-[#ece0c5] text-[#805c21]",
  error: "bg-[#fcf0ee] border-[#eacdc9] text-red",
};

export function Notice({
  type = "",
  small = false,
  className,
  children,
}: {
  type?: "" | "warn" | "error";
  /** 11px — dipakai di panel autentikasi (.auth-right .notice). */
  small?: boolean;
  className?: string;
  children: ReactNode;
}) {
  const icon = type === "warn" ? TriangleAlert : type === "error" ? CircleAlert : Info;
  return (
    <div
      className={cn(
        "flex gap-2.5 items-start px-4 py-[13px] rounded-[5px] border",
        small ? "text-[11px]" : "text-[12px]",
        noticeTone[type],
        className,
      )}
    >
      <Icon icon={icon} className="size-[17px] mt-0.5" />
      <div>{children}</div>
    </div>
  );
}

/* ---------- Empty state ---------- */

export function Empty({
  icon,
  title,
  text,
  action,
}: {
  icon: IconNode;
  title: string;
  text: string;
  action?: ReactNode;
}) {
  return (
    <div className="grid place-items-center text-center px-5 py-10 gap-3">
      <Icon icon={icon} className="size-8 text-[#87a18e]" />
      <h3>{title}</h3>
      <p className="text-muted max-w-[42ch]">{text}</p>
      {action}
    </div>
  );
}

/* ---------- Segmented control ---------- */

export const segments =
  "inline-flex border border-line rounded-[5px] overflow-hidden bg-[#f7f9f5] p-[3px] gap-0.5";

export function segmentButton(active: boolean) {
  return cn(
    "border-0 rounded-[3px] min-h-8 px-[13px] py-[5px] text-[12px] whitespace-nowrap max-md:px-[11px] max-md:py-1.5 max-md:min-h-[34px]",
    active ? "bg-primary text-white" : "bg-transparent text-muted",
  );
}

/* ---------- Legend (grafik) ---------- */

export function LegendItem({ color = "primary", children }: { color?: "primary" | "rose" | "blue"; children: ReactNode }) {
  // .legend .blue di referensi juga mewarnai teksnya (kelas global .blue).
  const bar = color === "rose" ? "before:bg-rose" : color === "blue" ? "before:bg-blue text-blue" : "before:bg-primary";
  return (
    <span
      className={cn(
        "before:content-[''] before:inline-block before:w-[15px] before:h-0.5 before:mr-1.5 before:align-middle",
        bar,
      )}
    >
      {children}
    </span>
  );
}
