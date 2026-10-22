import type { Metadata } from "next";
import { AlertsTab } from "@/components/portal/PatientDetail";

export const metadata: Metadata = { title: "Detail: Riwayat Alert" };

export default function PatientAlertsTabPage() {
  return <AlertsTab />;
}
