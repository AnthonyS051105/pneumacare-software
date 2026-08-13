"""Rolling window — hitung frekuensi kemunculan wheeze/crackle dari time series
hasil klasifikasi per segmen (FR-SW-020, FR-SW-021, SDD_SOFTWARE.md §6).

Fungsi murni, tanpa I/O — input: list event klasifikasi terurut waktu, output:
list titik (timestamp, frekuensi) yang jadi input untuk moving average + regresi
linear di trend_detector.py.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ClassificationEvent:
    """Satu hasil klasifikasi segmen (subset field dari readings_severity)."""

    timestamp: datetime
    wheeze_present: bool
    crackle_present: bool


@dataclass(frozen=True)
class FrequencyPoint:
    """Frekuensi kemunculan wheeze/crackle dalam satu rolling window (per menit)."""

    window_end: datetime
    wheeze_frequency: float
    crackle_frequency: float


def compute_rolling_frequency(
    events: list[ClassificationEvent],
    window_size: int,
) -> list[FrequencyPoint]:
    """Hitung frekuensi wheeze/crackle per rolling window berukuran `window_size` segmen.

    Window bergeser satu segmen setiap langkah (sliding window, bukan tumbling) supaya
    trend_detector punya cukup titik data untuk regresi meski jumlah segmen historis
    sedikit. Frekuensi dinyatakan sebagai "kemunculan per menit" berdasarkan rentang
    waktu aktual window (window_end - window_start dari `events`), bukan asumsi durasi
    segmen tetap — supaya benar meski ada gap koneksi/downtime device.

    `events` HARUS sudah terurut menaik berdasarkan timestamp (tanggung jawab caller,
    lihat FR-SW-020: disimpan sebagai time series per device+channel).
    """
    if window_size < 1:
        raise ValueError("window_size harus >= 1")

    points: list[FrequencyPoint] = []
    for end_idx in range(window_size - 1, len(events)):
        window = events[end_idx - window_size + 1 : end_idx + 1]
        window_start_ts = window[0].timestamp
        window_end_ts = window[-1].timestamp

        duration_minutes = (window_end_ts - window_start_ts).total_seconds() / 60
        if duration_minutes <= 0:
            # Segmen dengan timestamp identik/terbalik (mis. data uji sintetis) — hindari
            # divide-by-zero, anggap durasi minimal 1 segmen (~konservatif, bukan estimasi presisi).
            duration_minutes = 1 / 60

        wheeze_count = sum(1 for e in window if e.wheeze_present)
        crackle_count = sum(1 for e in window if e.crackle_present)

        points.append(
            FrequencyPoint(
                window_end=window_end_ts,
                wheeze_frequency=wheeze_count / duration_minutes,
                crackle_frequency=crackle_count / duration_minutes,
            )
        )

    return points
