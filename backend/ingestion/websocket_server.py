"""Websocket server untuk kanal audio (FR-SW-001, FR-SW-002, FR-SW-005).

Endpoint /ws/audio menerima chunk audio sesuai skema base64 JSON yang diputuskan
di INTEGRATION_CONTRACT.md §2.3, menyusunnya jadi segmen 10 detik per channel,
lalu meneruskan tiap segmen genap ke modul inference (mock atau asli).
"""

import base64
import json
import logging
from datetime import datetime, timezone

from flask import current_app
from flask_sock import Sock

from backend.ingestion.audio_segment_buffer import AudioSegmentBuffer, Segment
from backend.ingestion.device_registry import upsert_device_seen
from backend.inference.mock_inference import run_mock_inference
from backend.models import db
from backend.models.severity import ReadingSeverity

logger = logging.getLogger(__name__)

sock = Sock()

# TODO_AUTH_NOT_IMPLEMENTED: lihat config.py DEVICE_AUTH_TOKEN — endpoint ini belum
# memvalidasi token apapun (INTEGRATION_CONTRACT.md §6).
_segment_buffer = AudioSegmentBuffer()


def _decode_pcm_base64(pcm_base64: str) -> list[int]:
    raw_bytes = base64.b64decode(pcm_base64)
    # int16 little-endian, sesuai INTEGRATION_CONTRACT.md §2.3
    sample_count = len(raw_bytes) // 2
    samples = [0] * sample_count
    for i in range(sample_count):
        value = raw_bytes[2 * i] | (raw_bytes[2 * i + 1] << 8)
        if value >= 32768:
            value -= 65536
        samples[i] = value
    return samples


def _persist_segment_result(result: dict) -> None:
    prediction = result["prediction"]
    reading = ReadingSeverity(
        id=result["segment_id"],
        device_id=result["device_id"],
        channel_id=result["channel_id"],
        segment_start=datetime.fromtimestamp(result["segment_start_ms"] / 1000, tz=timezone.utc),
        segment_end=datetime.fromtimestamp(result["segment_end_ms"] / 1000, tz=timezone.utc),
        wheeze_present=prediction["wheeze"]["present"],
        wheeze_confidence=prediction["wheeze"]["confidence"],
        crackle_present=prediction["crackle"]["present"],
        crackle_confidence=prediction["crackle"]["confidence"],
        severity_class=prediction["severity_class"],
        model_version=result["model_version"],
    )
    db.session.add(reading)
    db.session.commit()


def _handle_segment(segment: Segment) -> None:
    scenario = current_app.config.get("MOCK_INFERENCE_SCENARIO", "random")
    result = run_mock_inference(
        pcm_samples=segment.pcm_samples,
        device_id=segment.device_id,
        channel_id=segment.channel_id,
        segment_start_ms=segment.segment_start_ms,
        segment_end_ms=segment.segment_end_ms,
        scenario=scenario,
    )
    _persist_segment_result(result)
    logger.info(
        "segment inferred device=%s channel=%s wheeze=%s crackle=%s",
        segment.device_id,
        segment.channel_id,
        result["prediction"]["wheeze"]["present"],
        result["prediction"]["crackle"]["present"],
    )


def register_websocket_routes(app) -> None:
    sock.init_app(app)

    @sock.route("/ws/audio")
    def ws_audio(ws):
        device_id_for_reset: tuple[str, int] | None = None
        try:
            while True:
                raw_message = ws.receive()
                if raw_message is None:
                    break

                try:
                    header = json.loads(raw_message)
                except json.JSONDecodeError:
                    logger.warning("pesan /ws/audio bukan JSON valid, diabaikan")
                    continue

                device_id = header.get("device_id")
                channel_id = header.get("channel_id")
                seq_no = header.get("seq_no")
                timestamp_ms = header.get("timestamp_ms")
                chunk_duration_ms = header.get("chunk_duration_ms")
                pcm_base64 = header.get("pcm_base64")

                if None in (device_id, channel_id, seq_no, timestamp_ms, chunk_duration_ms, pcm_base64):
                    logger.warning("pesan /ws/audio kurang field wajib, diabaikan: %s", header)
                    continue

                device_id_for_reset = (device_id, channel_id)
                pcm_samples = _decode_pcm_base64(pcm_base64)

                with current_app.app_context():
                    upsert_device_seen(device_id)

                    segment, gap_event = _segment_buffer.add_chunk(
                        device_id=device_id,
                        channel_id=channel_id,
                        timestamp_ms=timestamp_ms,
                        seq_no=seq_no,
                        chunk_duration_ms=chunk_duration_ms,
                        pcm_samples=pcm_samples,
                    )

                    if gap_event is not None:
                        logger.warning(
                            "gap terdeteksi device=%s channel=%s expected_seq=%s received_seq=%s",
                            gap_event.device_id,
                            gap_event.channel_id,
                            gap_event.expected_seq_no,
                            gap_event.received_seq_no,
                        )

                    if segment is not None:
                        _handle_segment(segment)
        finally:
            # §2.4: state segmen boleh direset saat koneksi berakhir/reconnect.
            if device_id_for_reset is not None:
                _segment_buffer.reset_channel(*device_id_for_reset)
