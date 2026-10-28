import base64
import json
from threading import Event

import pytest

from backend.ingestion.websocket_server import AudioReceiver, _decode_pcm_base64


def message(seq=0, ch=1, stream='boot', sample_start=None, **extra):
    data = dict(device_id='test-device', channel_id=ch, seq_no=seq,
                timestamp_ms=1700000000000 + seq * 250, chunk_duration_ms=250,
                sample_rate=16000, bit_depth=16, pcm_base64=base64.b64encode(b'\x01\x00'*4000).decode())
    if stream is not None:
        data.update(stream_id=stream, sample_start=seq*4000 if sample_start is None else sample_start)
    data.update(extra)
    return json.dumps(data)


class Sink:
    def __init__(self):
        self.jobs = []
    def submit(self, segment, cancelled):
        self.jobs.append((segment, cancelled))
        return True


def test_receiver_assembles_four_channels_without_waiting_for_inference(app):
    sink = Sink()
    receiver = AudioReceiver(app, sink)
    conn = receiver.connection()
    for seq in range(20):
        for ch in range(1,5):
            assert conn.receive(message(seq, ch))
    assert len(sink.jobs) == 4
    assert all(len(s.pcm_samples) == 80000 for s,_ in sink.jobs)
    assert all(not s.pcm_samples.flags.writeable for s,_ in sink.jobs)
    conn.close()
    assert all(cancel.is_set() for _,cancel in sink.jobs)


def test_old_close_and_old_messages_cannot_erase_new_connection(app):
    sink = Sink()
    receiver = AudioReceiver(app, sink)
    old, new = receiver.connection(), receiver.connection()
    assert old.receive(message())
    assert new.receive(message())
    assert not old.receive(message(1))
    old.close()
    for seq in range(1,20):
        assert new.receive(message(seq))
    assert len(sink.jobs) == 1
    assert not sink.jobs[0][1].is_set()
    new.close()


def test_stream_change_resets_all_channels_and_cancels_queued_work(app):
    sink = Sink()
    conn = AudioReceiver(app, sink).connection()
    for seq in range(20):
        conn.receive(message(seq, 1))
    conn.receive(message(0,2))
    assert conn.receive(message(0,1,stream='new'))
    assert sink.jobs[0][1].is_set()
    for seq in range(1,20):
        conn.receive(message(seq,2,stream='new'))
    assert len(sink.jobs) == 1  # channel 2's old partial must be gone
    conn.close()


@pytest.mark.parametrize('raw', ['[]','null','{"pcm_base64":"private-do-not-log"}',
    message(pcm_base64='!'), message(pcm_base64='AA=='), message(sample_rate=True),
    message(bit_depth=24),message(channel_id=5),message(sample_start=-1),
    message(stream_id=None),message(chunk_duration_ms=50000)])
def test_invalid_frame_does_not_kill_receiver_or_print_payload(app, caplog, raw):
    conn = AudioReceiver(app, Sink()).connection()
    assert not conn.receive(raw)
    assert conn.receive(message())
    assert 'private-do-not-log' not in caplog.text
    conn.close()


def test_decode_signed_little_endian_and_reject_invalid():
    assert list(_decode_pcm_base64('AID/fwAA//8=')) == [-32768,32767,0,-1]
    with pytest.raises(ValueError):
        _decode_pcm_base64('!')


def test_real_receiver_continues_while_worker_is_blocked_and_rejects_full_queue(app, monkeypatch):
    from backend.ingestion.audio_worker import AudioWorker
    from backend.ingestion import websocket_server as module
    entered, release = Event(), Event()
    original = module.run_mock_inference
    def blocked(**kwargs):
        entered.set()
        assert release.wait(3)
        return original(**kwargs)
    monkeypatch.setattr(module, 'run_mock_inference', blocked)
    worker = AudioWorker(app, lambda job: module._handle_segment(job.segment, job), capacity=2)
    conn = AudioReceiver(app, worker).connection()
    try:
        for seq in range(20):
            conn.receive(message(seq, 1))
        assert entered.wait(2)
        for seq in range(20):
            for ch in (2,3,4):
                assert conn.receive(message(seq,ch))
        assert conn.chunks == 80
        assert worker.snapshot()['queued'] == 2
        assert worker.snapshot()['rejected'] == 1
        conn.close()  # active inference must not save stale-session results
        release.set()
        assert worker.wait_idle(3)
        from backend.models.classification import ReadingClassification
        with app.app_context():
            assert ReadingClassification.query.count() == 0
        assert worker.snapshot()['cancelled'] == 3
    finally:
        release.set()
        worker.stop(3)


def test_worker_rolls_back_failed_transaction_then_persists_next_job(app):
    from backend.ingestion.audio_worker import AudioWorker
    from backend.models import db
    from backend.models.device import Device
    from backend.ingestion import websocket_server as module
    def process(job):
        if job.segment == 'broken':
            db.session.add(Device(device_id='must-rollback'))
            db.session.flush()
            raise RuntimeError('fail after flush')
        module._handle_segment(job.segment, job)
    worker = AudioWorker(app, process, capacity=4)
    conn = AudioReceiver(app, worker).connection()
    try:
        worker.submit('broken', Event())
        for seq in range(20):
            conn.receive(message(seq))
        assert worker.wait_idle(3)
        with app.app_context():
            assert db.session.get(Device, 'must-rollback') is None
            from backend.models.classification import ReadingClassification
            reading = ReadingClassification.query.one()
            assert reading.device_id == 'test-device'
            assert reading.channel_id == 1
        assert worker.snapshot()['completed'] == 1
        assert worker.snapshot()['failed'] == 1
    finally:
        conn.close()
        worker.stop(3)


def test_pre_ntp_timestamp_uses_receive_time_without_latency_claim(app):
    from time import time
    sink = Sink()
    conn = AudioReceiver(app,sink).connection()
    before = int(time()*1000)-250
    for seq in range(20):
        conn.receive(message(seq,timestamp_ms=seq*250))
    segment = sink.jobs[0][0]
    assert before <= segment.segment_start_ms <= int(time()*1000)
    assert segment.segment_end_ms - segment.segment_start_ms == 5000
    conn.close()
