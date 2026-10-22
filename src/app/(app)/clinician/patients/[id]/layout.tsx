import { ClinicianPatientProvider, DetailHeader } from "@/components/portal/PatientDetail";
import { Topbar } from "@/components/portal/Shell";

// Data pasien dimuat di klien dari API (butuh sesi login), jadi halaman ini dirender per permintaan.
export default async function PatientDetailLayout({ children, params }: LayoutProps<"/clinician/patients/[id]">) {
  const { id } = await params;
  return (
    <>
      <Topbar role="clinician" title="Detail Pasien" subtitle="Pemantauan kardio-respirasi dan peninjauan klinis." />
      <ClinicianPatientProvider id={id}>
        <DetailHeader />
        {children}
      </ClinicianPatientProvider>
    </>
  );
}
