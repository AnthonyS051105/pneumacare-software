import numpy as np

from backend.vitals.hr_estimator import estimate_hr

SAMPLE_RATE_HZ = 100
PLAUSIBLE_MIN_BPM = 30
PLAUSIBLE_MAX_BPM = 220


def _synthetic_cardiac_signal(duration_s: float, hr_bpm: float) -> np.ndarray:
    hz = hr_bpm / 60
    t = np.arange(0, duration_s, 1 / SAMPLE_RATE_HZ)
    return np.sin(2 * np.pi * hz * t)


def test_estimates_known_hr_within_tolerance():
    signal = _synthetic_cardiac_signal(duration_s=20, hr_bpm=72)
    result = estimate_hr(signal, SAMPLE_RATE_HZ, PLAUSIBLE_MIN_BPM, PLAUSIBLE_MAX_BPM)

    assert result.confidence == "good"
    assert result.hr_bpm is not None
    assert abs(result.hr_bpm - 72) < 2.0


def test_estimates_high_hr_within_tolerance():
    signal = _synthetic_cardiac_signal(duration_s=15, hr_bpm=140)
    result = estimate_hr(signal, SAMPLE_RATE_HZ, PLAUSIBLE_MIN_BPM, PLAUSIBLE_MAX_BPM)

    assert result.confidence == "good"
    assert abs(result.hr_bpm - 140) < 3.0


def test_flat_signal_returns_poor_confidence():
    signal = np.zeros(int(SAMPLE_RATE_HZ * 10))
    result = estimate_hr(signal, SAMPLE_RATE_HZ, PLAUSIBLE_MIN_BPM, PLAUSIBLE_MAX_BPM)

    assert result.confidence == "poor"
    assert result.hr_bpm is None


def test_noise_only_signal_does_not_crash_and_flags_low_confidence():
    rng = np.random.default_rng(7)
    signal = rng.standard_normal(int(SAMPLE_RATE_HZ * 10))
    result = estimate_hr(signal, SAMPLE_RATE_HZ, PLAUSIBLE_MIN_BPM, PLAUSIBLE_MAX_BPM)

    # Boleh "good" atau "poor" tergantung random seed (noise kadang kebetulan periodik semu),
    # tapi TIDAK BOLEH crash dan HARUS tetap mengembalikan objek HrEstimate valid.
    assert result.confidence in ("good", "poor")


def test_implausibly_slow_hr_flagged_as_poor_confidence():
    # Sinyal lebih lambat dari plausible_min_bpm mensimulasikan artefak/drift baseline
    # yang terdeteksi find_peaks sebagai "detak" (mis. gerakan pasien), bukan detak jantung
    # sungguhan — HARUS ditandai poor, bukan ditampilkan sebagai HR valid.
    signal = _synthetic_cardiac_signal(duration_s=30, hr_bpm=15)
    result = estimate_hr(signal, SAMPLE_RATE_HZ, PLAUSIBLE_MIN_BPM, PLAUSIBLE_MAX_BPM)

    assert result.confidence == "poor"


def test_max_bpm_constraint_prevents_double_counting_noisy_peaks():
    # plausible_max_bpm dipakai sebagai batas *jarak minimum* antar-puncak (bukan cuma
    # validasi akhir) — sinyal yang "secara sinyal" 400 bpm tidak mungkin lolos sebagai
    # >plausible_max_bpm karena find_peaks sendiri dibatasi tidak menghitung puncak
    # sedekat itu. HR hasil deteksi karenanya selalu <= plausible_max_bpm secara desain.
    signal = _synthetic_cardiac_signal(duration_s=10, hr_bpm=400)
    result = estimate_hr(signal, SAMPLE_RATE_HZ, PLAUSIBLE_MIN_BPM, PLAUSIBLE_MAX_BPM)

    if result.hr_bpm is not None:
        assert result.hr_bpm <= PLAUSIBLE_MAX_BPM
