import numpy as np
import pytest

from backend.vitals.bandpass_filter import bandpass_filter

SAMPLE_RATE_HZ = 100


def _synthetic_ppg(duration_s: float, cardiac_hz: float, respiratory_hz: float) -> np.ndarray:
    t = np.arange(0, duration_s, 1 / SAMPLE_RATE_HZ)
    cardiac = np.sin(2 * np.pi * cardiac_hz * t)
    respiratory = 0.5 * np.sin(2 * np.pi * respiratory_hz * t)
    noise = 0.05 * np.random.default_rng(42).standard_normal(len(t))
    return cardiac + respiratory + noise


def test_bandpass_attenuates_out_of_band_respiratory_component():
    signal = _synthetic_ppg(duration_s=30, cardiac_hz=1.5, respiratory_hz=0.3)
    filtered = bandpass_filter(signal, SAMPLE_RATE_HZ, low_hz=1.0, high_hz=2.0, order=4)

    fft_freqs = np.fft.rfftfreq(len(filtered), d=1 / SAMPLE_RATE_HZ)
    fft_magnitude = np.abs(np.fft.rfft(filtered))

    cardiac_band_power = fft_magnitude[(fft_freqs >= 1.0) & (fft_freqs <= 2.0)].sum()
    respiratory_band_power = fft_magnitude[(fft_freqs >= 0.2) & (fft_freqs <= 0.5)].sum()

    assert cardiac_band_power > respiratory_band_power * 5


def test_output_same_length_as_input():
    signal = _synthetic_ppg(duration_s=10, cardiac_hz=1.5, respiratory_hz=0.3)
    filtered = bandpass_filter(signal, SAMPLE_RATE_HZ, low_hz=1.0, high_hz=2.0, order=4)
    assert len(filtered) == len(signal)


def test_raises_on_invalid_cutoff_above_nyquist():
    signal = _synthetic_ppg(duration_s=10, cardiac_hz=1.5, respiratory_hz=0.3)
    with pytest.raises(ValueError):
        bandpass_filter(signal, SAMPLE_RATE_HZ, low_hz=1.0, high_hz=60.0, order=4)


def test_raises_on_low_greater_than_high():
    signal = _synthetic_ppg(duration_s=10, cardiac_hz=1.5, respiratory_hz=0.3)
    with pytest.raises(ValueError):
        bandpass_filter(signal, SAMPLE_RATE_HZ, low_hz=2.0, high_hz=1.0, order=4)


def test_raises_on_signal_too_short():
    short_signal = np.array([0.1, 0.2, 0.3])
    with pytest.raises(ValueError):
        bandpass_filter(short_signal, SAMPLE_RATE_HZ, low_hz=1.0, high_hz=2.0, order=4)
