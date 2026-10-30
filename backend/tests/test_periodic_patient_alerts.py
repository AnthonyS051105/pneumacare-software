"""Patient notifications from short audio are explicit prototype review requests."""
import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from threading import Event
from time import monotonic

import numpy as np
import pytest

from backend.ingestion import websocket_server as server
from backend.ingestion.audio_segment_buffer import Segment
from backend.ingestion.audio_worker import AudioJob, Cancelled
from backend.models import db
from backend.models.alert import Alert
from backend.models.classification import ReadingClassification
from backend.tests.test_patient_routes import _seed_patient_with_device, _login_patient


@pytest.fixture
def capture(app, tmp_path, monkeypatch):
    _seed_patient_with_device(app)
    app.config.update(AUDIO_CAPTURE_DIRECTORY=str(tmp_path), ML_SERVICE_URL='http://test',
                      AUDIO_PERIODIC_SHADOW_INFERENCE_ENABLED=False,
                      AUDIO_PERIODIC_PATIENT_ALERTS_ENABLED=True)
    def predict(**kw):
        return {'classification': {'predicted_class': 'abnormal', 'confidence': .8,
                'probabilities': {'normal': .2, 'abnormal': .8}}, 'model_version': 'test-model'}
    monkeypatch.setattr(server, '_classify_input', predict)
    return Segment('pneumacare-a1b2', 1, 1700000000000, 1700000002000,
                   np.ones(32000, dtype='<i2'), 16000, capture_id=1, capture_stream_id='boot')


def test_patient_alert_mode_runs_inference_and_creates_informational_alert(app, capture, tmp_path):
    with app.app_context():
        server._handle_segment(capture)
        alert = Alert.query.one()
        assert alert.level == 1 and alert.patient_id == 'patient-1'
        trigger = alert.triggers[0]
        assert trigger['type'] == 'periodic_audio_review'
        assert trigger['channel_id'] == 1 and trigger['capture_id'] == 1
        assert trigger['model_version'] == 'test-model'
        assert trigger['classification_validated'] is False
        assert ReadingClassification.query.count() == 0
    metadata = json.loads(next(tmp_path.glob('*.json')).read_text())
    assert metadata['inference_status'] == 'completed'
    assert metadata['patient_notification']['status'] == 'created'
    assert metadata['patient_notification']['alert_id'] == alert.id


def test_patient_sees_explicit_prototype_message_and_attention(app, client, capture):
    with app.app_context():
        server._handle_segment(capture)
    _login_patient(client)
    body = client.get('/api/v1/patient/me/alerts').get_json()
    assert len(body) == 1 and body[0]['level'] == 1
    text = ' '.join(body[0]['messages']).lower()
    assert 'eksperimental' in text and '2 detik' in text
    assert 'diagnosis' in text
    assert client.get('/api/v1/patient/me/summary').get_json()['status_label'] == 'attention'


@pytest.mark.parametrize('case', ['normal', 'simulation', '500ms', 'no_stream', 'disabled', 'unpaired'])
def test_no_patient_notification_for_ineligible_result(app, capture, monkeypatch, case):
    if case == 'normal':
        monkeypatch.setattr(server, '_classify_input', lambda **kw: {
            'classification': {'predicted_class': 'normal', 'confidence': .8,
                               'probabilities': {'normal': .8, 'abnormal': .2}},
            'model_version': 'test-model'})
    elif case == 'simulation':
        capture = replace(capture, channel_id=3, data_origin='simulated', source_channel_id=4)
    elif case == '500ms':
        capture = replace(capture, segment_end_ms=capture.segment_start_ms + 500,
                          pcm_samples=capture.pcm_samples[:8000])
    elif case == 'no_stream':
        capture = replace(capture, capture_stream_id=None)
    elif case == 'disabled':
        app.config['AUDIO_PERIODIC_PATIENT_ALERTS_ENABLED'] = False
        app.config['AUDIO_PERIODIC_SHADOW_INFERENCE_ENABLED'] = True
    else:
        capture = replace(capture, device_id='unpaired')
    with app.app_context():
        server._handle_segment(capture)
        assert Alert.query.count() == 0


def test_missing_real_model_never_uses_mock_for_notification(app, capture, monkeypatch):
    app.config['ML_SERVICE_URL'] = ''
    monkeypatch.setattr(server, '_classify_input', lambda **kw: pytest.fail('mock forbidden'))
    with app.app_context():
        server._handle_segment(capture)
        assert Alert.query.count() == 0


def test_cancelled_model_call_never_creates_notification(app, capture, monkeypatch):
    cancelled = Event()
    job = AudioJob(capture, cancelled, monotonic())
    def predict(**kw):
        cancelled.set()
        return {'classification': {'predicted_class': 'abnormal'}, 'model_version': 'test'}
    monkeypatch.setattr(server, '_classify_input', predict)
    with app.app_context(), pytest.raises(Cancelled):
        server._handle_segment(capture, job)
    with app.app_context():
        assert Alert.query.count() == 0


def test_repeated_capture_and_open_condition_do_not_flood_patient(app, capture):
    with app.app_context():
        server._handle_segment(capture)
        first = Alert.query.one()
        server._handle_segment(capture)
        server._handle_segment(replace(capture, channel_id=2))
        server._handle_segment(replace(capture, capture_id=2))
        assert Alert.query.count() == 1
        first.acknowledged = True
        db.session.commit()
        server._handle_segment(replace(capture, capture_id=3))
        assert Alert.query.count() == 1  # cooldown after acknowledgment
        first.created_at = datetime.now(timezone.utc) - timedelta(seconds=1000)
        db.session.commit()
        server._handle_segment(capture)  # old capture remains idempotent after cooldown
        assert Alert.query.count() == 1
        server._handle_segment(replace(capture, capture_id=4))
        assert Alert.query.count() == 2


def test_review_notification_never_hides_existing_urgent_alert(app, client, capture):
    with app.app_context():
        db.session.add(Alert(id='existing-urgent', device_id=capture.device_id, patient_id='patient-1',
                            level=3, triggers=[], created_at=datetime.now(timezone.utc), acknowledged=False))
        db.session.commit()
        server._handle_segment(capture)
        assert Alert.query.count() == 2
    _login_patient(client)
    assert client.get('/api/v1/patient/me/summary').get_json()['status_label'] == 'urgent'


def test_failed_model_creates_no_notification_and_next_job_recovers(app, capture, monkeypatch):
    from backend.inference.ml_service_client import MLServiceError
    from backend.ingestion.audio_worker import AudioWorker
    good = server._classify_input
    def classify(**kw):
        if kw['channel_id'] == 1:
            raise MLServiceError('service unavailable')
        return good(**kw)
    monkeypatch.setattr(server, '_classify_input', classify)
    worker = AudioWorker(app, lambda job: server._handle_segment(job.segment, job))
    try:
        assert worker.submit_batch([capture, replace(capture, channel_id=2)], Event())
        assert worker.wait_idle(5)
        assert worker.snapshot()['failed'] == worker.snapshot()['completed'] == 1
        with app.app_context():
            assert Alert.query.one().triggers[0]['channel_id'] == 2
    finally:
        worker.stop()
