"""Binary PCM and legacy JSON use identical continuity and session rules."""
import base64
import json
import struct

import pytest

from backend.ingestion.websocket_server import AudioReceiver
from backend.tests.test_audio_receiver import Sink, message


def binary_message(seq=0, ch=1, **extra):
    header = json.loads(message(seq, ch, **extra))
    pcm = base64.b64decode(header.pop('pcm_base64'))
    encoded = json.dumps(header, separators=(',', ':')).encode()
    return b'PCA1' + struct.pack('<H', len(encoded)) + encoded + pcm


def test_binary_four_channels_match_json_and_preserve_signed_pcm(app):
    sink = Sink()
    conn = AudioReceiver(app, sink).connection()
    for seq in range(20):
        for channel in range(1, 5):
            assert conn.receive(binary_message(seq, channel))
    assert len(sink.jobs) == 4
    assert all(len(s.pcm_samples) == 80000 for s, _ in sink.jobs)
    assert all(s.pcm_samples[0] == 1 and not s.pcm_samples.flags.writeable for s, _ in sink.jobs)
    conn.close()


def test_binary_gap_discards_partial_and_accepts_legacy_afterwards(app):
    sink = Sink()
    conn = AudioReceiver(app, sink).connection()
    for seq in range(10):
        assert conn.receive(binary_message(seq))
    for seq in range(11, 30):
        assert conn.receive(binary_message(seq))
    assert not sink.jobs
    assert conn.receive(message(30))
    assert len(sink.jobs) == 1
    assert conn.gaps == 1
    conn.close()


@pytest.mark.parametrize('raw', [b'', b'PCA1', b'XXXX\x00\x00',
    b'PCA1\xff\xff{}', b'PCA1\x02\x00[]', b'PCA1\x01\x00\xff',
    binary_message()[:-1], binary_message() + b'\x00\x00'],
    ids=['empty','truncated','magic','length','array','utf8','odd-pcm','wrong-count'])
def test_invalid_binary_resets_partial_and_next_frame_works(app, raw):
    sink = Sink()
    conn = AudioReceiver(app, sink).connection()
    assert conn.receive(binary_message())
    assert not conn.receive(raw)
    for seq in range(1, 20):
        assert conn.receive(binary_message(seq))
    assert not sink.jobs
    conn.close()


def test_fifty_ms_binary_chunks_still_form_complete_five_second_segments(app):
    sink = Sink()
    conn = AudioReceiver(app, sink).connection()
    for seq in range(100):
        for channel in range(1, 5):
            h = json.loads(message(seq, channel))
            h.pop('pcm_base64')
            h.update(chunk_duration_ms=50, sample_start=seq * 800,
                     timestamp_ms=1700000000000 + seq * 50)
            encoded = json.dumps(h).encode()
            raw = b'PCA1' + struct.pack('<H', len(encoded)) + encoded + b'\x01\x00' * 800
            assert conn.receive(raw)
    assert len(sink.jobs) == 4
    assert all(len(s.pcm_samples) == 80000 for s, _ in sink.jobs)
    conn.close()
