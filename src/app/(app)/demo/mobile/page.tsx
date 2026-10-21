import type { Metadata } from "next";
import Link from "next/link";
import { LabHeader, LabMain } from "@/components/lab/LabHeader";
import { ArrowRight, Icon } from "@/components/ui/Icon";

export const metadata: Metadata = { title: "Contoh Mobile" };

const PHONES: [string, string][] = [
  ["Landing Page", "/"],
  ["Login", "/login"],
  ["Beranda Pasien", "/patient/home"],
  ["Daftar Pasien", "/clinician/patients"],
];

export default function MobilePage() {
  return (
    <LabMain>
      <LabHeader title="Contoh Mobile" description="Lembar pelengkap 3, Halaman HTML asli dalam viewport ponsel." />
      <div className="grid grid-cols-2 gap-[35px] items-start max-md:grid-cols-[1fr]">
        {PHONES.map(([title, route]) => (
          <section key={route}>
            <h3 className="my-3 text-center text-[13px]">{title}</h3>
            <div className="border-[6px] border-[#243f34] rounded-[24px] bg-white overflow-hidden w-full max-w-[390px] m-auto">
              <iframe title={`Contoh mobile ${title}`} src={route} loading="lazy" className="block w-full h-[740px] border-0" />
            </div>
            <p className="text-center mt-6">
              <Link href={route} className="inline-flex items-center gap-3 justify-center">
                Buka halaman <Icon icon={ArrowRight} />
              </Link>
            </p>
          </section>
        ))}
      </div>
    </LabMain>
  );
}
