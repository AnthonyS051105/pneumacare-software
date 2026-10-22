"use client";

import { useSyncExternalStore } from "react";
import type { Patient, VitalKey } from "@/lib/demo-data";

// State demo yang dipersist ke localStorage (kunci sama dengan referensi: "pneuma-demo"),
// plus state UI sementara (filter, tab) yang bertahan selama sesi seperti variabel
// modul di app.js. Memakai useSyncExternalStore: server & hydration selalu memakai
// nilai default, lalu React sinkron ke localStorage tanpa hydration mismatch.

export type DemoData = {
  patient: { name: string; email: string; dob: string };
  clinician: { name: string; email: string; specialty: string; institution: string; str: string };
  read: string[];
  ack: string[];
  extra: Patient[];
  thresholds?: Record<string, Record<string, string>>;
};

export const demoDefaults: DemoData = {
  patient: { name: "Budi Santoso", email: "budi@example.com", dob: "1962-05-14" },
  clinician: { name: "dr. Nadia Putri", email: "nadia@example.com", specialty: "Dokter Spesialis Paru", institution: "RS Akademik UGM", str: "" },
  read: [],
  ack: [],
  extra: [],
};

const STORAGE_KEY = "pneuma-demo";

function createStore<T>(initial: () => T, persist?: (value: T) => void) {
  let value: T | null = null;
  const listeners = new Set<() => void>();
  const get = () => (value ??= initial());
  return {
    get,
    set(update: (current: T) => T) {
      value = update(get());
      persist?.(value);
      listeners.forEach((listener) => listener());
    },
    reload() {
      value = initial();
      listeners.forEach((listener) => listener());
    },
    subscribe(listener: () => void) {
      listeners.add(listener);
      return () => listeners.delete(listener);
    },
  };
}

const demoStore = createStore<DemoData>(
  () => {
    try {
      return { ...demoDefaults, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}") };
    } catch {
      return demoDefaults;
    }
  },
  (value) => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(value));
    } catch {}
  },
);

if (typeof window !== "undefined") {
  window.addEventListener("storage", (event) => {
    if (event.key === STORAGE_KEY) demoStore.reload();
  });
}

/** Pilih potongan state yang stabil (mis. `d => d.patient`), bukan objek baru. */
export function useDemo<T>(selector: (data: DemoData) => T): T {
  return useSyncExternalStore(
    demoStore.subscribe,
    () => selector(demoStore.get()),
    () => selector(demoDefaults),
  );
}

export const updateDemo = demoStore.set;

export type UiState = {
  chosenRole: "pasien" | "clinician";
  historyRange: "24h" | "7 hari" | "30 hari";
  metricTab: VitalKey;
  patientFilter: string;
  searchText: string;
  alertFilter: "all" | "unread";
  alertLevel: string;
  alertPatient: string;
  alertAck: string;
  alertDate: string;
  sortOrder: "priority" | "name";
};

const uiDefaults: UiState = {
  chosenRole: "pasien",
  historyRange: "24h",
  metricTab: "hr",
  patientFilter: "all",
  searchText: "",
  alertFilter: "all",
  alertLevel: "all",
  alertPatient: "all",
  alertAck: "all",
  alertDate: "all",
  sortOrder: "priority",
};

const uiStore = createStore<UiState>(() => uiDefaults);

export function useUi<K extends keyof UiState>(key: K): [UiState[K], (value: UiState[K]) => void] {
  const value = useSyncExternalStore(
    uiStore.subscribe,
    () => uiStore.get()[key],
    () => uiDefaults[key],
  );
  return [value, (next) => uiStore.set((state) => ({ ...state, [key]: next }))];
}
