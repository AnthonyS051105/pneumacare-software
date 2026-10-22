import type { Metadata } from "next";
import { ThresholdsTab } from "@/components/portal/PatientDetail";

export const metadata: Metadata = { title: "Detail: Konfigurasi Ambang" };

export default function PatientThresholdsPage() {
  return <ThresholdsTab />;
}
