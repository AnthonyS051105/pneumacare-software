import logging

import pytest

from backend.analysis.cycle_segmenter import CycleDetectionResult
from backend.ingestion import websocket_server as module
from backend.inference.ml_service_client import MLServiceError
from backend.tests.test_websocket_cycles import _segment


def test_failed_http_call_still_records_monotonic_stage_duration(app, monkeypatch, caplog):
    app.config['ML_SERVICE_URL'] = 'http://ml.test'
    def offline(**kwargs):
        raise MLServiceError('offline')
    monkeypatch.setattr(module, 'run_inference', offline)
    with caplog.at_level(logging.INFO), app.app_context():
        with pytest.raises(MLServiceError):
            module._classify_input([0],16000,'timing-device',2,0,5000)
    messages = [r.getMessage() for r in caplog.records]
    assert any('stage=classify_http' in m and 'status=error' in m
               and 'device=timing-device channel=2' in m and 'duration_ms=' in m
               for m in messages)


def test_complete_pipeline_logs_each_local_stage_with_identity(app, monkeypatch, caplog):
    monkeypatch.setattr(module, 'detect_cycle_slices', lambda *_: CycleDetectionResult('no_cycles'))
    with caplog.at_level(logging.INFO), app.app_context():
        module._handle_segment(_segment())
    messages = [r.getMessage() for r in caplog.records]
    for stage in ('registry','cycle_detection','classification','persist_cycle','trend','alert'):
        assert any(f'stage={stage} ' in m and 'status=ok' in m
                   and 'device=pneumacare-a1b2 channel=1' in m for m in messages)
