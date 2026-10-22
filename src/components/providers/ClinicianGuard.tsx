"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState, type ReactNode } from "react";
import { SessionUserProvider } from "@/components/providers/SessionUser";
import { ApiError, apiFetch } from "@/lib/api";
import { CLINICIAN_PROFILE_EVENT } from "@/lib/clinicianPatients";

type ClinicianProfile = { full_name: string };

/**
 * Penjaga sesi portal tenaga medis. Data portal ini masih fixture demo; yang disambungkan
 * baru sesi + nama. Belum login -> /login; login sebagai pasien -> portal pasien.
 */
export function ClinicianGuard({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [state, setState] = useState<{ status: "loading" } | { status: "error"; message: string } | { status: "ready"; name: string }>({
    status: "loading",
  });

  const [nonce, setNonce] = useState(0);

  useEffect(() => {
    // Nama di sidebar dimuat ulang setelah profil disimpan (lihat ProfileView).
    const onProfile = () => setNonce((n) => n + 1);
    window.addEventListener(CLINICIAN_PROFILE_EVENT, onProfile);
    return () => window.removeEventListener(CLINICIAN_PROFILE_EVENT, onProfile);
  }, []);

  useEffect(() => {
    let cancelled = false;
    apiFetch<ClinicianProfile>("/clinician/profile")
      .then((profile) => !cancelled && setState({ status: "ready", name: profile.full_name }))
      .catch((error) => {
        if (cancelled) return;
        if (error instanceof ApiError && error.status === 401) return router.replace("/login");
        if (error instanceof ApiError && error.status === 403) return router.replace("/patient/home");
        setState({
          status: "error",
          message:
            error instanceof ApiError
              ? error.message
              : "Tidak dapat terhubung ke server. Pastikan backend sedang berjalan.",
        });
      });
    return () => {
      cancelled = true;
    };
  }, [router, nonce]);

  if (state.status === "loading") {
    return (
      <p role="status" className="min-h-screen grid place-items-center text-muted text-[13px]">
        Memuat…
      </p>
    );
  }
  if (state.status === "error") {
    return (
      <div role="alert" className="min-h-screen grid place-items-center px-6 text-center">
        <div>
          <h1 className="text-[21px]">Data belum dapat dimuat</h1>
          <p className="text-muted mt-2">{state.message}</p>
          <button
            type="button"
            className="mt-6 inline-flex items-center min-h-11 px-5 rounded-[8px] border border-line bg-white font-semibold"
            onClick={() => window.location.reload()}
          >
            Coba lagi
          </button>
        </div>
      </div>
    );
  }
  return <SessionUserProvider value={state.name}>{children}</SessionUserProvider>;
}
