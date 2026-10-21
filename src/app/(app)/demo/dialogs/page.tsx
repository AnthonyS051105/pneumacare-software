import type { Metadata } from "next";
import { formGrid } from "@/components/portal/layout";
import { ModalButton, ToastButton } from "@/components/providers/Feedback";
import { grid2, LabHeader, LabMain } from "@/components/lab/LabHeader";
import { Field } from "@/components/ui/Field";
import { Icon, KeyRound, LinkIcon, UserPlus } from "@/components/ui/Icon";
import { btn, card, cardPad, cn, Notice } from "@/components/ui/primitives";

export const metadata: Metadata = { title: "Modal & Validasi" };

// .gallery>.grid>.card di referensi: kolom flex (tombol melebar penuh, jarak 5px).
const cardCls = cn(card, cardPad, "flex flex-col gap-[5px]");

export default function DialogsPage() {
  return (
    <LabMain>
      <LabHeader title="Modal & Validasi" description="Lembar pelengkap 1, Komponen interaktif dan contoh umpan balik." />
      <div className={grid2}>
        <div className={cardCls}>
          <h3>Pairing Perangkat</h3>
          <p className="text-muted mt-6">Masukkan PC-4821 untuk berhasil; kode lain menampilkan validasi.</p>
          <ModalButton kind="pair" className={cn(btn({ variant: "primary" }), "mt-6")}>
            <Icon icon={LinkIcon} />
            Hubungkan perangkat
          </ModalButton>
          <div className="mt-6">
            <Notice type="error">Kode pairing tidak ditemukan. Periksa kembali kode perangkat.</Notice>
          </div>
        </div>
        <div className={cardCls}>
          <h3>Tambah Pasien</h3>
          <p className="text-muted mt-6">Hubungkan pasien dengan email atau kode undangan demo.</p>
          <ModalButton kind="add" className={cn(btn({ variant: "primary" }), "mt-6")}>
            <Icon icon={UserPlus} />
            Tambah pasien
          </ModalButton>
          <div className="mt-6">
            <Notice>Pasien berhasil ditambahkan ke daftar pemantauan.</Notice>
          </div>
        </div>
        <div className={cardCls}>
          <h3>Lupa Password</h3>
          <p className="text-muted mt-6">Demo menampilkan alur bantuan tanpa mengirim email.</p>
          <ModalButton kind="forgot" className={cn(btn(), "mt-6")}>
            <Icon icon={KeyRound} />
            Bantuan akun
          </ModalButton>
        </div>
        <div className={cardCls}>
          <h3>Toast & Konfirmasi</h3>
          <p className="text-muted mt-6">Umpan balik singkat setelah menyimpan atau ketika terjadi kesalahan.</p>
          <div className="flex flex-wrap items-center gap-3 mt-6">
            <ToastButton text="Perubahan berhasil disimpan." className={btn({ variant: "primary" })}>
              Toast berhasil
            </ToastButton>
            <ToastButton text="Perubahan gagal disimpan. Silakan coba lagi." error className={btn()}>
              Toast kesalahan
            </ToastButton>
            <ModalButton kind="logout" className={btn({ variant: "danger" })}>
              Konfirmasi keluar
            </ModalButton>
          </div>
        </div>
        <div className={cn(cardCls, "col-span-full")}>
          <h3>Contoh Validasi Formulir</h3>
          <div className={cn(formGrid, "mt-6")}>
            <Field
              name="sample-email"
              label="Email"
              type="email"
              defaultValue="budi@"
              hint="Gunakan alamat email yang valid"
              required
              error="Format email tidak valid."
            />
            <Field
              name="sample-confirm"
              label="Konfirmasi password"
              type="password"
              hint="Harus sama dengan password baru"
              required
              error="Konfirmasi password tidak sesuai."
            />
          </div>
          <div className="mt-6">
            <Notice type="error">Periksa kembali kolom yang ditandai sebelum melanjutkan.</Notice>
          </div>
        </div>
      </div>
      <p className="text-[10px] leading-[1.6] text-muted mt-7 pt-[18px] border-t border-line">
        Validasi ditampilkan melalui pesan teks dan warna. Dialog dapat ditutup dengan Escape.
      </p>
    </LabMain>
  );
}
