import type { Metadata } from "next";
import { AlertsTab } from "@/components/portal/PatientDetail";

export const metadata: Metadata = { title: "Detail: Riwayat Alert" };

export default async function PatientAlertsTabPage({ params }: PageProps<"/clinician/patients/[id]/alerts">) {
  const { id } = await params;
  return <AlertsTab id={id} />;
}
