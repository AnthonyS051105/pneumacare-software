import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import carePatient from "@/assets/care-patient.png";
import { AlertItem } from "@/components/portal/AlertItem";
import { Connection } from "@/components/portal/Connection";
import { notificationsCard, stack, split } from "@/components/portal/layout";
import { Metric, metricsGrid } from "@/components/portal/Metric";
import { CareTeamPanel, VitalSwitcherCard } from "@/components/portal/PatientHomeWidgets";
import { Topbar } from "@/components/portal/Shell";
import { ArrowRight, Check, Icon } from "@/components/ui/Icon";
import { alerts, CURRENT_PATIENT_ID, vitalKeys } from "@/lib/demo-data";

export const metadata: Metadata = { title: "Beranda Pasien" };

export default function PatientHomePage() {
  return (
    <>
      <Topbar role="patient" greeting subtitle="Pantau kondisi Anda dan lanjutkan hari dengan lebih tenang." />
      <div className={stack}>
        <section className="flex items-center gap-[13px] bg-[#e8f5f0] border border-[#d7eae3] rounded-[6px] px-5 py-4 max-md:p-3.5 max-md:gap-2.5">
          <div className="grid place-items-center size-7 rounded-full bg-primary text-white shrink-0 max-md:hidden">
            <Icon icon={Check} className="size-[17px]" />
          </div>
          <div className="max-md:min-w-0 max-md:flex-1">
            <h2 className="text-[16px] tracking-normal max-md:text-[14px] max-md:leading-[1.4]">
              Tidak ada peringatan aktif
            </h2>
            <p className="text-[12px] mt-0.5 text-[#466554] max-md:text-[11px] max-md:leading-[1.6]">
              Pembacaan terbaru Anda tersaji di bawah ini.
            </p>
          </div>
          <span className="ml-auto text-[12px] text-[#466554] text-right max-2xl:hidden">
            Terakhir diperbarui
            <br />
            09.30 WIB
          </span>
          <div className="w-[120px] h-[84px] flex-[0_0_120px] overflow-hidden [mask-image:linear-gradient(to_right,transparent,#000_14%,#000_90%,transparent)] max-2xl:w-[98px] max-2xl:h-[76px] max-2xl:basis-[98px] max-md:w-[82px] max-md:h-[72px] max-md:basis-[82px] max-md:ml-auto">
            <Image
              src={carePatient}
              alt="Pasien melakukan pemantauan dari rumah"
              sizes="120px"
              className="w-full h-full object-contain"
            />
          </div>
        </section>
        <div className={metricsGrid}>
          {vitalKeys.map((k) => (
            <Metric key={k} vital={k} />
          ))}
        </div>
        <div className={split}>
          <VitalSwitcherCard />
          <CareTeamPanel />
        </div>
        <section className={notificationsCard}>
          <div className="flex items-center justify-between gap-3 *:min-w-0 max-md:flex-wrap">
            <h3 className="max-md:text-[16px]">Notifikasi terbaru</h3>
            <Link href="/patient/alerts" className="flex items-center gap-3 max-md:text-[12px] max-md:gap-2 max-md:min-h-11">
              Lihat semua <Icon icon={ArrowRight} />
            </Link>
          </div>
          {alerts
            .filter((a) => a.patient === CURRENT_PATIENT_ID)
            .slice(0, 2)
            .map((a) => (
              <AlertItem key={a.id} alert={a} />
            ))}
        </section>
        <div className="mt-1">
          <Connection />
        </div>
      </div>
    </>
  );
}
