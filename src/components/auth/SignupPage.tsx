import Link from "next/link";
import { AuthLayout, authMuted, authTitle, Stepper } from "@/components/auth/AuthLayout";
import { SignupForm } from "@/components/auth/SignupForm";
import { SignupRole } from "@/components/auth/SignupRole";
import { ArrowLeft, Icon } from "@/components/ui/Icon";
import { cn } from "@/components/ui/primitives";

const backLink = cn("flex items-center gap-3", authMuted);

/** Langkah 1 (pilih peran) atau langkah 2 (form) registrasi. */
export function SignupScreen({ role }: { role?: "patient" | "clinician" }) {
  if (!role)
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
        <Link href="/" className={backLink}>
          <Icon icon={ArrowLeft} /> Kembali ke beranda
        </Link>
        <h1 className={authTitle}>Mulai perjalanan Anda</h1>
        <p className={authMuted}>Pilih peran untuk membuat akun PNEUMACARE.</p>
        <Stepper step={1} />
        <SignupRole />
      </AuthLayout>
    );
  return (
    <AuthLayout
      heading={
        <>
          Pemantauan yang
          <br />
          mendampingi Anda.
        </>
      }
    >
      <Link href="/signup" className={backLink}>
        <Icon icon={ArrowLeft} /> Kembali pilih peran
      </Link>
      <h1 className={authTitle}>Daftar sebagai {role === "clinician" ? "Tenaga Medis" : "Pasien"}</h1>
      <p className={authMuted}>Lengkapi data Anda untuk mulai terhubung.</p>
      <Stepper step={2} />
      <SignupForm role={role} />
    </AuthLayout>
  );
}
