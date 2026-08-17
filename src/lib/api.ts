// Client kecil untuk memanggil REST API backend Flask (SDD_SOFTWARE.md §4).
// Semua endpoint /patient/me/* butuh sesi login (Fase 4, session cookie via flask-login) —
// fetch di sini SELALU pakai credentials:"include" supaya cookie sesi ikut terkirim.

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:5000/api/v1";

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message =
      (body && typeof body === "object" && "error" in body && String(body.error)) ||
      `Permintaan gagal (${response.status})`;
    throw new ApiError(response.status, message);
  }

  return response.json() as Promise<T>;
}
