from datetime import datetime, timedelta, timezone

from backend.models import db
from backend.models.classification import ReadingClassification
from backend.models.device import Device
from backend.models.trend import TrendEvent
from backend.trend_analysis.trend_service import compute_and_save_trend

DEVICE_ID = "pneumacare-a1b2"


def _seed_classifications(app, classes: list[str], interval_minutes: float = 1.0):
    now = datetime.now(timezone.utc)
    with app.app_context():
        db.session.add(Device(device_id=DEVICE_ID, status="online"))
        for i, cls in enumerate(classes):
            ts = now + timedelta(minutes=i * interval_minutes)
            db.session.add(
                ReadingClassification(
                    id=f"segment-{i}",
                    device_id=DEVICE_ID,
                    channel_id=1,
                    segment_start=ts - timedelta(seconds=5),
                    segment_end=ts,
                    predicted_class=cls,
                    confidence=0.9,
                    probabilities={"normal": 0.1, "abnormal": 0.9},
                    model_version="test-version",
                )
            )
        db.session.commit()


def test_returns_none_when_not_enough_history(app):
    # TREND_ROLLING_WINDOW_SIZE default = 6 -> perlu >= window_size+1 segmen untuk >=2 titik
    _seed_classifications(app, ["abnormal"] * 3)

    with app.app_context():
        result = compute_and_save_trend(app, DEVICE_ID, channel_id=1)

    assert result is None
    with app.app_context():
        assert db.session.query(TrendEvent).count() == 0


def test_rising_abnormal_frequency_produces_significant_trend(app):
    # normal -> makin sering abnormal seiring waktu, cukup segmen untuk >=2 rolling-window points
    classes = ["normal"] * 6 + ["abnormal"] * 6
    _seed_classifications(app, classes)

    with app.app_context():
        result = compute_and_save_trend(app, DEVICE_ID, channel_id=1)

        assert result is not None
        assert result.slope > 0
        assert result.significant is True
        stored = db.session.query(TrendEvent).one()
        assert stored.device_id == DEVICE_ID
        assert stored.significant == result.significant
