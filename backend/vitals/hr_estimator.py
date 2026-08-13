"""Estimasi HR dari sinyal PPG band-pass kardiak via deteksi puncak
(FR-SW-031, SDD_SOFTWARE.md §7).

Fungsi murni — menerima sinyal yang SUDAH difilter oleh bandpass_filter.py,
mendeteksi puncak, menghitung interval antar-puncak, HR = 60/interval rata-rata.
"""

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks


@dataclass(frozen=True)
class HrEstimate:
    hr_bpm: float | None
    confidence: str  # "good" | "poor" — SDD_SOFTWARE.md §8: jangan tampilkan angka palsu percaya diri
    peak_count: int


def estimate_hr(
    cardiac_signal: np.ndarray,
    sample_rate_hz: float,
    plausible_min_bpm: float,
    plausible_max_bpm: float,
) -> HrEstimate:
    """Estimasi HR dari sinyal PPG band-pass kardiak.

    `confidence="poor"` (bukan exception) dikembalikan bila:
    - puncak terdeteksi < 2 (tidak cukup untuk interval), atau
    - HR hasil hitung di luar rentang plausible (mis. deteksi puncak keliru akibat
      SNR rendah — SDD_SOFTWARE.md §8, "estimator HR/SpO2 sebaiknya punya mekanisme
      deteksi sinyal buruk").

    Ini best-effort: tetap mengembalikan HrEstimate (bukan raise), supaya caller
    (mis. endpoint API/dashboard) bisa menampilkan "sinyal tidak stabil" tanpa
    perlu try/except di setiap tempat pemanggilan.
    """
    cardiac_signal = np.asarray(cardiac_signal, dtype=float)

    # Jarak minimum antar-puncak berdasarkan plausible_max_bpm — mencegah mendeteksi
    # dua puncak dalam satu detak jantung yang sama akibat noise.
    min_distance_samples = int(sample_rate_hz * 60 / plausible_max_bpm)
    peaks, _ = find_peaks(cardiac_signal, distance=max(min_distance_samples, 1))

    if len(peaks) < 2:
        return HrEstimate(hr_bpm=None, confidence="poor", peak_count=len(peaks))

    intervals_samples = np.diff(peaks)
    mean_interval_seconds = float(np.mean(intervals_samples)) / sample_rate_hz

    if mean_interval_seconds <= 0:
        return HrEstimate(hr_bpm=None, confidence="poor", peak_count=len(peaks))

    hr_bpm = 60 / mean_interval_seconds

    if not (plausible_min_bpm <= hr_bpm <= plausible_max_bpm):
        return HrEstimate(hr_bpm=round(hr_bpm, 1), confidence="poor", peak_count=len(peaks))

    return HrEstimate(hr_bpm=round(hr_bpm, 1), confidence="good", peak_count=len(peaks))
