import io
import math
import wave
import numpy as np
import requests

CLASS_NAMES = ["normal", "abnormal"]
# Serialization tolerance for float32 softmax output; not a clinical threshold.
_PROBABILITY_TOLERANCE = 1e-5


def _is_probability(value) -> bool:
    return (type(value) in (int, float) and 0 <= value <= 1
            and math.isfinite(value))


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

    if type(index) is not int or index not in (0, 1):
        raise MLServiceError(f"Index kelas tidak dikenal: {index!r}")
    if not _is_probability(confidence):
        raise MLServiceError(f"Confidence tidak valid: {confidence!r}")
    if (
        not isinstance(probabilities, list)
        or len(probabilities) != len(CLASS_NAMES)
        or any(not _is_probability(value) for value in probabilities)
    ):
        raise MLServiceError(f"Probabilitas tidak valid: {probabilities!r}")

    if not math.isclose(sum(probabilities), 1.0, rel_tol=0,
                        abs_tol=_PROBABILITY_TOLERANCE):
        raise MLServiceError("Probabilitas ML harus berjumlah satu")
    # PyTorch argmax chooses the first class in an exact tie.
    if index != max(range(len(CLASS_NAMES)), key=probabilities.__getitem__):
        raise MLServiceError("Index kelas ML tidak sesuai argmax probabilitas")
    if not math.isclose(confidence, probabilities[index], rel_tol=0,
                        abs_tol=_PROBABILITY_TOLERANCE):
        raise MLServiceError("Confidence ML tidak sesuai probabilitas kelas terpilih")

    return {
        "predicted_class": CLASS_NAMES[index],
        "confidence": float(confidence),
        "probabilities": {
            name: float(probabilities[i]) for i, name in enumerate(CLASS_NAMES)
        },
    }
