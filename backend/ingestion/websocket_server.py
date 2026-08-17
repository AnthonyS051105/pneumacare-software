"""Websocket server untuk kanal audio (FR-SW-001, FR-SW-002, FR-SW-005).

Endpoint /ws/audio menerima chunk audio sesuai skema base64 JSON yang diputuskan
di INTEGRATION_CONTRACT.md §2.3, menyusunnya jadi segmen 5 detik per channel
(INTEGRATION_CONTRACT.md §4.1), lalu meneruskan tiap segmen genap ke Model A asli
(bila ter-load saat startup, lihat inference/model_startup.py) atau mock_inference.
"""

import base64
import json
import logging
from datetime import datetime, timezone

from flask import current_app, request
from flask_sock import Sock

from backend.alerting.alert_engine import VitalReading
from backend.alerting.alert_service import evaluate_and_save_alert
from backend.inference.inference_service import run_inference
from backend.inference.mock_inference import run_mock_inference
from backend.ingestion.audio_segment_buffer import AudioSegmentBuffer, Segment
from backend.ingestion.device_registry import upsert_device_seen
from backend.models import db
from backend.models.classification import ReadingClassification
from backend.models.vital import ReadingVital
from backend.trend_analysis.trend_service import compute_and_save_trend

logger = logging.getLogger(__name__)

sock = Sock()

# Validasi bearer token statis sesuai INTEGRATION_CONTRACT.md §6 — baseline demo,
# BUKAN autentikasi kelas produksi (tidak ada rotasi/expiry per device).
_segment_buffer = AudioSegmentBuffer()


def _is_authorized(headers) -> bool:
    expected_token = current_app.config.get("DEVICE_AUTH_TOKEN", "")
    if not expected_token:
        # Token belum dikonfigurasi di backend (dev tanpa .env) — jangan kunci semua
        # device di luar, tapi log jelas supaya tidak dianggap aman diam-diam.
        logger.warning("DEVICE_AUTH_TOKEN kosong di backend — /ws/audio menerima semua koneksi")
        return True

    auth_header = headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return False
    return auth_header[len("Bearer ") :] == expected_token


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
    wheeze_crackle = result["wheeze_crackle"]
    reading = ReadingClassification(
        id=result["segment_id"],
        device_id=result["device_id"],
        channel_id=result["channel_id"],
        segment_start=datetime.fromtimestamp(result["segment_start_ms"] / 1000, tz=timezone.utc),
        segment_end=datetime.fromtimestamp(result["segment_end_ms"] / 1000, tz=timezone.utc),
        wheeze_crackle_class=wheeze_crackle["predicted_class"],
        wheeze_crackle_confidence=wheeze_crackle["confidence"],
        wheeze_crackle_probabilities=wheeze_crackle["probabilities"],
        wheeze_crackle_model_version=result["model_version"],
    )
    db.session.add(reading)
    db.session.commit()


def _handle_segment(segment: Segment) -> None:
    model = current_app.config.get("_INFERENCE_MODEL")

    if model is not None:
        result = run_inference(
            model=model,
            pcm_samples=segment.pcm_samples,
            source_sample_rate=segment.sample_rate,
            device_id=segment.device_id,
            channel_id=segment.channel_id,
            segment_start_ms=segment.segment_start_ms,
            segment_end_ms=segment.segment_end_ms,
            model_version=current_app.config.get("MODEL_A_VERSION", "unknown"),
        )
    else:
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
        "segment inferred device=%s channel=%s predicted_class=%s confidence=%.3f",
        segment.device_id,
        segment.channel_id,
        result["wheeze_crackle"]["predicted_class"],
        result["wheeze_crackle"]["confidence"],
    )

    app = current_app._get_current_object()
    trend_result = compute_and_save_trend(app, segment.device_id, segment.channel_id)

    latest_vital = (
        db.session.query(ReadingVital)
        .filter_by(device_id=segment.device_id)
        .order_by(ReadingVital.timestamp.desc())
        .first()
    )
    vitals = VitalReading(
        hr=latest_vital.hr if latest_vital is not None else None,
        spo2=latest_vital.spo2 if latest_vital is not None else None,
        rr=latest_vital.rr if latest_vital is not None else None,
    )
    evaluate_and_save_alert(app, device_id=segment.device_id, vitals=vitals, trend_result=trend_result)


def register_websocket_routes(app) -> None:
    sock.init_app(app)

    @sock.route("/ws/audio")
    def ws_audio(ws):
        if not _is_authorized(request.headers):
            logger.warning("koneksi /ws/audio ditolak: token Authorization tidak valid")
            ws.close(reason=1008, message=b"unauthorized")
            return

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
                sample_rate = header.get("sample_rate")

                if None in (
                    device_id,
                    channel_id,
                    seq_no,
                    timestamp_ms,
                    chunk_duration_ms,
                    pcm_base64,
                    sample_rate,
                ):
                    logger.warning("pesan /ws/audio kurang field wajib, diabaikan: %s", header)
                    continue

                bit_depth = header.get("bit_depth")
                if bit_depth is not None and bit_depth != 16:
                    logger.warning(
                        "bit_depth tidak didukung: %s, hanya 16-bit yang didukung saat ini",
                        bit_depth,
                    )
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
                        sample_rate=sample_rate,
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
