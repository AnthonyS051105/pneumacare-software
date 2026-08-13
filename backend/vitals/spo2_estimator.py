"""Estimasi SpO2 dari rasio absorpsi cahaya merah/inframerah sensor MAX30102
(FR-SW-032, SDD_SOFTWARE.md §7).

🚨🚨 PERINGATAN AKURASI — BACA SEBELUM PAKAI DI LUAR DEVELOPMENT/DEMO 🚨🚨
Sensor dikonfirmasi dual-wavelength (MAX30102, konfirmasi Tony 2026-08-13), jadi
perhitungan rasio-R di modul ini SECARA MATEMATIS valid. TAPI kurva kalibrasi yang
memetakan rasio-R ke persen SpO2 (lihat config.py SPO2_CALIBRATION_COEFF_A/B) adalah
rumus umum dari referensi open-source, BUKAN hasil kalibrasi khusus sensor/kondisi
tim ini, dan BUKAN rujukan literatur medis. Angka SpO2 yang keluar dari modul ini
TIDAK BOLEH dianggap akurat secara klinis sampai dikalibrasi ulang (mis. dibandingkan
pulse oximeter medis rujukan pada subjek sehat). Selalu tampilkan sebagai skrining/
indikasi kasar, sesuai batasan yang sudah disepakati di keputusan_terkunci.md.

Fungsi murni — menerima sinyal red & infrared yang SUDAH difilter oleh
bandpass_filter.py (komponen kardiak), menghitung rasio AC/DC tiap kanal, lalu
rasio-of-ratios (R), lalu memetakan R ke persen SpO2 via kurva kalibrasi linear.
"""

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Spo2Estimate:
    spo2_percent: float | None
    confidence: str  # "good" | "poor" — sama prinsip dengan HrEstimate, lihat hr_estimator.py
    ratio_r: float | None


def _ac_dc_ratio(filtered_signal: np.ndarray, raw_signal: np.ndarray) -> float:
    """AC = amplitudo komponen kardiak (band-pass), DC = level sinyal mentah rata-rata.

    `raw_signal` HARUS sinyal sebelum band-pass (baseline absorpsi cahaya keseluruhan),
    `filtered_signal` HARUS hasil bandpass_filter.py (komponen berdenyut).
    """
    ac = float(np.std(filtered_signal))
    dc = float(np.mean(raw_signal))
    if dc == 0:
        return 0.0
    return ac / dc


def estimate_spo2(
    red_filtered: np.ndarray,
    red_raw: np.ndarray,
    infrared_filtered: np.ndarray,
    infrared_raw: np.ndarray,
    calibration_coeff_a: float,
    calibration_coeff_b: float,
    plausible_min_percent: float,
    plausible_max_percent: float,
) -> Spo2Estimate:
    """Estimasi SpO2 dari sinyal red & infrared MAX30102.

    Rumus: R = (AC_red / DC_red) / (AC_infrared / DC_infrared)
           SpO2 = calibration_coeff_a + calibration_coeff_b * R

    🚨 `calibration_coeff_a/b` BELUM tervalidasi klinis — lihat peringatan di docstring modul.

    `confidence="poor"` (bukan exception) dikembalikan bila DC infrared nol (divide-by-zero)
    atau hasil SpO2 di luar rentang plausible — sama prinsip dengan hr_estimator.py: tidak
    menampilkan angka SpO2 palsu dengan percaya diri (SDD_SOFTWARE.md §8).
    """
    red_filtered = np.asarray(red_filtered, dtype=float)
    red_raw = np.asarray(red_raw, dtype=float)
    infrared_filtered = np.asarray(infrared_filtered, dtype=float)
    infrared_raw = np.asarray(infrared_raw, dtype=float)

    ratio_red = _ac_dc_ratio(red_filtered, red_raw)
    ratio_infrared = _ac_dc_ratio(infrared_filtered, infrared_raw)

    if ratio_infrared == 0:
        return Spo2Estimate(spo2_percent=None, confidence="poor", ratio_r=None)

    ratio_r = ratio_red / ratio_infrared
    spo2_percent = calibration_coeff_a + calibration_coeff_b * ratio_r

    if not (plausible_min_percent <= spo2_percent <= plausible_max_percent):
        return Spo2Estimate(
            spo2_percent=round(spo2_percent, 1), confidence="poor", ratio_r=round(ratio_r, 4)
        )

    return Spo2Estimate(
        spo2_percent=round(spo2_percent, 1), confidence="good", ratio_r=round(ratio_r, 4)
    )
