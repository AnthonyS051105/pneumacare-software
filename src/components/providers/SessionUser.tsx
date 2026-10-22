"use client";

import { createContext, useContext } from "react";

// Nama pengguna yang sedang login (dari API). Sidebar/Topbar membacanya bila ada;
// bila tidak (lembar demo di luar portal) mereka jatuh ke state demo.
const SessionUserContext = createContext<string | null>(null);

export const SessionUserProvider = SessionUserContext.Provider;

export function useSessionName(): string | null {
  return useContext(SessionUserContext);
}
