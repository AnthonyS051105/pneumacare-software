import type { Metadata } from "next";
import { PatientHomeView } from "@/components/portal/PatientHomeView";

export const metadata: Metadata = { title: "Beranda Pasien" };

export default function PatientHomePage() {
  return <PatientHomeView />;
}
