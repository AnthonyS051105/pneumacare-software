import type { Metadata } from "next";
import { VitalsTab } from "@/components/portal/PatientDetail";

export const metadata: Metadata = { title: "Detail: Vital Real-time" };

export default async function PatientVitalsPage({ params }: PageProps<"/clinician/patients/[id]">) {
  const { id } = await params;
  return <VitalsTab id={id} />;
}
