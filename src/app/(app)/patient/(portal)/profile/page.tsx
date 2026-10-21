import type { Metadata } from "next";
import { ProfileView } from "@/components/portal/ProfileView";
import { Topbar } from "@/components/portal/Shell";

export const metadata: Metadata = { title: "Profil Pasien" };

export default function PatientProfilePage() {
  return (
    <>
      <Topbar role="patient" title="Profil saya" subtitle="Kelola informasi pribadi dan pengaturan akun." />
      <ProfileView role="patient" />
    </>
  );
}
