// Helper format waktu untuk data dari backend. Murni (tanpa I/O) supaya mudah dites.
//
// Backend menyimpan datetime sebagai UTC, tetapi SQLite mengembalikannya tanpa penanda zona
// ("2026-10-22T05:16:00"). `new Date()` akan menafsirkan string seperti itu sebagai waktu LOKAL
// browser — salah beberapa jam. Karena itu zona dipaksa UTC bila tidak ada penandanya.

const TIME_ZONE = "Asia/Jakarta";

export function parseApiDate(value: string): Date {
  const hasZone = /(Z|[+-]\d{2}:?\d{2})$/i.test(value);
  return new Date(hasZone ? value : `${value}Z`);
}

function part(date: Date, options: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat("id-ID", { timeZone: TIME_ZONE, ...options }).format(date);
}

/** "09.30" (WIB). */
export function formatClock(date: Date): string {
  return part(date, { hour: "2-digit", minute: "2-digit", hourCycle: "h23" });
}

/** "09.30 WIB". */
export function formatClockWib(date: Date): string {
  return `${formatClock(date)} WIB`;
}

/** "22 Okt" (WIB). */
export function formatDayMonth(date: Date): string {
  return part(date, { day: "numeric", month: "short" });
}

/** "22 Oktober 2026" (WIB). */
export function formatFullDate(date: Date): string {
  return part(date, { day: "numeric", month: "long", year: "numeric" });
}

/** Kunci hari "YYYY-MM-DD" menurut WIB, untuk membandingkan "hari yang sama". */
export function dayKey(date: Date): string {
  return new Intl.DateTimeFormat("en-CA", { timeZone: TIME_ZONE }).format(date);
}

/** "Hari ini, 09.28 WIB" / "Kemarin, 16.42 WIB" / "10 Okt 2026, 09.28 WIB". */
export function formatEventTime(iso: string, now: Date = new Date()): string {
  const date = parseApiDate(iso);
  const clock = formatClockWib(date);
  const today = dayKey(now);
  const yesterday = dayKey(new Date(now.getTime() - 24 * 60 * 60 * 1000));
  const key = dayKey(date);
  if (key === today) return `Hari ini, ${clock}`;
  if (key === yesterday) return `Kemarin, ${clock}`;
  return `${part(date, { day: "numeric", month: "short", year: "numeric" })}, ${clock}`;
}

/** Sapaan sesuai jam WIB. */
export function greetingFor(now: Date = new Date()): string {
  const hour = Number(part(now, { hour: "numeric", hourCycle: "h23" }));
  if (hour >= 4 && hour < 11) return "Selamat pagi";
  if (hour >= 11 && hour < 15) return "Selamat siang";
  if (hour >= 15 && hour < 18) return "Selamat sore";
  return "Selamat malam";
}
