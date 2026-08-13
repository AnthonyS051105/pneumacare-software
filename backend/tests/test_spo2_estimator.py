import numpy as np

from backend.vitals.bandpass_filter import bandpass_filter
from backend.vitals.spo2_estimator import estimate_spo2

SAMPLE_RATE_HZ = 100
CALIBRATION_A = 110.0
CALIBRATION_B = -25.0
PLAUSIBLE_MIN = 50
PLAUSIBLE_MAX = 100


def _synthetic_ppg_channel(duration_s: float, hr_bpm: float, dc_level: float, ac_amplitude: float) -> np.ndarray:
    hz = hr_bpm / 60
    t = np.arange(0, duration_s, 1 / SAMPLE_RATE_HZ)
    cardiac = ac_amplitude * np.sin(2 * np.pi * hz * t)
    return dc_level + cardiac


def _filtered(raw_signal: np.ndarray) -> np.ndarray:
    return bandpass_filter(raw_signal, SAMPLE_RATE_HZ, low_hz=1.0, high_hz=2.0, order=4)


def test_returns_plausible_spo2_for_typical_signal():
    red_raw = _synthetic_ppg_channel(duration_s=20, hr_bpm=72, dc_level=1000, ac_amplitude=20)
    infrared_raw = _synthetic_ppg_channel(duration_s=20, hr_bpm=72, dc_level=1500, ac_amplitude=15)

    result = estimate_spo2(
        red_filtered=_filtered(red_raw),
        red_raw=red_raw,
        infrared_filtered=_filtered(infrared_raw),
        infrared_raw=infrared_raw,
        calibration_coeff_a=CALIBRATION_A,
        calibration_coeff_b=CALIBRATION_B,
        plausible_min_percent=PLAUSIBLE_MIN,
        plausible_max_percent=PLAUSIBLE_MAX,
    )

    assert result.ratio_r is not None
    assert result.ratio_r > 0
    if result.confidence == "good":
        assert PLAUSIBLE_MIN <= result.spo2_percent <= PLAUSIBLE_MAX


def test_zero_infrared_dc_returns_poor_confidence():
    # infrared_raw benar-benar nol (mis. sensor infrared mati/lepas kontak) -> DC=0 persis,
    # rasio AC/DC infrared tidak terdefinisi -> harus poor, bukan crash divide-by-zero.
    red_raw = _synthetic_ppg_channel(duration_s=10, hr_bpm=72, dc_level=1000, ac_amplitude=20)
    infrared_raw = np.zeros(int(SAMPLE_RATE_HZ * 10))

    result = estimate_spo2(
        red_filtered=_filtered(red_raw),
        red_raw=red_raw,
        infrared_filtered=_filtered(infrared_raw),
        infrared_raw=infrared_raw,
        calibration_coeff_a=CALIBRATION_A,
        calibration_coeff_b=CALIBRATION_B,
        plausible_min_percent=PLAUSIBLE_MIN,
        plausible_max_percent=PLAUSIBLE_MAX,
    )

    assert result.confidence == "poor"
    assert result.spo2_percent is None
    assert result.ratio_r is None


def test_implausible_spo2_flagged_as_poor_confidence():
    # AC/DC red jauh lebih besar dari infrared -> ratio_r besar -> SpO2 hasil hitung
    # jatuh di luar rentang plausible (bisa negatif atau >100%), harus ditandai poor.
    red_raw = _synthetic_ppg_channel(duration_s=10, hr_bpm=72, dc_level=100, ac_amplitude=90)
    infrared_raw = _synthetic_ppg_channel(duration_s=10, hr_bpm=72, dc_level=10000, ac_amplitude=1)

    result = estimate_spo2(
        red_filtered=_filtered(red_raw),
        red_raw=red_raw,
        infrared_filtered=_filtered(infrared_raw),
        infrared_raw=infrared_raw,
        calibration_coeff_a=CALIBRATION_A,
        calibration_coeff_b=CALIBRATION_B,
        plausible_min_percent=PLAUSIBLE_MIN,
        plausible_max_percent=PLAUSIBLE_MAX,
    )

    assert result.confidence == "poor"


def test_result_never_exceeds_100_percent_when_good_confidence():
    # Sanity check fisiologis: bahkan dengan placeholder belum terkalibrasi, hasil "good"
    # tidak boleh lolos di atas 100% (plausible_max_percent=100 harus ditegakkan).
    red_raw = _synthetic_ppg_channel(duration_s=20, hr_bpm=80, dc_level=1200, ac_amplitude=18)
    infrared_raw = _synthetic_ppg_channel(duration_s=20, hr_bpm=80, dc_level=1400, ac_amplitude=16)

    result = estimate_spo2(
        red_filtered=_filtered(red_raw),
        red_raw=red_raw,
        infrared_filtered=_filtered(infrared_raw),
        infrared_raw=infrared_raw,
        calibration_coeff_a=CALIBRATION_A,
        calibration_coeff_b=CALIBRATION_B,
        plausible_min_percent=PLAUSIBLE_MIN,
        plausible_max_percent=PLAUSIBLE_MAX,
    )

    if result.confidence == "good":
        assert result.spo2_percent <= 100
