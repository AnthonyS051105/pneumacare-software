from datetime import datetime, timedelta, timezone

from backend.alerting.alert_engine import VitalReading
from backend.alerting.alert_service import evaluate_and_save_alert
from backend.models import db
from backend.models.alert import Alert
from backend.models.device import Device
from backend.models.patient import Patient
from backend.models.threshold import Threshold
from backend.models.trend import TrendEvent
from backend.trend_analysis.trend_detector import TrendResult


def _seed_device_with_patient(app, device_id="pneumacare-a1b2", patient_id="patient-1"):
    with app.app_context():
        db.session.add(Patient(id=patient_id, name="Pasien Test"))
        db.session.add(Device(device_id=device_id, status="online", patient_id=patient_id))
        db.session.commit()


def test_returns_none_when_device_not_paired_to_patient(app):
    with app.app_context():
        db.session.add(Device(device_id="pneumacare-a1b2", status="online"))
        db.session.commit()

        result = evaluate_and_save_alert(
            app, "pneumacare-a1b2", VitalReading(hr=200, spo2=None, rr=None), trend_result=None
        )

        assert result is None
        assert db.session.query(Alert).count() == 0


def test_no_threshold_configured_produces_no_alert(app):
    _seed_device_with_patient(app)
    with app.app_context():
        result = evaluate_and_save_alert(
            app, "pneumacare-a1b2", VitalReading(hr=200, spo2=50, rr=None), trend_result=None
        )

        assert result is None
        assert db.session.query(Alert).count() == 0


def test_hr_breach_creates_alert_with_correct_patient(app):
    _seed_device_with_patient(app)
    with app.app_context():
        db.session.add(Threshold(patient_id="patient-1", hr_min=60, hr_max=100, spo2_min=92))
        db.session.commit()

        result = evaluate_and_save_alert(
            app, "pneumacare-a1b2", VitalReading(hr=150, spo2=None, rr=None), trend_result=None
        )

        assert result is not None
        assert result.level == 2
        stored = db.session.query(Alert).one()
        assert stored.patient_id == "patient-1"
        assert stored.device_id == "pneumacare-a1b2"
        assert stored.level == 2
        assert stored.triggers[0]["parameter"] == "hr"


def test_significant_trend_plus_persistence_escalates_to_level_3(app):
    _seed_device_with_patient(app)
    now = datetime.now(timezone.utc)
    with app.app_context():
        db.session.add(Threshold(patient_id="patient-1", trend_significance_threshold=0.05))
        # 2 evaluasi trend signifikan sebelumnya + evaluasi saat ini (di bawah) = 3 berturut-turut
        db.session.add(
            TrendEvent(
                id="t1",
                device_id="pneumacare-a1b2",
                window_start=now - timedelta(minutes=10),
                window_end=now - timedelta(minutes=8),
                slope=0.1,
                significant=True,
            )
        )
        db.session.add(
            TrendEvent(
                id="t2",
                device_id="pneumacare-a1b2",
                window_start=now - timedelta(minutes=6),
                window_end=now - timedelta(minutes=4),
                slope=0.1,
                significant=True,
            )
        )
        db.session.commit()

        trend_result = TrendResult(window_start=now - timedelta(minutes=2), window_end=now, slope=0.1, significant=True)
        result = evaluate_and_save_alert(
            app, "pneumacare-a1b2", VitalReading(hr=None, spo2=None, rr=None), trend_result=trend_result
        )

        assert result is not None
        assert result.level == 3
        assert result.triggers[0]["type"] == "trend_slope"
