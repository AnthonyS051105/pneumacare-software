"""Mock inference module (FR-SW-013).

Fungsi murni, tanpa I/O — mengembalikan output dummy dengan skema IDENTIK ke
Model A asli (INTEGRATION_CONTRACT.md §4.1, inference_service.py): field
`wheeze_crackle.predicted_class` (4-kelas none/crackle/wheeze/both, urutan
dikonfirmasi Nathanael), `confidence` (fraksi 0-1), `probabilities` (4 nilai).

🔄 Skema direvisi 2026-08-17 — sebelumnya modul ini pakai skema lama
(`prediction.wheeze.present`/`prediction.crackle.present` dua-flag independen)
yang TIDAK sesuai output Model A sungguhan (single-label 4-kelas). Skema baru
ini mengikuti persis `inference_service.py` supaya modul hilir (trend analysis,
alert engine, database, dashboard) bisa dites dengan mock TANPA perlu tahu
apakah sedang bicara dengan model asli atau dummy.
"""

import random
import uuid
from typing import Literal

from backend.inference.inference_service import CLASS_NAMES

MODEL_VERSION = "mock_v2"


# state in-memory sederhana untuk skenario "wheeze_rising": confidence kelas
# "wheeze" naik bertahap per (device_id, channel_id) selama proses backend berjalan.
# Bukan persisted state.
_rising_state: dict[tuple[str, int], float] = {}


def run_mock_inference(
    pcm_samples: list[int],
    device_id: str,
    channel_id: int,
    segment_start_ms: int,
    segment_end_ms: int,
    scenario: Literal["random", "wheeze_rising"] = "random",
) -> dict:
    """Hasilkan output klasifikasi dummy untuk satu segmen 5 detik, skema identik
    Model A asli.

    `pcm_samples` diterima untuk menjaga interface identik dengan
    `inference_service.run_inference` (FR-SW-013: "interface identik"), tapi
    tidak dipakai untuk menghasilkan angka mock.
    """
    if scenario == "wheeze_rising":
        probabilities = _next_rising_probabilities(device_id, channel_id)
    else:
        probabilities = _random_probabilities()

    predicted_idx = max(range(len(CLASS_NAMES)), key=lambda i: probabilities[i])
    predicted_class = CLASS_NAMES[predicted_idx]
    confidence = probabilities[predicted_idx]

    return {
        "segment_id": str(uuid.uuid4()),
        "device_id": device_id,
        "channel_id": channel_id,
        "segment_start_ms": segment_start_ms,
        "segment_end_ms": segment_end_ms,
        "wheeze_crackle": {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "probabilities": dict(zip(CLASS_NAMES, probabilities)),
        },
        "model_version": MODEL_VERSION,
    }


def _random_probabilities() -> list[float]:
    raw = [random.uniform(0.0, 1.0) for _ in CLASS_NAMES]
    total = sum(raw)
    return [round(v / total, 4) for v in raw]


def _next_rising_probabilities(device_id: str, channel_id: int) -> list[float]:
    """Skenario demo tren naik: probabilitas kelas "wheeze" naik bertahap tiap
    segmen berturut-turut untuk (device_id, channel_id) ini, sisa probabilitas
    dibagi rata ke 3 kelas lain — untuk demo trend_detector.py mendeteksi tren naik.
    """
    key = (device_id, channel_id)
    current = _rising_state.get(key, 0.1)
    next_value = min(current + 0.05, 0.95)
    _rising_state[key] = next_value

    wheeze_idx = CLASS_NAMES.index("wheeze")
    remaining = (1.0 - next_value) / (len(CLASS_NAMES) - 1)
    probabilities = [remaining] * len(CLASS_NAMES)
    probabilities[wheeze_idx] = next_value
    return [round(p, 4) for p in probabilities]


def reset_rising_state() -> None:
    """Dipakai oleh test untuk mengembalikan state skenario wheeze_rising ke awal."""
    _rising_state.clear()
