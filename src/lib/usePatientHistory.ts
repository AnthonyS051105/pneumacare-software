"use client";

import { useCallback, useEffect, useState } from "react";
import { ApiError } from "@/lib/api";
import { fetchPatientHistory, type PatientHistory, type TimeRange } from "@/lib/patientApi";

type Result =
  | { key: string; status: "ready"; data: PatientHistory; asOf: number }
  | { key: string; status: "error"; message: string };

export type HistoryState =
  | { status: "loading" }
  | { status: "error"; message: string; retry: () => void }
  | { status: "ready"; data: PatientHistory; asOf: number };

/** Ambil riwayat vital untuk satu rentang; ganti rentang / retry otomatis memuat ulang. */
export function usePatientHistory(range: TimeRange): HistoryState {
  const [nonce, setNonce] = useState(0);
  const [result, setResult] = useState<Result | null>(null);
  const key = `${range}:${nonce}`;

  useEffect(() => {
    let cancelled = false;
    fetchPatientHistory(range)
      .then((data) => !cancelled && setResult({ key, status: "ready", data, asOf: Date.now() }))
      .catch((error) => {
        if (cancelled) return;
        setResult({
          key,
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
  }, [range, key]);

  const retry = useCallback(() => setNonce((n) => n + 1), []);

  // Hasil milik rentang/percobaan sebelumnya tidak boleh tampil sebagai data rentang ini.
  if (!result || result.key !== key) return { status: "loading" };
  if (result.status === "error") return { status: "error", message: result.message, retry };
  return { status: "ready", data: result.data, asOf: result.asOf };
}
