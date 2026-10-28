"""Websocket server untuk kanal audio (FR-SW-001, FR-SW-002, FR-SW-005).

Endpoint /ws/audio menerima chunk audio sesuai skema base64 JSON yang diputuskan
di INTEGRATION_CONTRACT.md §2.3, menyusunnya jadi segmen 5 detik per channel
(INTEGRATION_CONTRACT.md §4.1), lalu meneruskan tiap segmen genap ke ML service
via HTTP atau mock_inference hanya bila mode mock dipilih eksplisit.
"""

import base64
import json
import logging
from contextlib import contextmanager
from threading import Event, Lock
from time import monotonic, time
import numpy as np
from datetime import datetime, timezone

from flask import current_app, request
from flask_sock import Sock

from backend.alerting.alert_engine import VitalReading
from backend.alerting.alert_service import evaluate_and_save_alert
from backend.analysis.cycle_segmenter import CycleDetectionResult, CycleSlice, detect_cycle_slices
from backend.inference.inference_service import run_inference
from backend.inference.ml_service_client import MLServiceError
from backend.inference.mock_inference import run_mock_inference
from backend.ingestion.audio_segment_buffer import AudioSegmentBuffer, Segment
from backend.ingestion.audio_worker import AudioWorker
from backend.ingestion.device_registry import upsert_device_seen
from backend.models import db
from backend.models.classification import ReadingClassification
from backend.models.respiratory_cycle import RespiratoryCycle
from backend.models.vital import ReadingVital
from backend.trend_analysis.trend_service import compute_and_save_trend

logger = logging.getLogger(__name__)

@contextmanager
def _timed_stage(stage: str, device_id: str, channel_id: int):
    started = monotonic()
    status = "ok"
    try:
        yield
    except BaseException:
        status = "error"
        raise
    finally:
        logger.info("audio_stage stage=%s status=%s device=%s channel=%s duration_ms=%.3f",
                    stage, status, device_id, channel_id, (monotonic() - started) * 1000)


sock = Sock()

# Validasi bearer token statis sesuai INTEGRATION_CONTRACT.md §6 — baseline demo,
# BUKAN autentikasi kelas produksi (tidak ada rotasi/expiry per device).



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


def _decode_pcm_base64(pcm_base64: str):
    raw_bytes = base64.b64decode(pcm_base64, validate=True)
    if len(raw_bytes) % 2:
        raise ValueError("odd PCM byte length")
    return np.frombuffer(raw_bytes, dtype="<i2")


def _persist_segment_result(result: dict) -> None:
    classification = result["classification"]
    reading = ReadingClassification(
        id=result["segment_id"],
        device_id=result["device_id"],
        channel_id=result["channel_id"],
        segment_start=datetime.fromtimestamp(result["segment_start_ms"] / 1000, tz=timezone.utc),
        segment_end=datetime.fromtimestamp(result["segment_end_ms"] / 1000, tz=timezone.utc),
        predicted_class=classification["predicted_class"],
        confidence=classification["confidence"],
        probabilities=classification["probabilities"],
        model_version=result["model_version"],
    )
    db.session.add(reading)
    db.session.commit()


def _classify_input(
    pcm_samples: list[int],
    sample_rate: int,
    device_id: str,
    channel_id: int,
    segment_start_ms: int,
    segment_end_ms: int,
) -> dict:
    ml_service_url = current_app.config.get("ML_SERVICE_URL", "")
    scenario = current_app.config.get("MOCK_INFERENCE_SCENARIO", "random")

    if ml_service_url:
        try:
            # WAV serialization, HTTP wait and response validation; remote stages
            # need their own service logs and are not inferred from this timer.
            with _timed_stage("classify_http", device_id, channel_id):
                return run_inference(
                    pcm_samples=pcm_samples,
                    source_sample_rate=sample_rate,
                    device_id=device_id,
                    channel_id=channel_id,
                    segment_start_ms=segment_start_ms,
                    segment_end_ms=segment_end_ms,
                    model_version=current_app.config.get("ML_SERVICE_MODEL_VERSION", "unknown"),
                    ml_service_url=ml_service_url,
                    timeout_seconds=current_app.config.get("ML_SERVICE_TIMEOUT_SECONDS", 30),
                )
        except MLServiceError:
            logger.exception(
                "ML service gagal device=%s channel=%s — job gagal; hasil sintetis tidak dibuat",
                device_id,
                channel_id,
            )
            raise

    return run_mock_inference(
        pcm_samples=pcm_samples,
        device_id=device_id,
        channel_id=channel_id,
        segment_start_ms=segment_start_ms,
        segment_end_ms=segment_end_ms,
        scenario=scenario,
    )


def _persist_cycle_metadata(
    result: dict,
    segment: Segment,
    detection: CycleDetectionResult,
    cycle: CycleSlice | None,
) -> None:
    cycle_start_ms = None
    cycle_end_ms = None
    if cycle is not None:
        cycle_start_ms = segment.segment_start_ms + round(cycle.start_s * 1000)
        cycle_end_ms = segment.segment_start_ms + round(cycle.end_s * 1000)

    db.session.add(
        RespiratoryCycle(
            classification_id=result["segment_id"],
            device_id=segment.device_id,
            channel_id=segment.channel_id,
            analysis_start=datetime.fromtimestamp(
                segment.segment_start_ms / 1000, tz=timezone.utc
            ),
            analysis_end=datetime.fromtimestamp(
                segment.segment_end_ms / 1000, tz=timezone.utc
            ),
            detection_status="detected" if cycle is not None else detection.status,
            cycle_index=cycle.index if cycle is not None else None,
            cycle_start_ms=cycle_start_ms,
            cycle_end_ms=cycle_end_ms,
            mean_dtw=detection.mean_dtw,
            dtw_score=cycle.dtw_score if cycle is not None else None,
        )
    )
    db.session.commit()


def _handle_segment(segment: Segment, job=None) -> None:
    # Retain cycle detection/classification semantics from feat/ai-integration.
    if job is not None:
        job.check_cancelled()
    with _timed_stage("registry", segment.device_id, segment.channel_id):
        upsert_device_seen(segment.device_id)
    with _timed_stage("cycle_detection", segment.device_id, segment.channel_id):
        detection = detect_cycle_slices(segment.pcm_samples, segment.sample_rate)
    logger.info("audio_cycles device=%s channel=%s status=%s cycles=%d mean_dtw=%s",
                segment.device_id, segment.channel_id, detection.status,
                len(detection.cycles), detection.mean_dtw)

    if detection.cycles:
        inputs = [
            (
                cycle.pcm_samples,
                segment.segment_start_ms + round(cycle.start_s * 1000),
                segment.segment_start_ms + round(cycle.end_s * 1000),
                cycle,
            )
            for cycle in detection.cycles
        ]
    else:
        inputs = [
            (
                segment.pcm_samples,
                segment.segment_start_ms,
                segment.segment_end_ms,
                None,
            )
        ]

    for pcm_samples, start_ms, end_ms, cycle in inputs:
        if job is not None:
            job.check_cancelled()
        with _timed_stage("classification", segment.device_id, segment.channel_id):
            result = _classify_input(
                pcm_samples=pcm_samples,
                sample_rate=segment.sample_rate,
                device_id=segment.device_id,
                channel_id=segment.channel_id,
                segment_start_ms=start_ms,
                segment_end_ms=end_ms,
            )
        # HTTP/model calls cannot be interrupted safely; do not persist stale work
        # when replacement/disconnect was observed while the model was running.
        if job is not None:
            job.check_cancelled()
        # Includes both existing commits; this does not make them atomic.
        with _timed_stage("persist_cycle", segment.device_id, segment.channel_id):
            _persist_segment_result(result)
            _persist_cycle_metadata(result, segment, detection, cycle)
        logger.info(
            "segment inferred device=%s channel=%s classification_id=%s cycle=%s predicted_class=%s confidence=%.3f",
            segment.device_id,
            segment.channel_id,
            result["segment_id"],
            cycle.index if cycle is not None else "fallback",
            result["classification"]["predicted_class"],
            result["classification"]["confidence"],
        )

    if job is not None:
        job.check_cancelled()
    app = current_app._get_current_object()
    with _timed_stage("trend", segment.device_id, segment.channel_id):
        trend_result = compute_and_save_trend(app, segment.device_id, segment.channel_id)

    # Include the latest-vital lookup as downstream alert work.
    with _timed_stage("alert", segment.device_id, segment.channel_id):
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
        if job is not None:
            job.check_cancelled()
        evaluate_and_save_alert(app, device_id=segment.device_id, vitals=vitals, trend_result=trend_result)


class AudioReceiver:
    """App-local connection ownership; each connection owns all four partial buffers.

    Claim only on a valid first frame. A replaced connection can never reclaim a
    device and its finally block can only remove its own ownership.
    """
    def __init__(self, app, worker):
        self.app, self.worker = app, worker
        self.lock = Lock()
        self.owners = {}

    def connection(self):
        return AudioConnection(self)


class AudioConnection:
    def __init__(self, receiver):
        self.receiver = receiver
        self.buffer = AudioSegmentBuffer(receiver.app.config["AUDIO_SEGMENT_DURATION_MS"])
        self.device_id = None
        self.stream_id = None
        self.cancelled = Event()
        self.closed = False
        self.chunks = 0
        self.decode_ms = self.assemble_ms = self.receive_max_ms = 0.0
        self.gaps = 0
        self.invalid = 0
        self.timestamp_fallbacks = 0

    def _reset(self, reason):
        self.cancelled.set()
        self.cancelled = Event()
        discarded = self.buffer.reset_device(self.device_id)
        logger.info("audio_partial_cancel reason=%s device=%s discarded_samples=%d",
                    reason, self.device_id, discarded)

    def receive(self, raw_message):
        started = monotonic()
        try:
            if not isinstance(raw_message, str) or len(raw_message) > 260000:
                raise ValueError("message size/type")
            h = json.loads(raw_message)
            if not isinstance(h, dict):
                raise ValueError("JSON object required")
            device = h.get("device_id")
            if not isinstance(device, str) or not 1 <= len(device) <= 64:
                raise ValueError("device id")
            for key in ("channel_id", "seq_no", "timestamp_ms", "chunk_duration_ms", "sample_rate"):
                if type(h.get(key)) is not int:
                    raise ValueError("integer fields")
            if not 1 <= h["channel_id"] <= 4 or h["seq_no"] < 0 or not 0 <= h["timestamp_ms"] < 253402300799000:
                raise ValueError("channel/sequence/timestamp")
            if h["sample_rate"] not in (4000, 8000, 16000, 22000, 44100, 48000):
                raise ValueError("sample rate")
            if h.get("bit_depth", 16) != 16 or not 0 < h["chunk_duration_ms"] <= 2000:
                raise ValueError("format/duration")
            stream = h.get("stream_id")
            sample_start = h.get("sample_start")
            if "stream_id" in h or "sample_start" in h:
                if (not isinstance(stream, str) or not 1 <= len(stream) <= 64
                        or type(sample_start) is not int or not 0 <= sample_start < 2**64):
                    raise ValueError("continuity metadata pair")
            if not isinstance(h.get("pcm_base64"), str):
                raise ValueError("PCM base64 type")
            pcm = _decode_pcm_base64(h["pcm_base64"])
            if len(pcm) * 1000 != h["sample_rate"] * h["chunk_duration_ms"]:
                raise ValueError("PCM count/duration mismatch")
        except (ValueError, TypeError):
            self.invalid += 1
            # Payload and credentials must never reach logs.
            logger.warning("audio_invalid_frame count=%d", self.invalid)
            if self.device_id is not None:
                self._reset("invalid_frame")
            return False
        if h["timestamp_ms"] < 1700000000000:
            h["timestamp_ms"] = int(time() * 1000) - h["chunk_duration_ms"]
            self.timestamp_fallbacks += 1
            if self.timestamp_fallbacks == 1:
                logger.warning("audio_timestamp source=server_receive_estimate reason=device_pre_ntp")
        decoded = monotonic()
        r = self.receiver
        with r.lock:
            if self.closed or self.cancelled.is_set():
                return False
            if self.device_id is None:
                old = r.owners.get(device)
                if old is None and len(r.owners) >= r.app.config.get("AUDIO_MAX_DEVICES", 8):
                    logger.warning("audio_device_limit")
                    return False
                if old is not None:
                    old.close_locked("replaced")
                self.device_id, self.stream_id = device, stream
                r.owners[device] = self
                logger.info("audio_session_open device=%s continuity=%s", device,
                            "sample_index" if stream else "legacy_timestamp_only")
            elif device != self.device_id:
                self._reset("device_change_rejected")
                return False
            elif stream != self.stream_id:
                self._reset("stream_change")
                self.stream_id = stream
            segment, gap = self.buffer.add_chunk(
                device_id=device, channel_id=h["channel_id"], timestamp_ms=h["timestamp_ms"],
                seq_no=h["seq_no"], chunk_duration_ms=h["chunk_duration_ms"], pcm_samples=pcm,
                sample_rate=h["sample_rate"], sample_start=sample_start, stream_id=stream)
            if gap is not None:
                self.gaps += 1
                logger.warning("audio_gap device=%s channel=%d reason=%s expected_seq=%d received_seq=%d "
                               "lost_samples=%s discarded_samples=%d", device, h["channel_id"],
                               gap.reason, gap.expected_seq_no, gap.received_seq_no,
                               gap.lost_samples, gap.discarded_samples)
            if segment is not None:
                accepted = r.worker.submit(segment, self.cancelled)
                logger.info("audio_segment_ready device=%s channel=%d accepted=%s", device,
                            h["channel_id"], accepted)
        ended = monotonic()
        self.chunks += 1
        self.decode_ms += (decoded - started) * 1000
        self.assemble_ms += (ended - decoded) * 1000
        self.receive_max_ms = max(self.receive_max_ms, (ended - started) * 1000)
        if self.chunks % 80 == 0:
            logger.info("audio_receive device=%s chunks=%d gaps=%d invalid=%d decode_mean_ms=%.3f "
                        "assemble_mean_ms=%.3f receive_max_ms=%.3f", self.device_id,
                        self.chunks, self.gaps, self.invalid, self.decode_ms / self.chunks,
                        self.assemble_ms / self.chunks, self.receive_max_ms)
        return True

    def close_locked(self, reason):
        self.closed = True
        self._reset(reason)
        self.cancelled.set()
        if self.receiver.owners.get(self.device_id) is self:
            self.receiver.owners.pop(self.device_id)

    def close(self):
        with self.receiver.lock:
            self.close_locked("disconnect")


def register_websocket_routes(app) -> None:
    sock.init_app(app)
    if "audio_worker" not in app.extensions:
        worker = AudioWorker(app, lambda job: _handle_segment(job.segment, job),
                             capacity=app.config["AUDIO_QUEUE_CAPACITY"],
                             max_wait_seconds=app.config["AUDIO_QUEUE_MAX_WAIT_SECONDS"])
        app.extensions["audio_worker"] = worker
        app.extensions["audio_receiver"] = AudioReceiver(app, worker)

    @sock.route("/ws/audio")
    def ws_audio(ws):
        if not _is_authorized(request.headers):
            logger.warning("koneksi /ws/audio ditolak: token Authorization tidak valid")
            ws.close(reason=1008, message="unauthorized")
            return
        connection = app.extensions["audio_receiver"].connection()
        try:
            while True:
                raw_message = ws.receive()
                if raw_message is None:
                    break
                connection.receive(raw_message)
                if connection.closed:
                    ws.close(reason=1008, message="replaced session")
                    break
        finally:
            connection.close()
