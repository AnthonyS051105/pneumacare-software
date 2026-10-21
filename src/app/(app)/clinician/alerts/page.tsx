import type { Metadata } from "next";
import { ClinicianAlertsView } from "@/components/portal/ClinicianAlertsView";
import { Topbar } from "@/components/portal/Shell";

export const metadata: Metadata = { title: "Pusat Notifikasi Tenaga Medis" };

export default function ClinicianAlertsPage() {
  return (
    <>
      <Topbar role="clinician" title="Pusat Notifikasi" subtitle="Tinjau pemberitahuan seluruh pasien dalam pemantauan." />
      <ClinicianAlertsView />
    </>
  );
}
