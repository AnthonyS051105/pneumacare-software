"""Regression tests for the five fixed pre-merge audit findings."""
from datetime import datetime, timedelta, timezone

import pytest

from backend.models import db
from backend.models.alert import Alert
from backend.models.device import Device
from backend.models.patient import Patient
from backend.models.threshold import Threshold
from backend.models.vital import ReadingVital
from backend.tests.test_patient_routes import _seed_patient_with_device, _login_patient
from backend.tests.test_trend_service import _seed_classifications, DEVICE_ID
from backend.trend_analysis.trend_service import compute_and_save_trend


def test_patient_trend_threshold_is_used_for_significance(app):
    _seed_classifications(app, ['normal']*6 + ['abnormal']*6)
    with app.app_context():
        patient = Patient(id='audit-patient', name='Audit Fixture')
        db.session.add(patient)
        db.session.flush()
        db.session.get(Device, DEVICE_ID).patient_id = patient.id
        db.session.add(Threshold(patient_id=patient.id, trend_significance_threshold=999))
        db.session.commit()
        trend = compute_and_save_trend(app, DEVICE_ID, 1)
        assert 0 < trend.slope < 999
        assert trend.significant is False


def test_patient_summary_keeps_unresolved_urgent_status(app, client):
    _seed_patient_with_device(app)
    with app.app_context():
        now = datetime.now(timezone.utc)
        db.session.add(ReadingVital(device_id=DEVICE_ID, timestamp=now, hr=75, spo2=97, rr=None))
        db.session.add_all([
            Alert(device_id=DEVICE_ID,patient_id='patient-1',level=3,triggers=[],
                  created_at=now-timedelta(minutes=2),acknowledged=False),
            Alert(device_id=DEVICE_ID,patient_id='patient-1',level=1,triggers=[],
                  created_at=now,acknowledged=True),
        ])
        db.session.commit()
    _login_patient(client)
    response = client.get('/api/v1/patient/me/summary')
    assert response.status_code == 200
    assert response.get_json()['status_label'] == 'urgent'


def test_audio_does_not_reuse_poor_quality_ppg_for_alerts(app, monkeypatch):
    import numpy as np
    from backend.ingestion import mqtt_subscriber as mqtt
    from backend.ingestion import websocket_server as audio
    from backend.ingestion.audio_segment_buffer import Segment
    from backend.analysis.cycle_segmenter import CycleDetectionResult
    from backend.vitals.hr_estimator import HrEstimate
    _seed_patient_with_device(app)
    with app.app_context():
        # Synthetic test values only, not clinical defaults.
        db.session.add(Threshold(patient_id='patient-1', hr_min=60, hr_max=100))
        db.session.commit()
    monkeypatch.setattr(mqtt, 'compute_vitals_from_ppg_batch',
                        lambda **kw: (HrEstimate(hr_bpm=25, confidence='poor', peak_count=3),None))
    monkeypatch.setattr(audio, 'detect_cycle_slices',
                        lambda *args: CycleDetectionResult(status='no_cycles'))
    mqtt._run_vitals_estimation(app, DEVICE_ID,100)
    with app.app_context():
        assert Alert.query.count() == 0  # immediate PPG path correctly filters it
        now = int(datetime.now(timezone.utc).timestamp()*1000)
        audio._handle_segment(Segment(DEVICE_ID,1,now-5000,now,np.zeros(80000,dtype=np.int16),16000))
        assert Alert.query.count() == 0  # audio path must preserve the same quality rule


def test_default_startup_detects_legacy_schema(app, tmp_path):
    import sqlite3
    from backend.app import create_app
    from backend.tests.conftest import TestConfig
    database = tmp_path/'legacy.db'
    with sqlite3.connect(database) as conn:
        conn.execute('CREATE TABLE readings_classification (id TEXT PRIMARY KEY, wheeze_crackle_class TEXT)')
    class LegacyConfig(TestConfig):
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + str(database)
    # run_demo guards this, but README still documents python -m backend.app.
    with pytest.raises(RuntimeError, match='schema'):
        candidate = create_app(LegacyConfig,start_mqtt=False)
        candidate.extensions['audio_worker'].stop()


def test_mqtt_invalid_message_does_not_escape_callback(app):
    from types import SimpleNamespace
    from backend.ingestion.mqtt_subscriber import create_mqtt_client
    client = create_mqtt_client(app)
    msg = SimpleNamespace(topic=f'pneumacare/{DEVICE_ID}/ppg/raw', payload=b'[]')
    try:
        client.on_message(client,None,msg)
    except Exception as exc:
        pytest.fail(f'MQTT callback leaked {type(exc).__name__} instead of rejecting invalid message')
