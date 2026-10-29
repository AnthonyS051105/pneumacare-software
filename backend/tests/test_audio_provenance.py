"""A duplicate microphone tests transport, never a second observation."""
import json
from dataclasses import replace

import numpy as np
import pytest

from backend.ingestion.audio_segment_buffer import Segment
from backend.ingestion.periodic_audio import PeriodicCaptureAssembler
from backend.ingestion.websocket_server import AudioReceiver, _handle_segment
from backend.tests.test_periodic_audio import header


def window(assembler, change=None):
    for off in (0, 4000):
        for ch in range(1, 5):
            h = header(1, ch, off)
            h.update(data_origin='simulated' if ch == 3 else 'measured',
                     source_channel_id=4 if ch == 3 else ch)
            if change:
                change(h)
            result = assembler.add(h, np.full(4000, 4 if ch == 3 else ch, dtype='<i2'))
    return result


def test_periodic_preserves_provenance_on_immutable_segments():
    result = window(PeriodicCaptureAssembler(500))
    assert [s.data_origin for s in result] == ['measured', 'measured', 'simulated', 'measured']
    assert result[2].source_channel_id == 4
    np.testing.assert_array_equal(result[2].pcm_samples, result[3].pcm_samples)
    assert not result[2].pcm_samples.flags.writeable


def test_provenance_change_mid_window_invalidates_all_channels():
    def change(h):
        if h['channel_id'] == 3 and h['capture_offset_samples'] == 4000:
            h.update(data_origin='measured', source_channel_id=3)
    a = PeriodicCaptureAssembler(500)
    with pytest.raises(ValueError):
        window(a, change)
    assert not a.segments and not a.offsets


@pytest.mark.parametrize('extra', [
    {'data_origin': 'simulated'}, {'source_channel_id': 4},
    {'data_origin': 'measured', 'source_channel_id': 4},
    {'data_origin': 'simulated', 'source_channel_id': 3},
    {'data_origin': 'simulated', 'source_channel_id': True},
    {'data_origin': 'unknown', 'source_channel_id': 4},
])
def test_bad_provenance_rejected_before_enqueue(app, extra):
    class Sink:
        def submit_batch(self, *args):
            raise AssertionError('bad provenance queued')
    c = AudioReceiver(app, Sink()).connection()
    h = header(ch=3)
    h.update(extra)
    raw = json.dumps(h).encode()
    assert not c.receive(b'PCA1' + len(raw).to_bytes(2, 'little') + raw + b'\x01\x00' * 4000)


def test_synthetic_bypasses_inference_and_clinical_storage_even_with_legacy_gate(app, tmp_path, monkeypatch):
    from backend.ingestion import websocket_server as server
    from backend.models.classification import ReadingClassification
    from backend.models.alert import Alert
    app.config.update(AUDIO_CAPTURE_DIRECTORY=str(tmp_path),
                      AUDIO_SHORT_CAPTURE_INFERENCE_ENABLED=True)
    monkeypatch.setattr(server, '_classify_input', lambda **kw: pytest.fail('synthetic inference'))
    segment = Segment('test-device', 3, 1700000000000, 1700000000500,
                      np.ones(8000, dtype='<i2'), 16000, capture_id=1,
                      data_origin='simulated', source_channel_id=4)
    with app.app_context():
        _handle_segment(segment)
        assert ReadingClassification.query.count() == Alert.query.count() == 0
    meta = json.loads(next(tmp_path.glob('*.json')).read_text())
    assert meta['data_origin'] == 'simulated' and meta['source_channel_id'] == 4
    assert meta['alert_eligible'] is False


def test_shadow_predicts_measured_only_without_clinical_side_effects(app, tmp_path, monkeypatch):
    from backend.ingestion import websocket_server as server
    from backend.models.classification import ReadingClassification
    from backend.models.alert import Alert
    calls = []
    def predict(**kw):
        calls.append(kw['channel_id'])
        return {'classification': {'predicted_class': 'abnormal', 'confidence': .8,
                'probabilities': {'normal': .2, 'abnormal': .8}}, 'model_version': 'test-real-interface'}
    monkeypatch.setattr(server, '_classify_input', predict)
    app.config.update(AUDIO_CAPTURE_DIRECTORY=str(tmp_path), ML_SERVICE_URL='http://test',
                      AUDIO_PERIODIC_SHADOW_INFERENCE_ENABLED=True)
    base = Segment('test-device', 1, 1700000000000, 1700000002000,
                   np.ones(32000, dtype='<i2'), 16000, capture_id=1)
    with app.app_context():
        for ch in range(1, 5):
            _handle_segment(replace(base, channel_id=ch, data_origin='simulated' if ch == 3 else 'measured',
                                    source_channel_id=4 if ch == 3 else ch))
        assert ReadingClassification.query.count() == Alert.query.count() == 0
    assert calls == [1, 2, 4]
    meta = [json.loads(p.read_text()) for p in tmp_path.glob('*.json')]
    assert sum(m.get('experimental_classification') is not None for m in meta) == 3
    assert all(m['alert_eligible'] is False for m in meta)
    assert all(m['review_signal']['type'] == 'experimental_audio_abnormal'
               for m in meta if m['channel_id'] != 3)


def test_shadow_without_real_model_does_not_fall_back_to_mock(app, tmp_path, monkeypatch):
    from backend.ingestion import websocket_server as server
    monkeypatch.setattr(server, '_classify_input', lambda **kw: pytest.fail('mock forbidden'))
    app.config.update(AUDIO_CAPTURE_DIRECTORY=str(tmp_path), ML_SERVICE_URL='',
                      AUDIO_PERIODIC_SHADOW_INFERENCE_ENABLED=True)
    s = Segment('test-device', 1, 0, 2000, np.ones(32000, dtype='<i2'), 16000, capture_id=1)
    with app.app_context():
        _handle_segment(s)
    meta = json.loads(next(tmp_path.glob('*.json')).read_text())
    assert meta['inference_status'] == 'unavailable'


def test_copy_must_match_its_measured_source():
    def change(h):
        if h['channel_id'] == 3:
            h['source_channel_id'] = 2  # supplied PCM is actually copied from 4
    with pytest.raises(ValueError):
        window(PeriodicCaptureAssembler(500), change)


def test_simulation_chain_is_rejected():
    def change(h):
        if h['channel_id'] == 4:
            h.update(data_origin='simulated', source_channel_id=3)
    with pytest.raises(ValueError):
        window(PeriodicCaptureAssembler(500), change)


def test_cancel_during_shadow_http_never_publishes_prediction(app, tmp_path, monkeypatch):
    from backend.ingestion import websocket_server as server
    from backend.ingestion.audio_worker import AudioJob, Cancelled
    from threading import Event
    from time import monotonic
    s = Segment('test-device', 1, 0, 2000, np.ones(32000, dtype='<i2'), 16000, capture_id=1)
    event = Event()
    job = AudioJob(s, event, monotonic())
    def classify(**kw):
        event.set()
        return {'classification': {'predicted_class': 'abnormal'}, 'model_version': 'test'}
    monkeypatch.setattr(server, '_classify_input', classify)
    app.config.update(AUDIO_CAPTURE_DIRECTORY=str(tmp_path), ML_SERVICE_URL='http://test',
                      AUDIO_PERIODIC_SHADOW_INFERENCE_ENABLED=True)
    with app.app_context(), pytest.raises(Cancelled):
        _handle_segment(s, job)
    meta = json.loads(next(tmp_path.glob('*.json')).read_text())
    assert meta['inference_status'] == 'cancelled'
    assert meta.get('experimental_classification') is None


def test_result_annotation_retains_quota_and_does_not_leave_temporary_files(tmp_path):
    from backend.ingestion.capture_archive import archive_capture, annotate_capture
    s = Segment('test-device', 1, 0, 500, np.ones(8000, dtype='<i2'), 16000, capture_id=1)
    first = archive_capture(s, tmp_path, 40000)
    last = archive_capture(s, tmp_path, 40000)
    annotate_capture(last, {'extra': 'x' * 10000}, 40000)
    assert sum(p.stat().st_size for p in tmp_path.iterdir()) <= 40000
    assert last.exists() and not list(tmp_path.glob('*.tmp'))


def test_worker_log_identifies_capture_and_boot_for_reliable_cohort(app, tmp_path, caplog):
    import logging
    from threading import Event
    app.config['AUDIO_CAPTURE_DIRECTORY'] = str(tmp_path)
    s = Segment('test-device', 1, 0, 2000, np.ones(32000, dtype='<i2'), 16000,
                capture_id=42, capture_stream_id='unitboot')
    with caplog.at_level(logging.INFO):
        worker = app.extensions['audio_worker']
        assert worker.submit(s, Event())
        assert worker.wait_idle(3)
        assert worker.stop()  # join also waits for the final log after idle notification
    records = [r.message for r in caplog.records if r.message.startswith('audio_job status=completed')]
    assert len(records) == 1
    assert 'capture=42 stream=unitboot' in records[0]


@pytest.mark.parametrize('binary', [True, False])
def test_sixty_four_125ms_chunks_form_one_two_second_window(app, binary):
    import base64
    class Sink:
        def __init__(self): self.jobs = []
        def submit_batch(self, segments, cancelled):
            self.jobs.extend(segments)
            return True
    sink = Sink()
    c = AudioReceiver(app, sink).connection()
    for off in range(0, 32000, 2000):
        for ch in range(1, 5):
            h = header(ch=ch, offset=off)
            h.update(chunk_duration_ms=125, capture_duration_ms=2000, seq_no=off//2000)
            pcm = np.full(2000, 4 if ch == 3 else ch, dtype='<i2').tobytes()
            if ch == 3:
                h.update(data_origin='simulated', source_channel_id=4)
            if binary:
                encoded = json.dumps(h).encode()
                wire = b'PCA1' + len(encoded).to_bytes(2, 'little') + encoded + pcm
            else:
                h['pcm_base64'] = base64.b64encode(pcm).decode()
                wire = json.dumps(h)
            assert c.receive(wire)
            if (off, ch) != (30000, 4):
                assert c.capture_ack is None and not sink.jobs
    assert len(sink.jobs) == 4 and c.capture_ack['status'] == 'accepted'
    for s in sink.jobs:
        assert len(s.pcm_samples) == 32000
        assert s.segment_end_ms - s.segment_start_ms == 2000
        np.testing.assert_array_equal(s.pcm_samples, np.full(32000, 4 if s.channel_id == 3 else s.channel_id))
    c.close()
