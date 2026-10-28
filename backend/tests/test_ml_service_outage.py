import pytest

from backend.analysis.cycle_segmenter import CycleDetectionResult
from backend.ingestion import websocket_server as module
from backend.inference.ml_service_client import MLServiceError
from backend.models.classification import ReadingClassification
from backend.models.respiratory_cycle import RespiratoryCycle
from backend.tests.test_websocket_cycles import _segment


def test_configured_service_failure_does_not_create_synthetic_results(app, monkeypatch):
    app.config['ML_SERVICE_URL'] = 'http://127.0.0.1:8000'
    monkeypatch.setattr(module, 'detect_cycle_slices', lambda *args: CycleDetectionResult('no_cycles'))
    def unavailable(**kwargs):
        raise MLServiceError('service offline')
    monkeypatch.setattr(module, 'run_inference', unavailable)
    with app.app_context():
        with pytest.raises(MLServiceError):
            module._handle_segment(_segment())
        assert ReadingClassification.query.count() == 0
        assert RespiratoryCycle.query.count() == 0


def test_explicit_mock_mode_still_supports_synthetic_testing(app):
    app.config['ML_SERVICE_URL'] = ''
    with app.app_context():
        result = module._classify_input([0]*80000, 16000, 'test', 1, 0, 5000)
    assert result['model_version'] == 'mock_v3'
