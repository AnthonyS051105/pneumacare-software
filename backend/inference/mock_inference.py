"""Mock inference 2 kelas (normal/abnormal) tanpa ML service.

Skema output identik dengan `inference_service.run_inference` supaya modul
hilir tidak perlu tahu apakah data berasal dari service asli atau mock.
"""

import random
import uuid
from typing import Literal

from backend.inference.inference_service import CLASS_NAMES

MODEL_VERSION = "mock_v3"

# State in-memory untuk skenario "abnormal_rising" per (device_id, channel_id).
_rising_state: dict[tuple[str, int], float] = {}


def run_mock_inference(
    pcm_samples: list[int],
    device_id: str,
    channel_id: int,
    segment_start_ms: int,
    segment_end_ms: int,
    scenario: Literal["random", "abnormal_rising"] = "random",
) -> dict:
    if scenario == "abnormal_rising":
        probabilities = _next_rising_probabilities(device_id, channel_id)
    else:
        probabilities = _random_probabilities()

    predicted_idx = max(range(len(CLASS_NAMES)), key=lambda i: probabilities[i])

    return {
        "segment_id": str(uuid.uuid4()),
        "device_id": device_id,
        "channel_id": channel_id,
        "segment_start_ms": segment_start_ms,
        "segment_end_ms": segment_end_ms,
        "classification": {
            "predicted_class": CLASS_NAMES[predicted_idx],
            "confidence": probabilities[predicted_idx],
            "probabilities": dict(zip(CLASS_NAMES, probabilities)),
        },
        "model_version": MODEL_VERSION,
    }


def _random_probabilities() -> list[float]:
    normal = random.uniform(0.0, 1.0)
    return [round(normal, 4), round(1.0 - normal, 4)]


def _next_rising_probabilities(device_id: str, channel_id: int) -> list[float]:
    key = (device_id, channel_id)
    current = _rising_state.get(key, 0.1)
    abnormal = min(current + 0.05, 0.95)
    _rising_state[key] = abnormal
    return [round(1.0 - abnormal, 4), round(abnormal, 4)]


def reset_rising_state() -> None:
    _rising_state.clear()
