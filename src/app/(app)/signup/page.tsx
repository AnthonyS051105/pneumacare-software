import type { Metadata } from "next";
import { SignupScreen } from "@/components/auth/SignupPage";

export const metadata: Metadata = { title: "Daftar: Pilih Peran" };

export default function SignupPage() {
  return <SignupScreen />;
}
