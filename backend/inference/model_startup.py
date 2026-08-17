"""Load Model A saat startup backend, dengan fallback otomatis ke mock_inference
bila checkpoint tidak tersedia — SDD_SOFTWARE.md §9 ("Model gagal load saat startup
-> fallback otomatis ke mock_inference dengan log warning jelas, jangan silent fail").
"""

import logging

from backend.inference.model_loader import load_model

logger = logging.getLogger(__name__)


def load_model_a_or_none(checkpoint_path: str):
    """Return model yang sudah di-load, atau None bila checkpoint kosong/gagal dimuat.

    `websocket_server.py` menafsirkan None sebagai sinyal untuk memakai
    mock_inference — TIDAK raise di sini supaya app startup tidak pernah crash
    hanya karena checkpoint belum ada (mis. saat development tanpa file model).
    """
    if not checkpoint_path:
        logger.warning(
            "MODEL_A_CHECKPOINT_PATH kosong — fallback ke mock_inference. "
            "Set env var ini ke path checkpoint untuk memakai model asli."
        )
        return None

    try:
        return load_model(checkpoint_path)
    except FileNotFoundError as exc:
        logger.warning("Gagal load Model A checkpoint (%s) — fallback ke mock_inference", exc)
        return None
    except Exception:
        logger.exception("Gagal load Model A checkpoint karena error tak terduga — fallback ke mock_inference")
        return None
