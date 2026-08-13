"""Mock inference module (FR-SW-013).

Fungsi murni, tanpa I/O — mengembalikan output dummy dengan skema identik ke
INTEGRATION_CONTRACT.md §4, supaya modul hilir (trend analysis, alert engine,
database, dashboard) bisa dikembangkan tanpa menunggu model asli dari Nathanael.

🔓 `severity_class` sengaja diisi placeholder string, BUKAN ditebak — nama kelas
dan struktur confidence WAJIB dikonfirmasi ke Nathanael (INTEGRATION_CONTRACT.md §4).
"""

import random
import uuid
from typing import Literal

MODEL_VERSION = "mock_v1"

# state in-memory sederhana untuk skenario "wheeze_rising": confidence naik bertahap
# per (device_id, channel_id) selama proses backend berjalan. Bukan persisted state.
_rising_state: dict[tuple[str, int], float] = {}


def run_mock_inference(
    pcm_samples: list[int],
    device_id: str,
    channel_id: int,
    segment_start_ms: int,
    segment_end_ms: int,
    scenario: Literal["random", "wheeze_rising"] = "random",
) -> dict:
    """Hasilkan output klasifikasi dummy untuk satu segmen 10 detik.

    `pcm_samples` diterima untuk menjaga interface identik dengan inference_service.py
    asli (FR-SW-013: "interface identik"), tapi tidak dipakai untuk mock random/rising.
    """
    if scenario == "wheeze_rising":
        wheeze_confidence, crackle_confidence = _next_rising_confidence(device_id, channel_id)
        wheeze_present = wheeze_confidence >= 0.5
        crackle_present = False
    else:
        wheeze_confidence = round(random.uniform(0.0, 1.0), 4)
        crackle_confidence = round(random.uniform(0.0, 1.0), 4)
        wheeze_present = wheeze_confidence >= 0.7
        crackle_present = crackle_confidence >= 0.7

    return {
        "segment_id": str(uuid.uuid4()),
        "device_id": device_id,
        "channel_id": channel_id,
        "segment_start_ms": segment_start_ms,
        "segment_end_ms": segment_end_ms,
        "prediction": {
            "wheeze": {"present": wheeze_present, "confidence": wheeze_confidence},
            "crackle": {"present": crackle_present, "confidence": crackle_confidence},
            "severity_class": "TODO_CONFIRM_WITH_NATHANAEL",
        },
        "model_version": MODEL_VERSION,
    }


def _next_rising_confidence(device_id: str, channel_id: int) -> tuple[float, float]:
    key = (device_id, channel_id)
    current = _rising_state.get(key, 0.1)
    next_value = min(current + 0.05, 0.95)
    _rising_state[key] = next_value
    return round(next_value, 4), round(random.uniform(0.0, 0.2), 4)


def reset_rising_state() -> None:
    """Dipakai oleh test untuk mengembalikan state skenario wheeze_rising ke awal."""
    _rising_state.clear()
