"""Estimasi HR + SpO2 dari batch sample PPG mentah (red + infrared) — FR-SW-031,
FR-SW-032, SDD_SOFTWARE.md §7. Menggabungkan bandpass_filter.py + hr_estimator.py
+ spo2_estimator.py jadi satu titik pemanggilan, mengikuti pola inference_service.py
(logika murni, dipanggil dari ingestion layer yang menangani I/O — CLAUDE.md).

⚠️ RR (respiratory rate) TIDAK dihasilkan di sini — sumber sinyal untuk RR belum
ditentukan (audio vs PPG), lihat catatan di backend/models/vital.py. `rr` di
ReadingVital tetap None dari modul ini.
"""

import numpy as np

from backend.vitals.bandpass_filter import cardiac_bandpass_filter
from backend.vitals.hr_estimator import HrEstimate, estimate_hr
from backend.vitals.spo2_estimator import Spo2Estimate, estimate_spo2


def compute_vitals_from_ppg_batch(
    samples_ir: list[float],
    samples_red: list[float] | None,
    sample_rate_hz: float,
    cardiac_bandpass_low_hz: float,
    cardiac_bandpass_high_hz: float,
    bandpass_order: int,
    hr_plausible_min_bpm: float,
    hr_plausible_max_bpm: float,
    spo2_calibration_coeff_a: float,
    spo2_calibration_coeff_b: float,
    spo2_plausible_min_percent: float,
    spo2_plausible_max_percent: float,
) -> tuple[HrEstimate, Spo2Estimate | None]:
    """Hitung HR dari `samples_ir`, dan SpO2 bila `samples_red` tersedia.

    `samples_red=None` (firmware lama, sebelum INTEGRATION_CONTRACT.md §3.3 revisi
    17 Agt 2026) -> SpO2 di-skip (return None), BUKAN error — HR tetap bisa dihitung
    dari 1 channel saja.

    Raises ValueError bila batch terlalu pendek untuk bandpass_order yang diminta —
    caller (mqtt_subscriber.py) bertanggung jawab menunggu batch cukup panjang
    sebelum memanggil fungsi ini (lebih baik gagal jelas daripada estimasi tidak
    bermakna dari data terlalu sedikit, sama prinsip dengan bandpass_filter.py).
    """
    ir_array = np.asarray(samples_ir, dtype=float)
    ir_filtered = cardiac_bandpass_filter(
        ir_array, sample_rate_hz, cardiac_bandpass_low_hz, cardiac_bandpass_high_hz, bandpass_order
    )

    hr_estimate = estimate_hr(ir_filtered, sample_rate_hz, hr_plausible_min_bpm, hr_plausible_max_bpm)

    if samples_red is None:
        return hr_estimate, None

    red_array = np.asarray(samples_red, dtype=float)
    red_filtered = cardiac_bandpass_filter(
        red_array, sample_rate_hz, cardiac_bandpass_low_hz, cardiac_bandpass_high_hz, bandpass_order
    )

    spo2_estimate = estimate_spo2(
        red_filtered=red_filtered,
        red_raw=red_array,
        infrared_filtered=ir_filtered,
        infrared_raw=ir_array,
        calibration_coeff_a=spo2_calibration_coeff_a,
        calibration_coeff_b=spo2_calibration_coeff_b,
        plausible_min_percent=spo2_plausible_min_percent,
        plausible_max_percent=spo2_plausible_max_percent,
    )
    return hr_estimate, spo2_estimate
