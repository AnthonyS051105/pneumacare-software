from datetime import datetime, timedelta

from backend.trend_analysis.rolling_window import ClassificationEvent, compute_rolling_frequency

SEGMENT_DURATION = timedelta(seconds=5)
BASE = datetime(2026, 1, 1, 8, 0, 0)


def _events(wheeze_pattern: list[bool]) -> list[ClassificationEvent]:
    return [
        ClassificationEvent(
            timestamp=BASE + i * SEGMENT_DURATION,
            wheeze_crackle_class="wheeze" if w else "none",
        )
        for i, w in enumerate(wheeze_pattern)
    ]


def test_wheeze_present_and_crackle_present_derived_from_class():
    event_none = ClassificationEvent(timestamp=BASE, wheeze_crackle_class="none")
    event_wheeze = ClassificationEvent(timestamp=BASE, wheeze_crackle_class="wheeze")
    event_crackle = ClassificationEvent(timestamp=BASE, wheeze_crackle_class="crackle")
    event_both = ClassificationEvent(timestamp=BASE, wheeze_crackle_class="both")

    assert (event_none.wheeze_present, event_none.crackle_present) == (False, False)
    assert (event_wheeze.wheeze_present, event_wheeze.crackle_present) == (True, False)
    assert (event_crackle.wheeze_present, event_crackle.crackle_present) == (False, True)
    assert (event_both.wheeze_present, event_both.crackle_present) == (True, True)


def test_returns_no_points_when_fewer_events_than_window():
    events = _events([True, True])
    points = compute_rolling_frequency(events, window_size=5)
    assert points == []


def test_frequency_counts_present_events_in_window():
    # window_size=3: [T, F, F] -> 1 wheeze dalam 10 detik (3 segmen x 5 detik = index 0..2)
    events = _events([True, False, False, False])
    points = compute_rolling_frequency(events, window_size=3)

    assert len(points) == 2  # end_idx = 2 dan 3
    first = points[0]
    # window [0,1,2] = [True, False, False], durasi 10s = 1/6 menit -> 1 wheeze / (1/6 menit) = 6/menit
    assert first.wheeze_frequency == 6.0
    assert first.crackle_frequency == 0.0


def test_window_slides_by_one_segment():
    events = _events([True, True, True, True, True])
    points = compute_rolling_frequency(events, window_size=2)
    # tiap window 2 segmen, keduanya selalu True -> frequency sama di semua titik
    assert len(points) == 4
    frequencies = [p.wheeze_frequency for p in points]
    assert all(f == frequencies[0] for f in frequencies)


def test_raises_on_invalid_window_size():
    import pytest

    with pytest.raises(ValueError):
        compute_rolling_frequency(_events([True]), window_size=0)
