import type { Metadata } from "next";
import { ProfileView } from "@/components/portal/ProfileView";
import { Topbar } from "@/components/portal/Shell";

export const metadata: Metadata = { title: "Profil Tenaga Medis" };

export default function ClinicianProfilePage() {
  return (
    <>
      <Topbar role="clinician" title="Profil saya" subtitle="Kelola informasi profesional dan pengaturan akun." />
      <ProfileView role="clinician" />
    </>
  );
}
