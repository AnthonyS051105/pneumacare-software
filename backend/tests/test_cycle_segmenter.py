import pytest

from backend.analysis import cycle_segmenter
from backend.analysis.resp_cycle import _align_cycle_scores

FS = 16_000


def test_cycle_scores_are_aligned_except_for_model_cycle():
    # bounds: [c0, lo, hi, c1]; model adalah siklus (lo, hi) di indeks 1.
    assert _align_cycle_scores([0, 1, 2, 3], [10.0, 20.0], model_lo=1) == [
        10.0,
        None,
        20.0,
    ]


def test_detected_cycles_are_sliced_at_exact_boundaries(monkeypatch):
    monkeypatch.setattr(
        cycle_segmenter,
        "detect_respiratory_cycles",
        lambda x, fs: {
            "cycles": [(1.0, 2.0), (2.0, 3.5)],
            "mean_dtw": 0.25,
            "cycle_scores": [0.2, 0.3],
            "boundaries": [1.0, 2.0, 3.5],
        },
    )
    pcm = list(range(FS * 5))

    result = cycle_segmenter.detect_cycle_slices(pcm, FS)

    assert result.status == "detected"
    assert result.mean_dtw == pytest.approx(0.25)
    assert [c.index for c in result.cycles] == [1, 2]

    first, second = result.cycles
    assert (first.start_s, first.end_s) == (1.0, 2.0)
    assert first.pcm_samples == pcm[FS : 2 * FS]
    assert first.dtw_score == pytest.approx(0.2)

    assert (second.start_s, second.end_s) == (2.0, 3.5)
    assert second.pcm_samples == pcm[2 * FS : int(3.5 * FS)]
    assert second.dtw_score == pytest.approx(0.3)


def test_no_cycles_returns_fallback_status(monkeypatch):
    monkeypatch.setattr(
        cycle_segmenter,
        "detect_respiratory_cycles",
        lambda x, fs: {"cycles": [], "mean_dtw": None},
    )

    result = cycle_segmenter.detect_cycle_slices([0] * FS * 5, FS)

    assert result.status == "no_cycles"
    assert result.cycles == []
    assert result.mean_dtw is None


def test_unsupported_sample_rate_skips_detector(monkeypatch):
    def must_not_be_called(x, fs):
        raise AssertionError("detektor tidak boleh dipanggil untuk fs terlalu rendah")

    monkeypatch.setattr(cycle_segmenter, "detect_respiratory_cycles", must_not_be_called)

    result = cycle_segmenter.detect_cycle_slices([0] * 1000, 1000)

    assert result.status == "unsupported_sample_rate"
    assert result.cycles == []


def test_detector_error_returns_error_status(monkeypatch):
    def boom(x, fs):
        raise ValueError("sinyal rusak")

    monkeypatch.setattr(cycle_segmenter, "detect_respiratory_cycles", boom)

    result = cycle_segmenter.detect_cycle_slices([0] * FS * 5, FS)

    assert result.status == "error"
    assert result.error == "sinyal rusak"
    assert result.cycles == []


def test_cycles_with_no_samples_are_skipped(monkeypatch):
    monkeypatch.setattr(
        cycle_segmenter,
        "detect_respiratory_cycles",
        lambda x, fs: {
            "cycles": [(0.0, 0.0), (1.0, 2.0)],
            "mean_dtw": 0.1,
            "cycle_scores": [None, 0.1],
        },
    )
    pcm = list(range(FS * 5))

    result = cycle_segmenter.detect_cycle_slices(pcm, FS)

    assert result.status == "detected"
    assert len(result.cycles) == 1
    assert result.cycles[0].index == 2
    assert result.cycles[0].pcm_samples == pcm[FS : 2 * FS]
