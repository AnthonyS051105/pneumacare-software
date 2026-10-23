import io
import wave
import numpy as np
import requests

CLASS_NAMES = ["normal", "abnormal"]


class MLServiceError(RuntimeError):
    """Kesalahan saat memanggil ML service."""

def _pcm_to_wav_bytes(pcm_samples: list[int], sample_rate: int) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)  # PCM int16 little-endian
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(np.asarray(pcm_samples, dtype="<i2").tobytes())
    return buffer.getvalue()


def classify_segment(
    pcm_samples: list[int],
    sample_rate: int,
    base_url: str,
    timeout_seconds: float,
) -> dict:
    try:
        response = requests.post(
            f"{base_url.rstrip('/')}/predict",
            files={
                "file": (
                    "segment.wav",
                    _pcm_to_wav_bytes(pcm_samples, sample_rate),
                    "audio/wav",
                )
            },
            timeout=timeout_seconds,
        )
        response.raise_for_status()
        payload = response.json()
    except (requests.RequestException, ValueError) as exc:
        raise MLServiceError(f"Gagal memanggil ML service: {exc}") from exc

    if not isinstance(payload, dict):
        raise MLServiceError(f"Respons ML bukan object JSON: {payload!r}")

    index = payload.get("class")
    confidence = payload.get("confidence")
    probabilities = payload.get("probabilities")

    if index not in (0, 1):
        raise MLServiceError(f"Index kelas tidak dikenal: {index!r}")
    if not isinstance(confidence, (int, float)):
        raise MLServiceError(f"Confidence tidak valid: {confidence!r}")
    if (
        not isinstance(probabilities, list)
        or len(probabilities) != len(CLASS_NAMES)
        or any(not isinstance(value, (int, float)) for value in probabilities)
    ):
        raise MLServiceError(f"Probabilitas tidak valid: {probabilities!r}")

    return {
        "predicted_class": CLASS_NAMES[index],
        "confidence": float(confidence),
        "probabilities": {
            name: float(probabilities[i]) for i, name in enumerate(CLASS_NAMES)
        },
    }
