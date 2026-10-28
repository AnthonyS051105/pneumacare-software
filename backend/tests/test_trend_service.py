from datetime import datetime, timedelta, timezone

import pytest

from backend.models import db
from backend.models.classification import ReadingClassification
from backend.models.device import Device
from backend.models.trend import TrendEvent
from backend.models.patient import Patient
from backend.models.threshold import Threshold
from backend.alerting.alert_engine import VitalReading
from backend.alerting.alert_service import evaluate_and_save_alert
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


@pytest.mark.parametrize("threshold,default,expected", [
    (999, 0.05, False), (0.01, 999, True), (0, 999, True),
    (None, 999, False), (None, 0.05, True),
])
def test_patient_threshold_controls_saved_trend_and_alert(app, threshold, default, expected):
    _seed_classifications(app, ["normal"] * 6 + ["abnormal"] * 6)
    app.config["TREND_SIGNIFICANCE_THRESHOLD_DEFAULT"] = default
    with app.app_context():
        db.session.add_all([Patient(id="patient-a", name="A"), Patient(id="patient-b", name="B")])
        db.session.flush()
        db.session.get(Device, DEVICE_ID).patient_id = "patient-a"
        db.session.add_all([
            Threshold(patient_id="patient-a", trend_significance_threshold=threshold),
            Threshold(patient_id="patient-b", trend_significance_threshold=0 if not expected else 999),
        ])
        db.session.commit()
        trend = compute_and_save_trend(app, DEVICE_ID, 1)
        assert trend.significant is expected
        assert db.session.query(TrendEvent).one().significant is expected
        alert = evaluate_and_save_alert(app, DEVICE_ID, VitalReading(None, None, None), trend)
        assert (alert is not None) is expected
        if alert:
            assert alert.triggers[0]["threshold"] == (threshold if threshold is not None else default)


def test_paired_patient_without_threshold_row_uses_application_default(app):
    _seed_classifications(app, ["normal"] * 6 + ["abnormal"] * 6)
    app.config["TREND_SIGNIFICANCE_THRESHOLD_DEFAULT"] = 999
    with app.app_context():
        db.session.add(Patient(id="patient-no-threshold", name="No configuration"))
        db.session.flush()
        db.session.get(Device, DEVICE_ID).patient_id = "patient-no-threshold"
        db.session.commit()
        result = compute_and_save_trend(app, DEVICE_ID, 1)
        assert result is not None
        assert result.significant is False
