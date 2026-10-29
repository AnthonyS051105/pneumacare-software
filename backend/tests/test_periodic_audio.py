import json
import numpy as np
import pytest
from backend.ingestion.periodic_audio import PeriodicCaptureAssembler


def header(capture=1, ch=1, offset=0):
    return dict(device_id='test-device', channel_id=ch, seq_no=capture * 2 + offset // 4000,
                stream_id='boot', sample_start=capture * 160000 + offset,
                timestamp_ms=1700000000000 + capture * 10000 + offset // 16,
                sample_rate=16000, chunk_duration_ms=250, capture_id=capture,
                capture_duration_ms=500, capture_offset_samples=offset,
                capture_start_ms=1700000000000 + capture * 10000)


def test_four_channels_one_window_and_no_cross_window_concatenation():
    a = PeriodicCaptureAssembler(500)
    pcm = np.ones(4000, dtype='<i2')
    for capture in [1, 2]:
        result = None
        for ch in range(1, 5):
            for offset in [0, 4000]:
                result = a.add(header(capture, ch, offset), pcm)
        assert len(result) == 4
        assert all(len(s.pcm_samples) == 8000 and s.capture_id == capture for s in result)
        assert all(not s.pcm_samples.flags.writeable for s in result)
        with pytest.raises(ValueError):
            a.add(header(capture, 1, 4000), pcm)


def test_missing_prefix_and_gap_reject_window_but_next_window_recovers():
    a = PeriodicCaptureAssembler(500)
    pcm = np.ones(4000, dtype='<i2')
    with pytest.raises(ValueError):
        a.add(header(1, 1, 4000), pcm)
    assert a.add(header(2), pcm) is None
    with pytest.raises(ValueError):
        a.add(header(2, offset=0), pcm)
    assert a.add(header(3), pcm) is None


def test_incomplete_previous_window_is_discarded():
    a = PeriodicCaptureAssembler(500)
    pcm = np.ones(4000, dtype='<i2')
    a.add(header(), pcm)
    for ch in range(1, 5):
        for off in [0, 4000]:
            result = a.add(header(2, ch, off), pcm)
    assert len(result) == 4
    assert a.discarded_samples == 4000


@pytest.mark.parametrize('field,value', [('capture_duration_ms',10000),
    ('capture_id',True),('capture_offset_samples',-1),('sample_rate',8000)])
def test_invalid_capture_metadata(field, value):
    a = PeriodicCaptureAssembler(500)
    h = header();h[field] = value
    with pytest.raises(ValueError):a.add(h,np.ones(4000,dtype='<i2'))


def test_short_capture_saved_without_classification_or_alert(app, tmp_path):
    from backend.ingestion.websocket_server import _handle_segment
    from backend.ingestion.audio_segment_buffer import Segment
    from backend.models.classification import ReadingClassification
    from backend.models.alert import Alert
    import wave
    app.config['AUDIO_CAPTURE_DIRECTORY'] = str(tmp_path)
    app.config['AUDIO_SHORT_CAPTURE_INFERENCE_ENABLED'] = False
    s = Segment('test-device',1,1700000000000,1700000000500,
                np.ones(8000,dtype='<i2'),16000,capture_id=1)
    with app.app_context():
        _handle_segment(s)
        assert ReadingClassification.query.count() == 0
        assert Alert.query.count() == 0
    files = list(tmp_path.glob('*.wav'))
    assert len(files) == 1
    with wave.open(str(files[0])) as f:
        assert f.getnframes() == 8000 and f.getframerate() == 16000


def test_capture_archive_quota_is_bounded(tmp_path):
    from backend.ingestion.capture_archive import archive_capture
    from backend.ingestion.audio_segment_buffer import Segment
    s = Segment('test-device',1,0,500,np.ones(8000,dtype='<i2'),16000,capture_id=1)
    for _ in range(5):archive_capture(s,tmp_path,20000)
    assert sum(p.stat().st_size for p in tmp_path.iterdir()) <= 20000
    assert len(list(tmp_path.glob('*.wav'))) == 1


def test_batch_overload_rejects_all_four_channels(app):
    from backend.ingestion.audio_worker import AudioWorker
    from backend.ingestion.audio_segment_buffer import Segment
    from threading import Event
    worker = AudioWorker(app,lambda job:None,capacity=3)
    s = Segment('test-device',1,0,500,np.ones(8000,dtype='<i2'),16000,capture_id=1)
    assert not worker.submit_batch([s]*4,Event())
    assert worker.snapshot()['accepted'] == 0
    assert worker.snapshot()['rejected'] == 4
    worker.stop()


def test_real_websocket_ack_only_after_all_four_complete_channels(app, tmp_path):
    import base64
    from threading import Thread
    from werkzeug.serving import make_server
    from websockets.sync.client import connect
    app.config['AUDIO_CAPTURE_DIRECTORY'] = str(tmp_path)
    app.config['DEVICE_AUTH_TOKEN'] = 'test-only'
    server = make_server('127.0.0.1',0,app,threaded=True)
    thread = Thread(target=server.serve_forever,daemon=True);thread.start()
    try:
        with connect(f'ws://127.0.0.1:{server.server_port}/ws/audio',
                     additional_headers={'Authorization':'Bearer test-only'}) as ws:
            for capture in [1,2]:
                for offset in [0,4000]:
                    for ch in range(1,5):
                        h=header(capture,ch,offset)
                        h['pcm_base64']=base64.b64encode(b'\x01\x00'*4000).decode()
                        ws.send(json.dumps(h))
                        if ch==3 and offset==4000:
                            with pytest.raises(TimeoutError):ws.recv(timeout=.03)
                ack=json.loads(ws.recv(timeout=3))
                assert ack == dict(type='audio_capture_ack',capture_id=capture,status='accepted')
                assert app.extensions['audio_worker'].wait_idle(3)
            assert len(list(tmp_path.glob('*.wav'))) == 8
    finally:
        server.shutdown();server.server_close();thread.join(2)


def test_periodic_reconnect_never_joins_partial_or_allows_old_close_to_erase_new(app):
    from backend.ingestion.websocket_server import AudioReceiver
    import base64
    class BatchSink:
        def __init__(self):self.jobs=[]
        def submit_batch(self, segments, cancelled):
            self.jobs.extend(segments);return True
    sink=BatchSink();r=AudioReceiver(app,sink)
    def wire(capture,ch,off):
        h=header(capture,ch,off)
        h['pcm_base64']=base64.b64encode(b'\x01\x00'*4000).decode()
        return json.dumps(h)
    old=r.connection();new=r.connection()
    assert old.receive(wire(1,1,0))
    assert new.receive(wire(1,1,4000)) is False  # no prefix from old session
    old.close()
    assert not old.receive(wire(2,1,0))
    for off in [0,4000]:
        for ch in range(1,5):assert new.receive(wire(2,ch,off))
    assert len(sink.jobs)==4
    assert new.capture_ack['status']=='accepted'
    assert new.gaps==0
    new.close()


def test_default_two_second_capture_binary_ack_and_archive(app, tmp_path):
    """32 paced-shape frames; no ACK/job until all four exact 2s channels."""
    from backend.ingestion.websocket_server import AudioReceiver
    class Sink:
        def __init__(self): self.jobs=[]
        def submit_batch(self, segments, cancelled):
            self.jobs.extend(segments); return True
    assert app.config['AUDIO_PERIODIC_CAPTURE_MS'] == 2000
    sink=Sink(); connection=AudioReceiver(app,sink).connection()
    for offset in range(0,32000,4000):
        for ch in range(1,5):
            h=header(1,ch,offset)
            h['capture_duration_ms']=2000
            h['seq_no']=offset//4000
            raw=json.dumps(h).encode()
            assert connection.receive(b'PCA1'+len(raw).to_bytes(2,'little')+raw+b'\x01\x00'*4000)
            if (offset,ch)!=(28000,4):
                assert connection.capture_ack is None and not sink.jobs
    assert connection.capture_ack['status']=='accepted'
    assert len(sink.jobs)==4
    assert all(len(s.pcm_samples)==32000 and s.segment_end_ms-s.segment_start_ms==2000
               and not s.pcm_samples.flags.writeable for s in sink.jobs)
    app.config['AUDIO_CAPTURE_DIRECTORY']=str(tmp_path)
    from backend.ingestion.websocket_server import _handle_segment
    import wave
    with app.app_context():
        for segment in sink.jobs: _handle_segment(segment)
    for path in tmp_path.glob('*.wav'):
        with wave.open(str(path)) as wav: assert wav.getnframes()==32000
    assert len(list(tmp_path.glob('*.wav')))==4
    connection.close()


def test_two_second_capture_gap_never_produces_partial_result():
    a=PeriodicCaptureAssembler(2000)
    pcm=np.ones(4000,dtype='<i2')
    def h(off):
        msg=header(1,1,off); msg['capture_duration_ms']=2000; return msg
    assert a.add(h(0),pcm) is None
    broken=h(4000); broken['sample_start']+=256
    with pytest.raises(ValueError): a.add(broken,pcm)
    assert not a.segments and not a.offsets


def test_legacy_500ms_and_two_seconds_are_supported_but_never_mixed(app):
    from backend.ingestion.websocket_server import AudioReceiver
    import base64
    class Sink:
        def __init__(self): self.jobs=[]
        def submit_batch(self, segments, cancelled): self.jobs.extend(segments); return True
    sink=Sink(); c=AudioReceiver(app,sink).connection()
    def send(capture,ch,off,duration):
        h=header(capture,ch,off); h['capture_duration_ms']=duration
        h['pcm_base64']=base64.b64encode(b'\x01\x00'*4000).decode()
        return c.receive(json.dumps(h))
    for off in [0,4000]:
        for ch in range(1,5): assert send(1,ch,off,500)
    assert len(sink.jobs)==4
    assert send(2,1,0,2000)
    assert not send(2,2,0,500)  # format change invalidates this entire ID
    assert c.capture_ack['status']=='rejected'
    for off in range(0,32000,4000):
        for ch in range(1,5): assert send(3,ch,off,2000)
    assert len(sink.jobs)==8
    assert all(len(s.pcm_samples)==32000 and s.capture_id==3 for s in sink.jobs[4:])
    c.close()


def test_two_seconds_reconnect_discards_all_old_channel_prefixes(app):
    from backend.ingestion.websocket_server import AudioReceiver
    import base64
    class Sink:
        def __init__(self):self.jobs=[]
        def submit_batch(self, segments, cancelled):self.jobs.extend(segments);return True
    sink=Sink();r=AudioReceiver(app,sink)
    old,new=r.connection(),r.connection()
    def send(connection,cid,ch,off):
        h=header(cid,ch,off);h['capture_duration_ms']=2000
        h['pcm_base64']=base64.b64encode(b'\x02\x00'*4000).decode()
        return connection.receive(json.dumps(h))
    for ch in range(1,5):assert send(old,1,ch,0)
    assert not send(new,1,1,4000)
    old.close()
    for off in range(0,32000,4000):
        for ch in range(1,5):assert send(new,2,ch,off)
    assert len(sink.jobs)==4 and all(s.capture_id==2 for s in sink.jobs)
    assert old.cancelled.is_set()
    new.close()


def test_disconnect_logs_discarded_periodic_samples(app, caplog):
    from backend.ingestion.websocket_server import AudioReceiver
    import base64,logging
    class Sink:
        def submit_batch(self, segments, cancelled):raise AssertionError('partial submitted')
    c=AudioReceiver(app,Sink()).connection()
    for ch in range(1,5):
        h=header(1,ch,0);h['capture_duration_ms']=2000
        h['pcm_base64']=base64.b64encode(b'\x01\x00'*4000).decode()
        assert c.receive(json.dumps(h))
    with caplog.at_level(logging.INFO):c.close()
    assert 'discarded_samples=16000' in caplog.text


def test_two_second_windows_preserve_each_channel_and_frame_order():
    a=PeriodicCaptureAssembler(2000)
    for cid in [1,2]:
        for index,off in enumerate(range(0,32000,4000)):
            for ch in range(1,5):
                h=header(cid,ch,off);h['capture_duration_ms']=2000
                result=a.add(h,np.full(4000,cid*1000+ch*10+index,dtype='<i2'))
        for s in result:
            expected=np.repeat(np.arange(8,dtype='<i2')+cid*1000+s.channel_id*10,4000)
            np.testing.assert_array_equal(s.pcm_samples,expected)
            assert s.capture_id==cid
