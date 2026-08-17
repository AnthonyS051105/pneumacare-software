"""Load checkpoint Model A (wheeze/crackle CNN) — FR-SW-010, FR-SW-010b,
SDD_SOFTWARE.md §5, INTEGRATION_CONTRACT.md §4.1.

Import LANGSUNG `RespiratoryMobileNet` dari `ai_reference/model.py` (kode asli
Nathanael) — TIDAK ditulis ulang, sesuai instruksi eksplisit ("jangan tulis ulang
class-nya"). Cara load checkpoint mengikuti persis pola di
`ai_reference/detector_reference_standalone.py` (`Detector.__init__`), termasuk
detail penting: `load_state_dict` dipanggil ke `model.model` (nested attribute),
BUKAN `model` langsung.
"""

import logging
import os

import torch

from ai_reference.model import RespiratoryMobileNet

logger = logging.getLogger(__name__)

NUM_CLASSES = 4


def load_model(checkpoint_path: str, device: torch.device | None = None) -> RespiratoryMobileNet:
    """Load checkpoint PyTorch Lightning ke instance `RespiratoryMobileNet`, dalam mode eval.

    Raises FileNotFoundError bila checkpoint_path tidak ada — caller (app startup,
    lihat SDD_SOFTWARE.md §9) bertanggung jawab menangkap ini dan fallback ke
    mock_inference dengan log warning jelas, BUKAN membiarkan silent fail.
    """
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    if not os.path.exists(checkpoint_path):
        raise FileNotFoundError(f"Checkpoint model tidak ditemukan di: {checkpoint_path}")

    model = RespiratoryMobileNet(num_classes=NUM_CLASSES)

    checkpoint = torch.load(checkpoint_path, map_location=device)
    if "state_dict" in checkpoint:
        # Persis pola ai_reference/detector_reference_standalone.py: filter key
        # berawalan "model.", strip prefix, load ke model.model (nested attribute).
        # Catatan: kode referensi asli pakai k.replace("model.", "") tanpa count=1
        # (mengganti SEMUA kemunculan substring, bukan cuma prefix) — di sini dibuat
        # eksplisit strip prefix sekali saja (lebih aman untuk key yang secara teori
        # bisa mengandung "model." lagi di tengah), hasilnya identik untuk checkpoint
        # yang ada karena strukturnya flat.
        state_dict = {
            k[len("model."):]: v
            for k, v in checkpoint["state_dict"].items()
            if k.startswith("model.")
        }
        model.model.load_state_dict(state_dict)
    else:
        model.load_state_dict(checkpoint)

    model.to(device)
    model.eval()

    logger.info("Model A checkpoint dimuat dari %s (device=%s)", checkpoint_path, device)
    return model
