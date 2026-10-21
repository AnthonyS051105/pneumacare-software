import type { Metadata } from "next";
import { ClinicianPatientsView } from "@/components/portal/ClinicianPatientsView";
import { Topbar } from "@/components/portal/Shell";

export const metadata: Metadata = { title: "Daftar Pasien Tenaga Medis" };

export default function ClinicianPatientsPage() {
  return (
    <>
      <Topbar
        role="clinician"
        title="Pasien Saya"
        subtitle="Tinjau kondisi dan prioritaskan pasien yang memerlukan perhatian."
      />
      <ClinicianPatientsView />
    </>
  );
}
