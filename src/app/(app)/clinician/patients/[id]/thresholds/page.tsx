import type { Metadata } from "next";
import { ThresholdsTab } from "@/components/portal/PatientDetail";

export const metadata: Metadata = { title: "Detail: Konfigurasi Ambang" };

export default async function PatientThresholdsPage({ params }: PageProps<"/clinician/patients/[id]/thresholds">) {
  const { id } = await params;
  return <ThresholdsTab id={id} />;
}
