import pytest

from backend.inference import inference_service
from backend.inference.ml_service_client import MLServiceError


def _fake_classify(monkeypatch, result):
    monkeypatch.setattr(inference_service, "classify_segment", lambda **kwargs: result)


def _run(**overrides):
    kwargs = dict(
        pcm_samples=[0] * 100,
        source_sample_rate=16000,
        device_id="pneumacare-a1b2",
        channel_id=1,
        segment_start_ms=0,
        segment_end_ms=5000,
        model_version="test_v1",
        ml_service_url="http://ml.test",
        timeout_seconds=30,
    )
    kwargs.update(overrides)
    return inference_service.run_inference(**kwargs)


def test_output_schema(monkeypatch):
    classification = {
        "predicted_class": "normal",
        "confidence": 0.9,
        "probabilities": {"normal": 0.9, "abnormal": 0.1},
    }
    _fake_classify(monkeypatch, classification)

    result = _run()

    assert result["segment_id"]
    assert result["device_id"] == "pneumacare-a1b2"
    assert result["channel_id"] == 1
    assert result["segment_start_ms"] == 0
    assert result["segment_end_ms"] == 5000
    assert result["model_version"] == "test_v1"
    assert result["classification"] == classification


def test_class_names_are_normal_then_abnormal():
    assert inference_service.CLASS_NAMES == ["normal", "abnormal"]


def test_ml_service_error_propagates(monkeypatch):
    def boom(**kwargs):
        raise MLServiceError("service mati")

    monkeypatch.setattr(inference_service, "classify_segment", boom)

    with pytest.raises(MLServiceError):
        _run()
