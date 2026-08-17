"""Jalankan Model A (wheeze/crackle) atas satu segmen audio, hasilkan output
sesuai skema INTEGRATION_CONTRACT.md §4.1 — FR-SW-012, SDD_SOFTWARE.md §5.

✅ **Keputusan confidence (2026-08-17, didokumentasikan juga di
INTEGRATION_CONTRACT.md §4.1)**: confidence/probabilities disimpan sebagai
FRAKSI 0-1, BUKAN persentase 0-100 seperti kode asli Nathanael
(`ai_reference/detector_reference_standalone.py` kali dengan 100). Konversi
terjadi SEKALI di titik ini (bagi softmax output dengan 100 tidak diperlukan
karena softmax PyTorch sudah menghasilkan fraksi 0-1 secara native — kode asli
Nathanael-lah yang mengalikan 100 belakangan, jadi modul ini justru TIDAK
mengalikan 100, mempertahankan fraksi asli dari `F.softmax`). Alasan pemilihan
fraksi: konsisten dengan skema confidence yang sudah dipakai `mock_inference.py`
sejak Fase 1 (0-1) dan `TREND_SIGNIFICANCE_THRESHOLD_DEFAULT` di config.py.
"""

import uuid

import torch
import torch.nn.functional as F

from ai_reference.model import RespiratoryMobileNet
from backend.inference.preprocessing import preprocess_segment

# ✅ Urutan kelas dikonfirmasi Nathanael (12 Agt 2026) — BUKAN urutan
# `self.classes` di ai_reference/detector_reference_standalone.py (itu bug).
CLASS_NAMES = ["none", "crackle", "wheeze", "both"]


def run_inference(
    model: RespiratoryMobileNet,
    pcm_samples: list[int],
    source_sample_rate: int,
    device_id: str,
    channel_id: int,
    segment_start_ms: int,
    segment_end_ms: int,
    model_version: str,
) -> dict:
    """Jalankan inference Model A atas satu segmen, kembalikan dict sesuai skema
    INTEGRATION_CONTRACT.md §4.1 (field `wheeze_crackle`, bukan lagi skema lama
    `prediction.wheeze`/`prediction.crackle` dua-flag independen).
    """
    tensor_x = preprocess_segment(pcm_samples, source_sample_rate)

    device = next(model.parameters()).device
    tensor_x = tensor_x.to(device)

    with torch.no_grad():
        logits = model(tensor_x)
        probabilities = F.softmax(logits, dim=1).cpu().numpy()[0]

    predicted_idx = int(probabilities.argmax())
    predicted_class = CLASS_NAMES[predicted_idx]
    confidence = float(probabilities[predicted_idx])  # fraksi 0-1, lihat docstring modul

    return {
        "segment_id": str(uuid.uuid4()),
        "device_id": device_id,
        "channel_id": channel_id,
        "segment_start_ms": segment_start_ms,
        "segment_end_ms": segment_end_ms,
        "wheeze_crackle": {
            "predicted_class": predicted_class,
            "confidence": confidence,
            "probabilities": {
                cls_name: float(probabilities[i]) for i, cls_name in enumerate(CLASS_NAMES)
            },
        },
        "model_version": model_version,
    }
