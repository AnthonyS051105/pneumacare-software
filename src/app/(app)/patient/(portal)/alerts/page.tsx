import type { Metadata } from "next";
import { PatientAlertsView } from "@/components/portal/PatientAlertsView";
import { Topbar } from "@/components/portal/Shell";

export const metadata: Metadata = { title: "Notifikasi Pasien" };

export default function PatientAlertsPage() {
  return (
    <>
      <Topbar role="patient" title="Notifikasi" subtitle="Pemberitahuan pemantauan dan status perangkat Anda." />
      <PatientAlertsView />
    </>
  );
}
