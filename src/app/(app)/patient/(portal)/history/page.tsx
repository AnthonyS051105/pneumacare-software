import type { Metadata } from "next";
import { HistoryView } from "@/components/portal/HistoryView";
import { Topbar } from "@/components/portal/Shell";

export const metadata: Metadata = { title: "Riwayat Pasien" };

export default function PatientHistoryPage() {
  return (
    <>
      <Topbar role="patient" title="Riwayat Pemantauan" subtitle="Lihat perubahan kondisi Anda dari waktu ke waktu." />
      <HistoryView />
    </>
  );
}
