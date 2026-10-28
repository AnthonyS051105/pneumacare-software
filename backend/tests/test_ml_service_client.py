from unittest.mock import Mock

import pytest

from backend.inference import ml_service_client


def _mock_response(monkeypatch, payload):
    response = Mock()
    response.json.return_value = payload
    response.raise_for_status.return_value = None
    monkeypatch.setattr(ml_service_client.requests, "post", lambda *args, **kwargs: response)
    return response


def test_class_zero_is_normal(monkeypatch):
    _mock_response(
        monkeypatch,
        {"class": 0, "confidence": 0.9, "probabilities": [0.9, 0.1]},
    )

    result = ml_service_client.classify_segment([0] * 100, 16000, "http://ml.test", 30)

    assert result == {
        "predicted_class": "normal",
        "confidence": 0.9,
        "probabilities": {"normal": 0.9, "abnormal": 0.1},
    }


def test_class_one_is_abnormal(monkeypatch):
    _mock_response(
        monkeypatch,
        {"class": 1, "confidence": 0.8, "probabilities": [0.2, 0.8]},
    )

    result = ml_service_client.classify_segment([0] * 100, 16000, "http://ml.test", 30)

    assert result["predicted_class"] == "abnormal"
    assert result["confidence"] == 0.8


def test_invalid_payload_raises_ml_service_error(monkeypatch):
    _mock_response(
        monkeypatch,
        {"class": 2, "confidence": 0.9, "probabilities": [0.5, 0.5]},
    )

    with pytest.raises(ml_service_client.MLServiceError):
        ml_service_client.classify_segment([0] * 100, 16000, "http://ml.test", 30)


def test_pcm_to_wav_has_riff_header():
    data = ml_service_client._pcm_to_wav_bytes([0, 1, -1], 16000)

    assert data[:4] == b"RIFF"
    assert data[8:12] == b"WAVE"


@pytest.mark.parametrize('payload', [
    {'class': True, 'confidence': .8, 'probabilities': [.2, .8]},
    {'class': 0.0, 'confidence': .8, 'probabilities': [.8, .2]},
    {'class': 0, 'confidence': True, 'probabilities': [.8, .2]},
    {'class': 0, 'confidence': float('nan'), 'probabilities': [.8, .2]},
    {'class': 0, 'confidence': float('inf'), 'probabilities': [.8, .2]},
    {'class': 0, 'confidence': -.1, 'probabilities': [.8, .2]},
    {'class': 0, 'confidence': 80, 'probabilities': [.8, .2]},
    {'class': 0, 'confidence': .8, 'probabilities': [True, 0]},
    {'class': 0, 'confidence': .8, 'probabilities': [float('nan'), .2]},
    {'class': 0, 'confidence': .8, 'probabilities': [float('inf'), .2]},
    {'class': 0, 'confidence': .8, 'probabilities': [-.1, 1.1]},
    {'class': 0, 'confidence': .8, 'probabilities': [.8, .8]},
    {'class': 0, 'confidence': .8, 'probabilities': [.2, .8]},
    {'class': 1, 'confidence': .7, 'probabilities': [.2, .8]},
    {'class': 1, 'confidence': .5, 'probabilities': [.5, .5]},
])
def test_rejects_invalid_probability_contract(monkeypatch, payload):
    _mock_response(monkeypatch, payload)
    with pytest.raises(ml_service_client.MLServiceError):
        ml_service_client.classify_segment([0]*100, 16000, 'http://ml.test', 30)


def test_accepts_float32_roundoff_without_changing_values(monkeypatch):
    _mock_response(monkeypatch, {'class': 0, 'confidence': .9000001,
                                'probabilities': [.9000001, .10000001]})
    result = ml_service_client.classify_segment([0]*100, 16000, 'http://ml.test', 30)
    assert result['probabilities'] == {'normal': .9000001, 'abnormal': .10000001}
    assert result['confidence'] == .9000001
