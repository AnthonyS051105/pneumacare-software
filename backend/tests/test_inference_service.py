import numpy as np
import torch

from ai_reference.model import RespiratoryMobileNet
from backend.inference.inference_service import CLASS_NAMES, run_inference


def _random_weight_model() -> RespiratoryMobileNet:
    model = RespiratoryMobileNet(num_classes=4)
    model.eval()
    return model


def test_run_inference_output_schema():
    model = _random_weight_model()
    n_samples = 16000 * 5
    pcm_samples = [int(1000 * np.sin(2 * np.pi * 300 * i / 16000)) for i in range(n_samples)]

    result = run_inference(
        model=model,
        pcm_samples=pcm_samples,
        source_sample_rate=16000,
        device_id="pneumacare-a1b2",
        channel_id=1,
        segment_start_ms=0,
        segment_end_ms=5000,
        model_version="test_v1",
    )

    assert result["device_id"] == "pneumacare-a1b2"
    assert result["channel_id"] == 1
    assert result["segment_start_ms"] == 0
    assert result["segment_end_ms"] == 5000
    assert result["model_version"] == "test_v1"
    assert "segment_id" in result

    wheeze_crackle = result["wheeze_crackle"]
    assert set(wheeze_crackle.keys()) == {"predicted_class", "confidence", "probabilities"}
    assert wheeze_crackle["predicted_class"] in CLASS_NAMES
    assert set(wheeze_crackle["probabilities"].keys()) == set(CLASS_NAMES)


def test_run_inference_confidence_is_fraction_not_percentage():
    """✅ Keputusan confidence (INTEGRATION_CONTRACT.md §4.1): fraksi 0-1, BUKAN
    persentase 0-100 seperti kode asli Nathanael."""
    model = _random_weight_model()
    pcm_samples = [0] * (16000 * 5)

    result = run_inference(
        model=model,
        pcm_samples=pcm_samples,
        source_sample_rate=16000,
        device_id="pneumacare-a1b2",
        channel_id=1,
        segment_start_ms=0,
        segment_end_ms=5000,
        model_version="test_v1",
    )

    wheeze_crackle = result["wheeze_crackle"]
    assert 0.0 <= wheeze_crackle["confidence"] <= 1.0
    for prob in wheeze_crackle["probabilities"].values():
        assert 0.0 <= prob <= 1.0


def test_run_inference_probabilities_sum_to_one():
    model = _random_weight_model()
    pcm_samples = [100] * (16000 * 5)

    result = run_inference(
        model=model,
        pcm_samples=pcm_samples,
        source_sample_rate=16000,
        device_id="pneumacare-a1b2",
        channel_id=1,
        segment_start_ms=0,
        segment_end_ms=5000,
        model_version="test_v1",
    )

    total = sum(result["wheeze_crackle"]["probabilities"].values())
    assert abs(total - 1.0) < 1e-5


def test_run_inference_predicted_class_matches_argmax_probability():
    model = _random_weight_model()
    pcm_samples = [50] * (16000 * 5)

    result = run_inference(
        model=model,
        pcm_samples=pcm_samples,
        source_sample_rate=16000,
        device_id="pneumacare-a1b2",
        channel_id=1,
        segment_start_ms=0,
        segment_end_ms=5000,
        model_version="test_v1",
    )

    wheeze_crackle = result["wheeze_crackle"]
    probabilities = wheeze_crackle["probabilities"]
    argmax_class = max(probabilities, key=probabilities.get)
    assert wheeze_crackle["predicted_class"] == argmax_class
    assert wheeze_crackle["confidence"] == probabilities[argmax_class]


def test_run_inference_class_order_matches_confirmed_order():
    # ✅ urutan dikonfirmasi Nathanael 12 Agt 2026 — none, crackle, wheeze, both
    assert CLASS_NAMES == ["none", "crackle", "wheeze", "both"]
