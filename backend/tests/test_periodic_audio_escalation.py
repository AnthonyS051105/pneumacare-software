"""Distinct same-channel recording windows, not channel copies, drive escalation."""
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from backend.ingestion import websocket_server as server
from backend.models import db
from backend.models.alert import Alert
from backend.tests.test_periodic_patient_alerts import capture  # noqa: F401
from backend.tests.test_patient_routes import _login_patient


def next_capture(base, cid, **changes):
    offset = (cid - 1) * 20000
    return replace(base, capture_id=cid, segment_start_ms=base.segment_start_ms+offset,
                   segment_end_ms=base.segment_end_ms+offset, **changes)


def test_three_distinct_abnormal_windows_escalate_to_urgent(app, capture):
    with app.app_context():
        for cid in (1, 2, 3, 4):
            server._handle_segment(next_capture(capture, cid))
        alerts = Alert.query.order_by(Alert.created_at).all()
        assert [a.level for a in alerts] == [1, 2, 3]
        trigger = alerts[-1].triggers[0]
        assert trigger['consecutive_abnormal'] == 3
        assert trigger['urgent_after'] == 3
        assert [e['capture_id'] for e in trigger['evidence']] == [1, 2, 3]
        assert trigger['classification_validated'] is False


def test_channels_in_same_window_never_multiply_persistence(app, capture):
    with app.app_context():
        for ch in (1, 2, 4):
            server._handle_segment(replace(capture, channel_id=ch))
        assert [a.level for a in Alert.query.all()] == [1]


def test_normal_breaks_abnormal_streak_without_clearing_open_alert(app, capture, monkeypatch):
    good = server._classify_input
    with app.app_context():
        server._handle_segment(capture)
        monkeypatch.setattr(server, '_classify_input', lambda **kw: {
            'classification': {'predicted_class':'normal', 'confidence':.8,
                               'probabilities':{'normal':.8,'abnormal':.2}}, 'model_version':'test-model'})
        server._handle_segment(next_capture(capture, 2))
        monkeypatch.setattr(server, '_classify_input', good)
        server._handle_segment(next_capture(capture, 3))
        assert [a.level for a in Alert.query.all()] == [1]
        server._handle_segment(next_capture(capture, 4))
        assert sorted(a.level for a in Alert.query.all()) == [1, 2]


@pytest.mark.parametrize('change', ['missing', 'stream', 'model', 'session', 'long_gap'])
def test_discontinuity_starts_new_streak(app, capture, monkeypatch, change):
    with app.app_context():
        server._handle_segment(capture)
        server._handle_segment(next_capture(capture, 2))
        third = next_capture(capture, 3)
        if change == 'missing':
            third = next_capture(capture, 4)
        elif change == 'stream':
            third = replace(third, capture_stream_id='new-boot')
        elif change == 'model':
            good = server._classify_input
            monkeypatch.setattr(server, '_classify_input', lambda **kw: {
                **good(**kw), 'model_version':'new-model'})
        elif change == 'session':
            # Internal session id changes on reconnect/receiver invalidation.
            third = replace(third, reception_session_id='new-connection')
        else:
            third = replace(third, segment_start_ms=third.segment_start_ms+120000,
                            segment_end_ms=third.segment_end_ms+120000)
        server._handle_segment(third)
        assert sorted(a.level for a in Alert.query.all()) == [1, 2]


def test_duplicate_and_old_capture_do_not_advance_streak(app, capture):
    with app.app_context():
        server._handle_segment(capture)
        server._handle_segment(capture)
        server._handle_segment(next_capture(capture, 2))
        server._handle_segment(capture)
        assert sorted(a.level for a in Alert.query.all()) == [1, 2]
        server._handle_segment(next_capture(capture, 3))
        assert sorted(a.level for a in Alert.query.all()) == [1, 2, 3]


def test_patient_api_marks_urgent_only_after_third_window(app, client, capture):
    _login_patient(client)
    for cid, expected in ((1, 'attention'), (2, 'attention'), (3, 'urgent')):
        with app.app_context():
            server._handle_segment(next_capture(capture, cid))
        assert client.get('/api/v1/patient/me/summary').get_json()['status_label'] == expected
    alerts = client.get('/api/v1/patient/me/alerts').get_json()
    red = next(a for a in alerts if a['level'] == 3)
    text = ' '.join(red['messages']).lower()
    assert 'berturut-turut' in text and '3' in text
    assert 'eksperimental' in text


def test_persistence_state_is_bounded_and_restored_from_database(app, capture):
    from backend.models.periodic_audio_state import PeriodicAudioState
    with app.app_context():
        server._handle_segment(capture)
        db.session.remove()  # new job/session, no in-memory counter shortcut
        server._handle_segment(next_capture(capture, 2))
        db.session.remove()
        server._handle_segment(next_capture(capture, 3))
        server._handle_segment(next_capture(capture, 4))
        state = PeriodicAudioState.query.one()
        assert state.consecutive_abnormal == 3 and len(state.evidence) == 3
        assert state.last_capture_id == 4
        assert sorted(a.level for a in Alert.query.all()) == [1, 2, 3]


def test_failed_window_breaks_persistence(app, capture, monkeypatch):
    from backend.inference.ml_service_client import MLServiceError
    good = server._classify_input
    with app.app_context():
        server._handle_segment(capture)
        monkeypatch.setattr(server, '_classify_input', lambda **kw: (_ for _ in ()).throw(MLServiceError('offline')))
        with pytest.raises(MLServiceError):
            server._handle_segment(next_capture(capture, 2))
        db.session.rollback()
        monkeypatch.setattr(server, '_classify_input', good)
        server._handle_segment(next_capture(capture, 3))
        assert [a.level for a in Alert.query.all()] == [1]


def test_thresholds_are_configurable_without_counting_microphone_copies(app, capture):
    app.config.update(AUDIO_PERIODIC_WARNING_CONSECUTIVE=3, AUDIO_PERIODIC_URGENT_CONSECUTIVE=4)
    with app.app_context():
        for cid in (1, 2):
            server._handle_segment(next_capture(capture, cid))
        assert [a.level for a in Alert.query.all()] == [1]
        server._handle_segment(next_capture(capture, 3))
        server._handle_segment(next_capture(capture, 4))
        assert sorted(a.level for a in Alert.query.all()) == [1, 2, 3]


def test_cancellation_before_commit_rolls_back_state_and_alert(app, capture, monkeypatch):
    from backend.ingestion.audio_worker import AudioJob, Cancelled
    from threading import Event
    from time import monotonic
    from backend.models.periodic_audio_state import PeriodicAudioState
    from backend.alerting import periodic_audio_alerts as service
    original = service._commit
    event = Event()
    def cancel(job):
        event.set()
        original(job)
    monkeypatch.setattr(service, '_commit', cancel)
    with app.app_context():
        with pytest.raises(Cancelled):
            server._handle_segment(capture, AudioJob(capture, event, monotonic()))
        db.session.rollback()
        assert Alert.query.count() == PeriodicAudioState.query.count() == 0


def test_receiver_reconnect_resets_same_boot_microphone_streak(app, capture):
    import json
    from backend.ingestion.websocket_server import AudioReceiver
    from backend.tests.test_periodic_audio import header
    class Sink:
        def submit_batch(self, segments, cancelled):
            self.segments = segments
            return True
    sink = Sink()
    receiver = AudioReceiver(app, sink)
    first = receiver.connection()
    def send(connection, cid):
        for offset in range(0, 32000, 4000):
            for ch in range(1, 5):
                h = header(cid, ch, offset)
                h.update(device_id=capture.device_id, capture_duration_ms=2000)
                raw = json.dumps(h).encode()
                assert connection.receive(b'PCA1'+len(raw).to_bytes(2,'little')+raw+b'\x01\x00'*4000)
        with app.app_context():
            for segment in sink.segments:
                server._handle_segment(segment)
    try:
        send(first, 1)
        send(first, 2)
        previous = sink.segments[0].reception_session_id
        first.close()
        second = receiver.connection()
        try:
            send(second, 3)
            assert sink.segments[0].reception_session_id != previous
            with app.app_context():
                assert sorted(a.level for a in Alert.query.all()) == [1, 2]
        finally:
            second.close()
    finally:
        first.close()
