import Link from "next/link";
import { LabMain } from "@/components/lab/LabHeader";
import { Brand, btn } from "@/components/ui/primitives";

export default function NotFound() {
  return (
    <LabMain>
      <Brand />
      <h1 className="mt-6">Halaman tidak ditemukan</h1>
      <p className="text-muted mt-2">Alamat yang Anda buka tidak tersedia.</p>
      <div className="flex flex-wrap gap-3 mt-6">
        <Link href="/" className={btn({ variant: "primary" })}>
          Kembali ke beranda
        </Link>
      </div>
    </LabMain>
  );
}
