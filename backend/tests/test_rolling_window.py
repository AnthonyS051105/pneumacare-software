from datetime import datetime, timedelta

import pytest

from backend.trend_analysis.rolling_window import ClassificationEvent, compute_rolling_frequency

SEGMENT_DURATION = timedelta(seconds=5)
BASE = datetime(2026, 1, 1, 8, 0, 0)


def _events(abnormal_pattern: list[bool]) -> list[ClassificationEvent]:
    return [
        ClassificationEvent(
            timestamp=BASE + i * SEGMENT_DURATION,
            predicted_class="abnormal" if abnormal else "normal",
        )
        for i, abnormal in enumerate(abnormal_pattern)
    ]


def test_returns_no_points_when_fewer_events_than_window():
    events = _events([True, True])
    points = compute_rolling_frequency(events, window_size=5)
    assert points == []


def test_frequency_counts_abnormal_events_in_window():
    # window_size=3: [A, N, N] -> 1 abnormal dalam 10 detik (3 segmen x 5 detik = index 0..2)
    events = _events([True, False, False, False])
    points = compute_rolling_frequency(events, window_size=3)

    assert len(points) == 2  # end_idx = 2 dan 3
    first = points[0]
    # window [0,1,2] = [A, N, N], durasi 10s = 1/6 menit -> 1 abnormal / (1/6 menit) = 6/menit
    assert first.abnormal_frequency == 6.0


def test_normal_events_do_not_increase_frequency():
    events = _events([False, False, False])
    points = compute_rolling_frequency(events, window_size=3)
    assert points[0].abnormal_frequency == 0.0


def test_window_slides_by_one_segment():
    events = _events([True, True, True, True, True])
    points = compute_rolling_frequency(events, window_size=2)
    # tiap window 2 segmen, keduanya selalu abnormal -> frequency sama di semua titik
    assert len(points) == 4
    frequencies = [p.abnormal_frequency for p in points]
    assert all(f == frequencies[0] for f in frequencies)


def test_raises_on_invalid_window_size():
    with pytest.raises(ValueError):
        compute_rolling_frequency(_events([True]), window_size=0)
