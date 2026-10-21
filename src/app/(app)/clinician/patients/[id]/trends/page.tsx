import type { Metadata } from "next";
import { TrendsTab } from "@/components/portal/PatientDetail";

export const metadata: Metadata = { title: "Detail: Tren & Severity" };

export default function PatientTrendsPage() {
  return <TrendsTab />;
}
