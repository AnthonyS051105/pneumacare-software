"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { authMuted } from "@/components/auth/AuthLayout";
import { ArrowRight, Icon, Stethoscope, UserRound } from "@/components/ui/Icon";
import { btn, cn } from "@/components/ui/primitives";
import { useUi } from "@/lib/demo-store";

const ROLES = [
  ["pasien", "Saya adalah Pasien", "Pantau kondisi dan riwayat kesehatan Anda."],
  ["clinician", "Saya adalah Tenaga Medis", "Tinjau dan dampingi pemantauan pasien Anda."],
] as const;

export function SignupRole() {
  const router = useRouter();
  const [role, setRole] = useUi("chosenRole");
  return (
    <>
      {ROLES.map(([value, title, text]) => {
        const selected = role === value;
        return (
          <button
            key={value}
            type="button"
            aria-pressed={selected}
            onClick={() => setRole(value)}
            className={cn(
              "flex items-center gap-4 w-full min-h-[110px] my-3.5 px-[18px] py-[22px] rounded-[6px] border text-left text-ink max-md:px-4 max-md:py-5",
              selected ? "border-primary bg-[#f1f5ee] shadow-[inset_3px_0_var(--color-primary)]" : "border-line bg-white",
            )}
          >
            <Icon icon={value === "clinician" ? Stethoscope : UserRound} className="size-7 text-teal" />
            <div>
              <h3 className="text-[15px] max-md:text-[14px]">{title}</h3>
              <p className="text-[12px] text-muted mt-1.5">{text}</p>
            </div>
            <span
              aria-hidden="true"
              className={cn(
                "size-[17px] rounded-full ml-auto shrink-0",
                selected ? "border-[5px] border-primary" : "border border-[#a4b5a6]",
              )}
            />
          </button>
        );
      })}
      <button
        type="button"
        className={cn(btn({ variant: "primary", full: true }), "mt-6")}
        onClick={() => router.push(role === "clinician" ? "/signup/clinician" : "/signup/patient")}
      >
        Lanjut <Icon icon={ArrowRight} />
      </button>
      <p className={cn("text-center mt-6", authMuted)}>
        Sudah memiliki akun? <Link href="/login">Masuk</Link>
      </p>
    </>
  );
}
