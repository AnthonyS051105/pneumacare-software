from datetime import datetime, timedelta

import pytest

from backend.analytics.classification_history import ClassifiedSegment, bucket_classifications

START = datetime(2026, 10, 22, 0, 0)


def _seg(minutes: float, cls: str) -> ClassifiedSegment:
    return ClassifiedSegment(segment_end=START + timedelta(minutes=minutes), predicted_class=cls)


def test_counts_per_bucket_and_ratio():
    rows = bucket_classifications(
        [_seg(1, "normal"), _seg(2, "abnormal"), _seg(3, "abnormal"), _seg(61, "normal")],
        START,
        START + timedelta(hours=2),
        timedelta(hours=1),
    )

    assert len(rows) == 2
    assert rows[0]["total"] == 3
    assert rows[0]["normal"] == 1 and rows[0]["abnormal"] == 2
    assert rows[0]["abnormal_ratio"] == pytest.approx(2 / 3, abs=1e-4)
    assert rows[1]["normal"] == 1
    assert rows[1]["abnormal_ratio"] == 0.0


def test_empty_bucket_has_null_ratio_not_zero():
    rows = bucket_classifications([_seg(1, "abnormal")], START, START + timedelta(hours=3), timedelta(hours=1))

    assert [r["total"] for r in rows] == [1, 0, 0]
    assert rows[1]["abnormal_ratio"] is None


def test_segments_outside_window_are_ignored():
    rows = bucket_classifications(
        [_seg(-5, "abnormal"), _seg(120, "abnormal"), _seg(30, "normal")],
        START,
        START + timedelta(hours=2),
        timedelta(hours=1),
    )

    assert sum(r["total"] for r in rows) == 1


def test_unknown_class_counts_in_total_only():
    rows = bucket_classifications([_seg(1, "mystery")], START, START + timedelta(hours=1), timedelta(hours=1))

    assert rows[0]["total"] == 1
    assert rows[0]["abnormal_ratio"] == 0.0


def test_partial_last_bucket_is_included():
    rows = bucket_classifications([_seg(90, "abnormal")], START, START + timedelta(minutes=90, seconds=1), timedelta(hours=1))

    assert len(rows) == 2
    assert rows[1]["abnormal"] == 1


def test_invalid_window_and_bucket():
    assert bucket_classifications([], START, START, timedelta(hours=1)) == []
    with pytest.raises(ValueError):
        bucket_classifications([], START, START + timedelta(hours=1), timedelta(0))
