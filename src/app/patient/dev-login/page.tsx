"use client";

// TEMPORARY_DEV_AUTH — HALAMAN INI BUKAN ALUR LOGIN SUNGGUHAN.
//
// Halaman Login asli (`/login`, UIUX_FLOW.md §2.3) belum dikerjakan di sesi ini
// (di luar scope: "JANGAN buat halaman Login/Sign Up/Landing"). Endpoint
// `/patient/me/*` butuh sesi login (flask-login session cookie, Fase 4) supaya
// bisa dites, jadi halaman kecil ini dibuat KHUSUS untuk development: submit
// email+password ke POST /api/v1/auth/login, cookie sesi yang didapat otomatis
// tersimpan browser (fetch pakai credentials:"include") dan langsung bisa dipakai
// mengakses /patient/home, /patient/history, /patient/alerts.
//
// WAJIB DIHAPUS begitu halaman Login asli (`/login`) selesai dikerjakan — jangan
// sampai halaman ini lolos ke build/demo final. TIDAK ditautkan dari navigasi
// manapun (sidebar/topbar/bottomnav tidak punya link ke sini), tapi TETAP bisa
// diakses langsung via URL (/patient/dev-login) selama masih ada di codebase.
// (Nama folder awalnya diawali underscore `_dev-login`, tapi itu ternyata membuat
// Next.js App Router mengecualikannya sepenuhnya dari routing — private folder
// convention — sehingga halaman tidak bisa diakses sama sekali. Diganti ke
// `dev-login` tanpa underscore supaya tetap bisa dibuka manual saat development.)

import { useState } from "react";
import { apiFetch } from "@/lib/api";

export default function DevLoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setStatus("loading");
    setMessage("");

    try {
      const user = await apiFetch<{ email: string; role: string }>("/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      setStatus("success");
      setMessage(`Login berhasil sebagai ${user.email} (role: ${user.role}). Cookie sesi tersimpan.`);
    } catch (error) {
      setStatus("error");
      setMessage(error instanceof Error ? error.message : "Login gagal");
    }
  }

  return (
    <div className="mx-auto flex min-h-screen max-w-sm flex-col justify-center gap-4 p-6">
      <div className="rounded-lg border-2 border-dashed border-status-error/50 bg-status-error/5 p-3 text-sm text-status-error">
        ⚠️ TEMPORARY_DEV_AUTH — halaman development sementara, BUKAN halaman Login
        produk. Hapus setelah halaman Login asli selesai.
      </div>

      <h1 className="text-xl font-bold">Dev Login (Portal Pasien)</h1>

      <form onSubmit={handleSubmit} className="flex flex-col gap-3">
        <input
          type="email"
          placeholder="Email akun pasien"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="rounded border border-outline-variant/40 p-2"
          required
        />
        <input
          type="password"
          placeholder="Password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="rounded border border-outline-variant/40 p-2"
          required
        />
        <button
          type="submit"
          disabled={status === "loading"}
          className="rounded bg-primary p-2 font-semibold text-on-primary disabled:opacity-50"
        >
          {status === "loading" ? "Memproses..." : "Login (dev)"}
        </button>
      </form>

      {message && (
        <p className={status === "error" ? "text-status-error" : "text-status-success"}>
          {message}
        </p>
      )}

      {status === "success" && (
        <div className="flex flex-col gap-2 text-sm">
          <a href="/patient/home" className="text-primary underline">
            → Buka Patient Home
          </a>
          <a href="/patient/history" className="text-primary underline">
            → Buka Patient Vital History
          </a>
          <a href="/patient/alerts" className="text-primary underline">
            → Buka Patient Alerts
          </a>
        </div>
      )}
    </div>
  );
}
