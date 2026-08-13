"""Moving average + regresi linear terhadap frekuensi wheeze/crackle, untuk memicu
trend_event bila slope melewati ambang signifikansi (FR-SW-022, FR-SW-023,
SDD_SOFTWARE.md §6).

Fungsi murni, tanpa I/O — input: list FrequencyPoint dari rolling_window.py,
output: TrendResult (slope + status signifikan). Dipisah dari database/network
supaya bisa ditest dengan data simulasi (FR-SW-024).
"""

from dataclasses import dataclass
from datetime import datetime

from backend.trend_analysis.rolling_window import FrequencyPoint


@dataclass(frozen=True)
class TrendResult:
    window_start: datetime
    window_end: datetime
    slope: float
    significant: bool


def _moving_average(values: list[float], window: int) -> list[float]:
    """Simple moving average, window bergeser satu titik per langkah.

    Titik-titik pertama (kurang dari `window` data tersedia) memakai rata-rata
    dari data yang ada saja, supaya deret hasil punya panjang sama dengan input
    (dibutuhkan agar tiap titik smoothed tetap punya timestamp berpasangan untuk regresi).
    """
    if window < 1:
        raise ValueError("window harus >= 1")

    smoothed: list[float] = []
    for i in range(len(values)):
        start = max(0, i - window + 1)
        chunk = values[start : i + 1]
        smoothed.append(sum(chunk) / len(chunk))
    return smoothed


def _linear_regression_slope(x: list[float], y: list[float]) -> float:
    """Slope regresi linear least-squares sederhana (tanpa dependency scipy/numpy)."""
    n = len(x)
    if n < 2:
        return 0.0

    mean_x = sum(x) / n
    mean_y = sum(y) / n

    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denominator = sum((xi - mean_x) ** 2 for xi in x)

    if denominator == 0:
        return 0.0

    return numerator / denominator


def detect_trend(
    points: list[FrequencyPoint],
    moving_average_window: int,
    significance_threshold: float,
    metric: str = "wheeze_frequency",
) -> TrendResult | None:
    """Hitung slope tren dari rolling-window frequency points untuk satu metrik.

    Mengembalikan None bila titik data kurang dari 2 (regresi tidak bermakna).
    `significant=true` hanya bila |slope| melewati ambang DAN arah naik (slope > 0),
    sesuai SDD_SOFTWARE.md §6 — tren turun tidak memicu alert (secara klinis tren
    membaik bukan kondisi yang perlu diwaspadai).
    """
    if len(points) < 2:
        return None

    if metric not in ("wheeze_frequency", "crackle_frequency"):
        raise ValueError(f"metric tidak dikenal: {metric}")

    raw_values = [getattr(p, metric) for p in points]
    smoothed_values = _moving_average(raw_values, moving_average_window)

    # Sumbu-x regresi: menit sejak titik pertama, supaya slope punya satuan
    # "perubahan frekuensi per menit" — konsisten dengan satuan frekuensi itu sendiri.
    t0 = points[0].window_end
    x = [(p.window_end - t0).total_seconds() / 60 for p in points]

    slope = _linear_regression_slope(x, smoothed_values)
    significant = slope > significance_threshold

    return TrendResult(
        window_start=points[0].window_end,
        window_end=points[-1].window_end,
        slope=slope,
        significant=significant,
    )
