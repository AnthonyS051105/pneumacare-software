"use client";

import { useRouter } from "next/navigation";
import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from "react";
import { SessionUserProvider } from "@/components/providers/SessionUser";
import { ApiError } from "@/lib/api";
import {
  fetchPatientAlerts,
  fetchPatientProfile,
  fetchPatientSummary,
  type PatientAlert,
  type PatientProfile,
  type PatientSummary,
} from "@/lib/patientApi";

/** Event yang dikirim modal "Hubungkan ulang" (di luar provider ini) setelah perangkat berganti. */
export const PATIENT_RELOAD_EVENT = "pneuma:patient-reload";

/** FR-SW-050: data diperbarui berkala tanpa reload manual. Parameter UI, bukan nilai klinis. */
const REFRESH_MS = 15_000;

type PatientData = {
  summary: PatientSummary;
  profile: PatientProfile;
  alerts: PatientAlert[];
  reload: () => Promise<void>;
};

const Context = createContext<PatientData | null>(null);

export function usePatientData(): PatientData {
  const ctx = useContext(Context);
  if (!ctx) throw new Error("usePatientData harus dipakai di dalam <PatientDataProvider>");
  return ctx;
}

type State =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: Omit<PatientData, "reload"> };

/**
 * Penjaga sesi + sumber data portal pasien. Memuat ringkasan, profil, dan alert sekali;
 * halaman di dalamnya memakai `usePatientData()`. Belum login -> /login; login sebagai
 * tenaga medis -> portal tenaga medis (backend juga menolak dengan 401/403, ini hanya UX).
 */
export function PatientDataProvider({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [state, setState] = useState<State>({ status: "loading" });
  const latest = useRef(0);
  const mounted = useRef(false);

  const load = useCallback(async (silent = false) => {
    const run = ++latest.current;
    try {
      const [summary, profile, alerts] = await Promise.all([
        fetchPatientSummary(),
        fetchPatientProfile(),
        fetchPatientAlerts(),
      ]);
      if (mounted.current && run === latest.current) setState({ status: "ready", data: { summary, profile, alerts } });
    } catch (error) {
      if (!mounted.current || run !== latest.current) return;
      if (error instanceof ApiError && error.status === 401) return router.replace("/login");
      if (error instanceof ApiError && error.status === 403) return router.replace("/clinician/patients");
      // Pembaruan berkala yang gagal sesaat tidak mengganti tampilan dengan layar error.
      if (silent) return;
      setState({
        status: "error",
        message:
          error instanceof ApiError
            ? error.message
            : "Tidak dapat terhubung ke server. Pastikan backend sedang berjalan.",
      });
    }
  }, [router]);

  useEffect(() => {
    mounted.current = true;
    // Memuat dari API saat mount adalah sinkronisasi dengan sistem eksternal; setState hanya
    // terjadi setelah `await`, bukan sinkron di dalam efek.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
    const onReload = () => void load();
    window.addEventListener(PATIENT_RELOAD_EVENT, onReload);
    const timer = setInterval(() => void load(true), REFRESH_MS);
    return () => {
      mounted.current = false;
      clearInterval(timer);
      window.removeEventListener(PATIENT_RELOAD_EVENT, onReload);
    };
  }, [load]);

  if (state.status === "loading") {
    return (
      <p role="status" className="min-h-screen grid place-items-center text-muted text-[13px]">
        Memuat data Anda…
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
            onClick={() => {
              setState({ status: "loading" });
              void load();
            }}
          >
            Coba lagi
          </button>
        </div>
      </div>
    );
  }

  const { data } = state;
  return (
    <Context.Provider value={{ ...data, reload: () => load() }}>
      <SessionUserProvider value={data.profile.full_name}>{children}</SessionUserProvider>
    </Context.Provider>
  );
}
