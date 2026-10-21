import type { Metadata } from "next";
import { SignupScreen } from "@/components/auth/SignupPage";

export const metadata: Metadata = { title: "Daftar Tenaga Medis" };

export default function SignupClinicianPage() {
  return <SignupScreen role="clinician" />;
}
