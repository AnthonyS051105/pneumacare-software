"use client";

import { useRouter } from "next/navigation";
import { useCallback, useEffect, useRef, useState } from "react";
import { ApiError } from "@/lib/api";

export const OFFLINE_MESSAGE = "Tidak dapat terhubung ke server. Pastikan backend sedang berjalan.";

export function errorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : OFFLINE_MESSAGE;
}

type Result<T> =
  | { key: string; status: "ready"; data: T; at: number }
  | { key: string; status: "error"; message: string; httpStatus?: number };

export type ApiState<T> =
  | { status: "loading"; reload: () => void }
  | { status: "error"; message: string; httpStatus?: number; reload: () => void }
  | { status: "ready"; data: T; at: number; reload: () => void; setData: (update: (data: T) => T) => void };

/**
 * Ambil data dari API untuk satu `key` (mis. id pasien + rentang). Ganti key = muat ulang.
 * `pollMs`: muat ulang berkala tanpa kembali ke status loading (FR-SW-050: data vital
 * terbarui tanpa reload manual). Gagal saat polling tidak menghapus data terakhir.
 * 401 (sesi berakhir) diarahkan ke /login.
 */
export function useApi<T>(fetcher: () => Promise<T>, key: string, options: { pollMs?: number } = {}): ApiState<T> {
  const router = useRouter();
  const [nonce, setNonce] = useState(0);
  const [result, setResult] = useState<Result<T> | null>(null);
  const fetcherRef = useRef(fetcher);
  useEffect(() => {
    fetcherRef.current = fetcher;
  });
  const fullKey = `${key}#${nonce}`;
  const { pollMs } = options;

  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout> | undefined;
    const run = (silent: boolean) => {
      fetcherRef.current()
        .then((data) => {
          if (!cancelled) setResult({ key: fullKey, status: "ready", data, at: Date.now() });
        })
        .catch((error) => {
          if (cancelled) return;
          if (error instanceof ApiError && error.status === 401) {
            router.replace("/login");
            return;
          }
          // Polling yang gagal sesaat tidak boleh mengganti data yang sudah tampil dengan layar error.
          if (!silent)
            setResult({
              key: fullKey,
              status: "error",
              message: errorMessage(error),
              httpStatus: error instanceof ApiError ? error.status : undefined,
            });
        })
        .finally(() => {
          if (!cancelled && pollMs) timer = setTimeout(() => run(true), pollMs);
        });
    };
    run(false);
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [fullKey, pollMs, router]);

  const reload = useCallback(() => setNonce((n) => n + 1), []);
  const setData = useCallback(
    (update: (data: T) => T) =>
      setResult((current) => (current && current.status === "ready" ? { ...current, data: update(current.data) } : current)),
    [],
  );

  if (!result || result.key !== fullKey) {
    // Saat reload manual, tetap tampilkan data lama (bukan berkedip ke "memuat").
    if (result && result.status === "ready" && result.key.startsWith(`${key}#`)) {
      return { status: "ready", data: result.data, at: result.at, reload, setData };
    }
    return { status: "loading", reload };
  }
  if (result.status === "error") return { status: "error", message: result.message, httpStatus: result.httpStatus, reload };
  return { status: "ready", data: result.data, at: result.at, reload, setData };
}
