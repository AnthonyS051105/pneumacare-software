from datetime import datetime, timedelta

import pytest

from backend.analytics.wear_time import StatusChange, compute_daily_online_hours, compute_online_duration_seconds

DAY_START = datetime(2026, 1, 1, 0, 0, 0)
DAY_END = DAY_START + timedelta(days=1)


def test_no_changes_stays_offline_whole_range():
    duration = compute_online_duration_seconds([], DAY_START, DAY_END, status_before_range="offline")
    assert duration == 0


def test_no_changes_stays_online_whole_range():
    duration = compute_online_duration_seconds([], DAY_START, DAY_END, status_before_range="online")
    assert duration == 86400  # 24 jam penuh


def test_single_online_period_within_range():
    changes = [
        StatusChange("online", DAY_START + timedelta(hours=2)),
        StatusChange("offline", DAY_START + timedelta(hours=6)),
    ]
    duration = compute_online_duration_seconds(changes, DAY_START, DAY_END)
    assert duration == 4 * 3600  # online dari jam 2 ke jam 6


def test_online_before_range_start_counted_from_range_start():
    changes = [StatusChange("offline", DAY_START + timedelta(hours=3))]
    duration = compute_online_duration_seconds(changes, DAY_START, DAY_END, status_before_range="online")
    assert duration == 3 * 3600


def test_still_online_at_range_end_counted_until_range_end():
    changes = [StatusChange("online", DAY_START + timedelta(hours=20))]
    duration = compute_online_duration_seconds(changes, DAY_START, DAY_END)
    assert duration == 4 * 3600  # online dari jam 20 sampai akhir range (jam 24)


def test_multiple_online_offline_cycles_sum_correctly():
    changes = [
        StatusChange("online", DAY_START + timedelta(hours=1)),
        StatusChange("offline", DAY_START + timedelta(hours=2)),
        StatusChange("online", DAY_START + timedelta(hours=5)),
        StatusChange("offline", DAY_START + timedelta(hours=8)),
    ]
    duration = compute_online_duration_seconds(changes, DAY_START, DAY_END)
    assert duration == (1 + 3) * 3600  # (2-1) + (8-5) jam


def test_changes_outside_range_are_ignored():
    changes = [
        StatusChange("online", DAY_START - timedelta(hours=5)),  # sebelum range, jadi status_before_range
        StatusChange("offline", DAY_END + timedelta(hours=5)),  # sesudah range, diabaikan
    ]
    duration = compute_online_duration_seconds(changes, DAY_START, DAY_END, status_before_range="offline")
    # perubahan pertama sebelum range -> current_status jadi online sejak awal range
    assert duration == 86400


def test_raises_on_invalid_range():
    with pytest.raises(ValueError):
        compute_online_duration_seconds([], DAY_END, DAY_START)


def test_daily_online_hours_rounds_to_one_decimal():
    changes = [
        StatusChange("online", DAY_START),
        StatusChange("offline", DAY_START + timedelta(hours=6, minutes=15)),  # 6.25 jam
    ]
    hours = compute_daily_online_hours(changes, DAY_START, DAY_END)
    assert hours == 6.2  # round-half-to-even pada 6.25 -> 6.2
