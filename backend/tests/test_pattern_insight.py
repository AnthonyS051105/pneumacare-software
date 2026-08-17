from datetime import datetime

from backend.analytics.pattern_insight import VitalPoint, compute_most_stable_period, generate_pattern_insight


def _point(hour: int, hr: float, day: int = 1) -> VitalPoint:
    return VitalPoint(timestamp=datetime(2026, 1, day, hour, 0), hr=hr)


def test_returns_none_with_insufficient_data():
    points = [_point(8, 70)]
    assert compute_most_stable_period(points) is None


def test_returns_none_with_only_one_eligible_bucket():
    points = [_point(8, 70), _point(9, 72)]  # semua di bucket "pagi" saja
    assert compute_most_stable_period(points) is None


def test_identifies_most_stable_bucket():
    # pagi: variansi kecil (70, 71, 70)
    # malam: variansi besar (60, 90, 65)
    points = [
        _point(8, 70), _point(9, 71), _point(10, 70),
        _point(19, 60), _point(20, 90), _point(21, 65),
    ]
    assert compute_most_stable_period(points) == "pagi"


def test_ignores_points_with_none_hr():
    points = [_point(8, 70), _point(9, 71), VitalPoint(timestamp=datetime(2026, 1, 1, 10), hr=None)]
    # cuma 1 bucket eligible (pagi, 2 titik valid) -> None
    assert compute_most_stable_period(points) is None


def test_dini_hari_wraps_around_midnight():
    points = [
        _point(23, 70), _point(1, 71),  # dini hari: jam 23 dan jam 1, wrap-around
        _point(8, 60), _point(9, 90),  # pagi: variansi besar
    ]
    assert compute_most_stable_period(points) == "dini hari"


def test_generate_pattern_insight_returns_sentence():
    points = [_point(8, 70), _point(9, 71), _point(19, 60), _point(20, 90)]
    insight = generate_pattern_insight(points)
    assert insight == "Detak jantung Anda paling stabil di pagi hari."


def test_generate_pattern_insight_returns_none_when_no_conclusion():
    assert generate_pattern_insight([_point(8, 70)]) is None
