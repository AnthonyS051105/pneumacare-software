import type { Metadata } from "next";
import { VitalsTab } from "@/components/portal/PatientDetail";

export const metadata: Metadata = { title: "Detail: Vital Real-time" };

export default function PatientVitalsPage() {
  return <VitalsTab />;
}
