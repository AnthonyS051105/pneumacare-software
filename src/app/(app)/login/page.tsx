import type { Metadata } from "next";
import Link from "next/link";
import { AuthLayout, authMuted, authTitle } from "@/components/auth/AuthLayout";
import { LoginForm } from "@/components/auth/LoginForm";
import { ArrowLeft, Icon } from "@/components/ui/Icon";

export const metadata: Metadata = { title: "Login" };

export default function LoginPage() {
  return (
    <AuthLayout
      heading={
        <>
          Tetap terhubung,
          <br />
          dari rumah.
        </>
      }
    >
      <Link href="/" className="flex items-center gap-3 text-[12px]">
        <Icon icon={ArrowLeft} /> Kembali ke beranda
      </Link>
      <h1 className={authTitle}>Selamat datang kembali</h1>
      <p className={authMuted}>Masuk untuk melanjutkan pemantauan Anda.</p>
      <LoginForm />
    </AuthLayout>
  );
}
