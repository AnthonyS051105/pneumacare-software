import Image from "next/image";
import type { ReactNode } from "react";
import carePatient from "@/assets/care-patient.png";
import { Brand } from "@/components/ui/primitives";

/** Tata letak dua kolom halaman masuk/daftar (padanan authLayout() di referensi). */
export function AuthLayout({ heading, subtitle, children }: { heading: ReactNode; subtitle?: string; children: ReactNode }) {
  return (
    <main
      id="main-content"
      className="min-h-svh bg-white grid grid-cols-[minmax(0,46%)_minmax(0,54%)] max-tb:grid-cols-[40%_60%] max-md:block"
    >
      <section className="relative overflow-hidden flex flex-col items-start bg-mint py-[38px] px-[clamp(32px,5vw,76px)] max-2xl:p-8 max-tb:p-7 max-md:px-[22px] max-md:py-6 max-md:min-h-0">
        <Brand variant="auth" />
        <h1 className="font-semibold text-[clamp(30px,3vw,42px)] leading-[1.2] tracking-[-1px] mt-[76px] max-w-[430px] max-2xl:text-[37px] max-tb:text-[32px] max-md:hidden">
          {heading}
        </h1>
        <p className="mt-[22px] text-[#587263] text-[14px] max-w-[35ch] leading-[1.75] max-md:hidden">
          {subtitle ??
            "Lihat kondisi pernapasan, ikuti riwayat pemantauan, dan tetap terhubung dengan tenaga medis Anda."}
        </p>
        <div className="w-[calc(100%+40px)] -mx-5 flex-1 grid place-items-center min-h-[200px] mt-5 max-md:hidden">
          <Image
            src={carePatient}
            alt="Ilustrasi pasien melihat informasi pemantauan di ponsel, dari rumah"
            sizes="(max-width: 960px) 40vw, 520px"
            className="w-full max-w-[520px] h-[1024px] max-h-[390px] object-contain"
          />
        </div>
        <div className="text-[10px] text-[#587263] mt-6 flex w-full justify-between border-t border-[#cdd9ca] pt-[18px] max-tb:block max-md:hidden">
          <span className="max-tb:block">Pemantauan dari rumah</span>
          <span className="max-tb:block">Tim PNEUMA, UGM</span>
        </div>
      </section>
      <section className="flex items-center justify-center py-12 px-[clamp(28px,6vw,95px)] max-2xl:p-10 max-tb:py-9 max-tb:px-7 max-md:pt-8 max-md:px-[22px] max-md:pb-[50px] max-xs:px-[18px]">
        <div className="w-full max-w-[460px]">{children}</div>
      </section>
    </main>
  );
}

export const authTitle = "text-[29px] mt-[26px] mb-3 tracking-[-.8px] max-md:text-[27px] max-md:mt-[22px]";
export const authMuted = "text-muted text-[13px]";
export const authFormGrid = "grid grid-cols-2 gap-[17px] max-md:grid-cols-[1fr]";

export function Stepper({ step }: { step: 1 | 2 }) {
  const dot = "inline-grid place-items-center size-6 rounded-full mr-[5px]";
  return (
    <div className="flex items-center gap-2.5 text-[11px] my-7">
      <span>
        <b className={`${dot} bg-primary text-white`}>1</b>Pilih peran
      </span>
      <span className="flex-1 h-px bg-line" />
      <span className={step === 1 ? "text-muted" : undefined}>
        <b className={`${dot} ${step === 1 ? "bg-[#eef1eb] text-[#778677]" : "bg-primary text-white"}`}>2</b>
        Lengkapi data
      </span>
    </div>
  );
}
