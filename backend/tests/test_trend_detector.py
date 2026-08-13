import pytest

from backend.trend_analysis.rolling_window import compute_rolling_frequency
from backend.trend_analysis.trend_detector import detect_trend
from backend.tests.fixtures.trend_scenarios import (
    falling_wheeze_scenario,
    no_wheeze_scenario,
    rising_wheeze_scenario,
    stable_wheeze_scenario,
)

ROLLING_WINDOW_SIZE = 6
MOVING_AVERAGE_WINDOW = 3
SIGNIFICANCE_THRESHOLD = 0.05


def _detect(events, threshold=SIGNIFICANCE_THRESHOLD):
    points = compute_rolling_frequency(events, window_size=ROLLING_WINDOW_SIZE)
    return detect_trend(
        points,
        moving_average_window=MOVING_AVERAGE_WINDOW,
        significance_threshold=threshold,
    )


def test_rising_scenario_produces_positive_significant_slope():
    result = _detect(rising_wheeze_scenario())
    assert result is not None
    assert result.slope > 0
    assert result.significant is True


def test_falling_scenario_produces_negative_non_significant_slope():
    result = _detect(falling_wheeze_scenario())
    assert result is not None
    assert result.slope < 0
    # tren turun tidak boleh signifikan meski |slope| besar — SDD_SOFTWARE.md §6:
    # hanya arah naik yang memicu alert.
    assert result.significant is False


def test_stable_scenario_has_near_zero_slope_and_not_significant():
    result = _detect(stable_wheeze_scenario())
    assert result is not None
    assert abs(result.slope) < SIGNIFICANCE_THRESHOLD
    assert result.significant is False


def test_no_wheeze_scenario_has_zero_slope():
    result = _detect(no_wheeze_scenario())
    assert result is not None
    assert result.slope == 0
    assert result.significant is False


def test_returns_none_with_fewer_than_two_points():
    points = compute_rolling_frequency(no_wheeze_scenario(n_segments=3), window_size=6)
    result = detect_trend(points, moving_average_window=3, significance_threshold=0.05)
    assert result is None


def test_invalid_metric_raises():
    points = compute_rolling_frequency(rising_wheeze_scenario(), window_size=ROLLING_WINDOW_SIZE)
    with pytest.raises(ValueError):
        detect_trend(points, moving_average_window=3, significance_threshold=0.05, metric="not_a_real_metric")


def test_higher_threshold_can_flip_rising_scenario_to_not_significant():
    result_low_threshold = _detect(rising_wheeze_scenario(), threshold=0.01)
    result_high_threshold = _detect(rising_wheeze_scenario(), threshold=10_000)

    assert result_low_threshold.significant is True
    assert result_high_threshold.significant is False
