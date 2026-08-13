"""Band-pass filter untuk memisahkan komponen kardiak dari artefak napas pada
sinyal PPG (FR-SW-030, SDD_SOFTWARE.md §7).

Fungsi murni (numpy in, numpy out) — Butterworth IIR via scipy.signal, zero-phase
(filtfilt) supaya tidak menggeser posisi puncak yang dipakai hr_estimator.py.
"""

import numpy as np
from scipy.signal import butter, filtfilt


def bandpass_filter(
    signal: np.ndarray,
    sample_rate_hz: float,
    low_hz: float,
    high_hz: float,
    order: int = 4,
) -> np.ndarray:
    """Terapkan Butterworth band-pass filter zero-phase pada `signal`.

    Raises ValueError bila `signal` terlalu pendek untuk order filter yang diminta
    (filtfilt butuh panjang sinyal > 3 * (order * 2 + 1) kira-kira) — lebih baik
    gagal jelas daripada mengembalikan hasil filter yang tidak stabil/tidak bermakna.
    """
    signal = np.asarray(signal, dtype=float)

    nyquist = sample_rate_hz / 2
    if not (0 < low_hz < high_hz < nyquist):
        raise ValueError(
            f"cutoff tidak valid untuk sample_rate_hz={sample_rate_hz}: "
            f"low={low_hz}, high={high_hz}, nyquist={nyquist}"
        )

    min_length = 3 * (2 * order + 1)
    if len(signal) <= min_length:
        raise ValueError(
            f"sinyal terlalu pendek ({len(signal)} sample) untuk filter order={order}, "
            f"minimal {min_length + 1} sample"
        )

    b, a = butter(order, [low_hz, high_hz], btype="bandpass", fs=sample_rate_hz)
    return filtfilt(b, a, signal)


def cardiac_bandpass_filter(
    signal: np.ndarray,
    sample_rate_hz: float,
    low_hz: float,
    high_hz: float,
    order: int = 4,
) -> np.ndarray:
    """Alias eksplisit untuk komponen kardiak — dipakai hr_estimator.py.

    Parameter cutoff/order diteruskan dari config.py (CARDIAC_BANDPASS_LOW_HZ dkk.),
    TIDAK di-hardcode di sini, supaya nilai placeholder tetap mudah di-grep/diubah.
    """
    return bandpass_filter(signal, sample_rate_hz, low_hz, high_hz, order)
