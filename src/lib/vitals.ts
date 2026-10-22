// Pengolahan data vital untuk grafik. Murni (tanpa I/O) supaya mudah dites.

import type { VitalKey } from "@/lib/demo-data";
import { formatClock, formatDayMonth } from "@/lib/format";
import type { TimeRange } from "@/lib/patientApi";

export type ReadingLike = { hr: number | null; spo2: number | null; rr: number | null; timestamp: string };
export type ChartPoint = { t: number; v: number };

const HOUR = 60 * 60 * 1000;

export const RANGE_MS: Record<TimeRange, number> = { "24h": 24 * HOUR, "7d": 7 * 24 * HOUR, "30d": 30 * 24 * HOUR };

/** Lebar bucket rata-rata per rentang — supaya 30 hari data tidak menjadi ribuan titik di SVG. */
export const BUCKET_MS: Record<TimeRange, number> = { "24h": 0.25 * HOUR, "7d": 2 * HOUR, "30d": 6 * HOUR };

/** Jeda lebih dari ini (dalam jumlah bucket kosong berturut-turut) digambar sebagai putus. */
export const GAP_BUCKETS = 3;

/** Rata-ratakan bacaan per bucket waktu; nilai null dilewati, bucket tanpa data tidak dibuat. */
export function bucketSeries(
  readings: { timestamp: number; value: number | null }[],
  bucketMs: number,
): ChartPoint[] {
  const buckets = new Map<number, { sum: number; count: number; tSum: number }>();
  for (const r of readings) {
    if (r.value === null || !Number.isFinite(r.value) || !Number.isFinite(r.timestamp)) continue;
    const key = Math.floor(r.timestamp / bucketMs);
    const bucket = buckets.get(key) ?? { sum: 0, count: 0, tSum: 0 };
    bucket.sum += r.value;
    bucket.count += 1;
    bucket.tSum += r.timestamp;
    buckets.set(key, bucket);
  }
  return [...buckets.entries()]
    .sort(([a], [b]) => a - b)
    .map(([, b]) => ({ t: b.tSum / b.count, v: b.sum / b.count }));
}

export function seriesFor(
  readings: ReadingLike[],
  vital: VitalKey,
  range: TimeRange,
  toMs: (iso: string) => number,
): ChartPoint[] {
  return bucketSeries(
    readings.map((r) => ({ timestamp: toMs(r.timestamp), value: r[vital] })),
    BUCKET_MS[range],
  );
}

/** Rentang minimum sumbu-Y per tanda vital supaya fluktuasi kecil tidak terlihat seperti lonjakan. */
const MIN_SPAN: Record<VitalKey, number> = { hr: 10, spo2: 4, rr: 6 };

export function yDomain(vital: VitalKey, values: number[]): [number, number] {
  if (!values.length) return [0, 1];
  const lo = Math.min(...values);
  const hi = Math.max(...values);
  const pad = Math.max((hi - lo) * 0.2, MIN_SPAN[vital] / 2);
  let min = Math.floor(lo - pad);
  let max = Math.ceil(hi + pad);
  if (vital === "spo2" && max > 100) {
    max = 100;
    min = Math.min(min, 100 - MIN_SPAN[vital]);
  }
  return [min, max];
}

/** 7 label sumbu-X yang tersebar rata di [start, end]. */
export function tickLabels(start: number, end: number, range: TimeRange): string[] {
  return Array.from({ length: 7 }, (_, i) => {
    const date = new Date(start + (i * (end - start)) / 6);
    return range === "24h" ? formatClock(date) : formatDayMonth(date);
  });
}
