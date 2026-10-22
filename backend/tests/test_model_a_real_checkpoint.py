"""Integrasi dengan checkpoint Model A ASLI dari tim model (bukan checkpoint sintetis).

Dilewati otomatis bila file checkpoint tidak ada di environment ini, supaya suite tetap
bisa jalan di mesin tanpa artifact model. Tes ini memastikan rantai load checkpoint ->
preprocessing (resample + mel-spectrogram dari ai_reference) -> forward -> skema output
sesuai INTEGRATION_CONTRACT.md §4.1 benar-benar tersambung, bukan hanya diuji dengan mock.
"""

import math
import os

import pytest

from backend.config import Config

CHECKPOINT = Config.MODEL_A_CHECKPOINT_PATH

pytestmark = pytest.mark.skipif(
    not CHECKPOINT or not os.path.exists(CHECKPOINT),
    reason="checkpoint Model A asli tidak tersedia di environment ini",
)


@pytest.fixture(scope="module")
def real_model():
    from backend.inference.model_loader import load_model

    return load_model(CHECKPOINT)


def _tone_pcm(seconds: float, sample_rate: int) -> list[int]:
    return [int(3000 * math.sin(2 * math.pi * 400 * i / sample_rate)) for i in range(int(seconds * sample_rate))]


def test_real_checkpoint_inference_matches_contract_schema(real_model):
    from backend.inference.inference_service import CLASS_NAMES, run_inference

    result = run_inference(
        model=real_model,
        pcm_samples=_tone_pcm(5.0, 16000),
        source_sample_rate=16000,
        device_id="pneumacare-test",
        channel_id=2,
        segment_start_ms=1_723_276_800_000,
        segment_end_ms=1_723_276_805_000,
        model_version="test-version",
    )

    wc = result["wheeze_crackle"]
    assert result["device_id"] == "pneumacare-test"
    assert result["channel_id"] == 2
    assert result["model_version"] == "test-version"
    assert wc["predicted_class"] in CLASS_NAMES
    assert set(wc["probabilities"]) == set(CLASS_NAMES)
    # Konvensi backend: fraksi 0-1 (bukan persentase 0-100 seperti kode asli).
    assert all(0.0 <= p <= 1.0 for p in wc["probabilities"].values())
    assert sum(wc["probabilities"].values()) == pytest.approx(1.0, abs=1e-4)
    assert wc["confidence"] == pytest.approx(max(wc["probabilities"].values()))
    assert wc["probabilities"][wc["predicted_class"]] == pytest.approx(wc["confidence"])


def test_real_checkpoint_is_deterministic_in_eval_mode(real_model):
    from backend.inference.inference_service import run_inference

    kwargs = dict(
        model=real_model,
        pcm_samples=_tone_pcm(5.0, 16000),
        source_sample_rate=16000,
        device_id="d",
        channel_id=1,
        segment_start_ms=0,
        segment_end_ms=5000,
        model_version="v",
    )
    first = run_inference(**kwargs)["wheeze_crackle"]["probabilities"]
    second = run_inference(**kwargs)["wheeze_crackle"]["probabilities"]

    assert first == pytest.approx(second)
