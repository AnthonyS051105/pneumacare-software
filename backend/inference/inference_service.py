import uuid

from backend.inference.ml_service_client import classify_segment
CLASS_NAMES = ["normal", "abnormal"]

def run_inference(
    pcm_samples: list[int],
    source_sample_rate: int,
    device_id: str,
    channel_id: int,
    segment_start_ms: int,
    segment_end_ms: int,
    model_version: str,
    ml_service_url: str,
    timeout_seconds: float,
) -> dict:
    classification = classify_segment(
        pcm_samples=pcm_samples,
        sample_rate=source_sample_rate,
        base_url=ml_service_url,
        timeout_seconds=timeout_seconds,
    )

    return {
        "segment_id": str(uuid.uuid4()),
        "device_id": device_id,
        "channel_id": channel_id,
        "segment_start_ms": segment_start_ms,
        "segment_end_ms": segment_end_ms,
        "classification": classification,
        "model_version": model_version,
    }
