import numpy as np
import pytest

from backend.vitals.vitals_service import compute_vitals_from_ppg_batch

SAMPLE_RATE_HZ = 100
CARDIAC_LOW_HZ = 1.0
CARDIAC_HIGH_HZ = 2.0
BANDPASS_ORDER = 4
HR_PLAUSIBLE_MIN = 30
HR_PLAUSIBLE_MAX = 220
SPO2_CALIBRATION_A = 110.0
SPO2_CALIBRATION_B = -25.0
SPO2_PLAUSIBLE_MIN = 50
SPO2_PLAUSIBLE_MAX = 100


def _synthetic_ppg_channel(duration_s: float, hr_bpm: float, dc_level: float, ac_amplitude: float) -> list[float]:
    hz = hr_bpm / 60
    t = np.arange(0, duration_s, 1 / SAMPLE_RATE_HZ)
    cardiac = ac_amplitude * np.sin(2 * np.pi * hz * t)
    return (dc_level + cardiac).tolist()


def _compute(samples_ir, samples_red):
    return compute_vitals_from_ppg_batch(
        samples_ir=samples_ir,
        samples_red=samples_red,
        sample_rate_hz=SAMPLE_RATE_HZ,
        cardiac_bandpass_low_hz=CARDIAC_LOW_HZ,
        cardiac_bandpass_high_hz=CARDIAC_HIGH_HZ,
        bandpass_order=BANDPASS_ORDER,
        hr_plausible_min_bpm=HR_PLAUSIBLE_MIN,
        hr_plausible_max_bpm=HR_PLAUSIBLE_MAX,
        spo2_calibration_coeff_a=SPO2_CALIBRATION_A,
        spo2_calibration_coeff_b=SPO2_CALIBRATION_B,
        spo2_plausible_min_percent=SPO2_PLAUSIBLE_MIN,
        spo2_plausible_max_percent=SPO2_PLAUSIBLE_MAX,
    )


def test_hr_only_when_red_channel_absent():
    ir = _synthetic_ppg_channel(duration_s=20, hr_bpm=72, dc_level=1500, ac_amplitude=15)

    hr_estimate, spo2_estimate = _compute(ir, None)

    assert hr_estimate.confidence == "good"
    assert abs(hr_estimate.hr_bpm - 72) < 2.0
    assert spo2_estimate is None


def test_hr_and_spo2_when_red_channel_present():
    ir = _synthetic_ppg_channel(duration_s=20, hr_bpm=72, dc_level=1500, ac_amplitude=15)
    red = _synthetic_ppg_channel(duration_s=20, hr_bpm=72, dc_level=1000, ac_amplitude=20)

    hr_estimate, spo2_estimate = _compute(ir, red)

    assert hr_estimate.confidence == "good"
    assert spo2_estimate is not None
    assert spo2_estimate.ratio_r is not None
    assert spo2_estimate.ratio_r > 0


def test_raises_value_error_when_batch_too_short():
    ir = _synthetic_ppg_channel(duration_s=0.1, hr_bpm=72, dc_level=1500, ac_amplitude=15)

    with pytest.raises(ValueError):
        _compute(ir, None)
