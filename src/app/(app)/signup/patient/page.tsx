import type { Metadata } from "next";
import { SignupScreen } from "@/components/auth/SignupPage";

export const metadata: Metadata = { title: "Daftar Pasien" };

export default function SignupPatientPage() {
  return <SignupScreen role="patient" />;
}
