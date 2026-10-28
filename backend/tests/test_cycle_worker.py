"""Compatibility of queued immutable PCM and the latest cycle pipeline."""
from threading import Event
from time import monotonic

import numpy as np
import pytest

from backend.analysis.cycle_segmenter import CycleDetectionResult, CycleSlice, detect_cycle_slices
from backend.ingestion import websocket_server as module
from backend.ingestion.audio_segment_buffer import Segment
from backend.ingestion.audio_worker import AudioJob, Cancelled
from backend.models.classification import ReadingClassification
from backend.models.respiratory_cycle import RespiratoryCycle


def test_cycle_detector_accepts_immutable_receiver_pcm():
    samples = np.zeros(80000, dtype='<i2')
    samples.flags.writeable = False
    assert detect_cycle_slices(samples, 16000).status == 'no_cycles'


def test_replaced_session_during_cycle_model_call_saves_no_result(app, monkeypatch):
    cancelled = Event()
    segment = Segment('latest-device', 1, 1700000000000, 1700000005000,
                      np.zeros(80000, dtype='<i2'), 16000)
    monkeypatch.setattr(module, 'detect_cycle_slices', lambda *_: CycleDetectionResult(
        status='detected', cycles=[CycleSlice(1, .5, 2.0, [0] * 24000, .1)]))
    def classify(**kwargs):
        cancelled.set()  # replacement/disconnect while HTTP call was in flight
        return {'segment_id': 'must-not-save'}
    monkeypatch.setattr(module, '_classify_input', classify)
    with app.app_context():
        with pytest.raises(Cancelled):
            module._handle_segment(segment, AudioJob(segment, cancelled, monotonic()))
        assert ReadingClassification.query.count() == 0
        assert RespiratoryCycle.query.count() == 0
