import { apiFetch } from "@/lib/api";

// Mengikuti backend/auth/auth_routes.py (SDD_SOFTWARE.md §4.1). Role di backend
// memakai "pasien" | "clinician" (bukan "patient" seperti di route frontend).
export type BackendRole = "pasien" | "clinician";

export type AuthUser = {
  id: string;
  email: string;
  role: BackendRole;
  full_name: string;
};

export type SignupPayload = {
  role: BackendRole;
  email: string;
  password: string;
  full_name: string;
  pairing_code?: string;
  specialization?: string;
  institution?: string;
  str_sip_number?: string;
};

export function login(email: string, password: string): Promise<AuthUser> {
  return apiFetch<AuthUser>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
}

export function signup(payload: SignupPayload): Promise<AuthUser> {
  return apiFetch<AuthUser>("/auth/signup", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function logout(): Promise<{ status: "ok" }> {
  return apiFetch("/auth/logout", { method: "POST" });
}

export function homePathFor(role: BackendRole): string {
  return role === "clinician" ? "/clinician/patients" : "/patient/home";
}
