"""MQTT subscriber untuk kanal PPG + status device (FR-SW-003, FR-SW-004).

Subscribe ke `pneumacare/{device_id}/ppg/raw` dan `pneumacare/{device_id}/status`
sesuai INTEGRATION_CONTRACT.md §3. Dijalankan di background thread terpisah dari
Flask dev server request-handling thread (paho-mqtt `loop_start()`).
"""

import json
import logging
import uuid
from collections import deque
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from backend.alerting.alert_engine import VitalReading
from backend.alerting.alert_service import evaluate_and_save_alert
from backend.ingestion.device_registry import upsert_device_seen
from backend.models import db
from backend.models.device import Device, DeviceStatusLog
from backend.models.vital import ReadingVital
from backend.vitals.vitals_service import compute_vitals_from_ppg_batch

logger = logging.getLogger(__name__)

TOPIC_PPG_RAW = "pneumacare/+/ppg/raw"
TOPIC_STATUS = "pneumacare/+/status"

# ⚠️ Belum ada tabel DB untuk raw PPG samples di SDD_SOFTWARE.md §3 — skema yang ada
# (`readings_vital`) hanya menyimpan HR/SpO2/RR yang SUDAH diturunkan, bukan sample mentah.
# Buffer in-memory ini sementara menampung raw samples per device untuk dikonsumsi modul
# bandpass_filter/hr_estimator/spo2_estimator — TIDAK persisted, hilang saat restart.
# Kapasitas dibatasi (maxlen) supaya tidak bocor memori.
_RAW_PPG_BUFFER_MAXLEN = 6000  # ~60 detik pada 100 Hz (asumsi contoh §3.3, ⚠️ belum final)
raw_ppg_buffers: dict[str, deque[dict]] = {}

# 🧩 Panjang window akumulasi sebelum estimasi HR/SpO2 dijalankan — dipilih 15 detik
# (bukan nilai klinis, murni cukup siklus jantung untuk deteksi puncak stabil, sama
# orde besaran dengan window yang dipakai test_hr_estimator.py). TODO_NATHANAEL_CONFIRM
# tidak berlaku (bukan domain model AI), tapi tetap operasional/tuning, bukan final.
_VITALS_WINDOW_SECONDS = 15
_ir_sample_buffers: dict[str, list[float]] = {}
_red_sample_buffers: dict[str, list[float] | None] = {}


def _run_vitals_estimation(app, device_id: str, sample_rate_hz: float) -> None:
    samples_ir = _ir_sample_buffers.get(device_id, [])
    samples_red = _red_sample_buffers.get(device_id)

    cfg = app.config
    try:
        hr_estimate, spo2_estimate = compute_vitals_from_ppg_batch(
            samples_ir=samples_ir,
            samples_red=samples_red,
            sample_rate_hz=sample_rate_hz,
            cardiac_bandpass_low_hz=cfg["CARDIAC_BANDPASS_LOW_HZ"],
            cardiac_bandpass_high_hz=cfg["CARDIAC_BANDPASS_HIGH_HZ"],
            bandpass_order=cfg["BANDPASS_FILTER_ORDER"],
            hr_plausible_min_bpm=cfg["HR_PLAUSIBLE_MIN_BPM"],
            hr_plausible_max_bpm=cfg["HR_PLAUSIBLE_MAX_BPM"],
            spo2_calibration_coeff_a=cfg["SPO2_CALIBRATION_COEFF_A"],
            spo2_calibration_coeff_b=cfg["SPO2_CALIBRATION_COEFF_B"],
            spo2_plausible_min_percent=cfg["SPO2_PLAUSIBLE_MIN_PERCENT"],
            spo2_plausible_max_percent=cfg["SPO2_PLAUSIBLE_MAX_PERCENT"],
        )
    except ValueError as exc:
        logger.warning("gagal estimasi vitals device=%s: %s", device_id, exc)
        return

    # confidence="poor" TETAP disimpan (bukan di-skip) — dashboard/analisis boleh
    # tahu ada bacaan tapi tidak diyakini, bukan diam-diam kehilangan titik data.
    with app.app_context():
        db.session.add(
            ReadingVital(
                id=str(uuid.uuid4()),
                device_id=device_id,
                timestamp=datetime.now(timezone.utc),
                hr=hr_estimate.hr_bpm,
                spo2=spo2_estimate.spo2_percent if spo2_estimate is not None else None,
                rr=None,  # lihat docstring vitals_service.py — sumber sinyal RR belum ditentukan
            )
        )
        db.session.commit()
    logger.info(
        "vitals dihitung device=%s hr=%s(%s) spo2=%s(%s)",
        device_id,
        hr_estimate.hr_bpm,
        hr_estimate.confidence,
        spo2_estimate.spo2_percent if spo2_estimate is not None else None,
        spo2_estimate.confidence if spo2_estimate is not None else "n/a",
    )

    # Alert engine HANYA menerima nilai confidence="good" — sinyal "poor" (mis. deteksi
    # puncak gagal, SNR rendah) tetap disimpan di ReadingVital untuk transparansi data,
    # TAPI tidak boleh memicu evaluasi threshold (mencegah alert palsu dari sinyal buruk).
    hr_for_alert = hr_estimate.hr_bpm if hr_estimate.confidence == "good" else None
    spo2_for_alert = (
        spo2_estimate.spo2_percent if spo2_estimate is not None and spo2_estimate.confidence == "good" else None
    )
    if hr_for_alert is not None or spo2_for_alert is not None:
        with app.app_context():
            evaluate_and_save_alert(
                app,
                device_id=device_id,
                vitals=VitalReading(hr=hr_for_alert, spo2=spo2_for_alert, rr=None),
                trend_result=None,
            )


def _handle_ppg_raw(app, device_id: str, payload: dict) -> None:
    buffer = raw_ppg_buffers.setdefault(device_id, deque(maxlen=_RAW_PPG_BUFFER_MAXLEN))
    buffer.append(
        {
            "timestamp_ms": payload.get("timestamp_ms"),
            "sample_rate_hz": payload.get("sample_rate_hz"),
            "samples": payload.get("samples", []),
        }
    )

    sample_rate_hz = payload.get("sample_rate_hz") or app.config.get("PPG_SAMPLE_RATE_HZ_DEFAULT", 100)
    samples_ir = payload.get("samples", [])
    samples_red = payload.get("samples_red")  # None bila firmware belum update (§3.3 revisi)

    ir_acc = _ir_sample_buffers.setdefault(device_id, [])
    ir_acc.extend(samples_ir)

    # samples_red hanya diakumulasi bila SEMUA batch dari device ini membawanya —
    # sekali None terlihat, device ini dianggap firmware lama untuk sesi ini
    # (jangan campur batch dengan/tanpa red, index jadi tidak sejajar).
    if device_id not in _red_sample_buffers:
        _red_sample_buffers[device_id] = list(samples_red) if samples_red is not None else None
    elif _red_sample_buffers[device_id] is not None:
        if samples_red is not None:
            _red_sample_buffers[device_id].extend(samples_red)
        else:
            _red_sample_buffers[device_id] = None

    window_size = int(_VITALS_WINDOW_SECONDS * sample_rate_hz)
    if len(ir_acc) >= window_size:
        _run_vitals_estimation(app, device_id, sample_rate_hz)
        _ir_sample_buffers[device_id] = []
        if _red_sample_buffers.get(device_id) is not None:
            _red_sample_buffers[device_id] = []

    with app.app_context():
        upsert_device_seen(device_id)


def _handle_status(app, device_id: str, payload: dict) -> None:
    status = payload.get("status")
    battery_pct = payload.get("battery_pct")

    if status not in ("online", "offline"):
        logger.warning("status device tidak valid dari %s: %s", device_id, status)
        return

    with app.app_context():
        # NOTE: masih ada celah TOCTOU kecil antara SELECT dan upsert di bawah kalau dua
        # pesan status untuk device_id yang sama diproses persis bersamaan (mqtt_subscriber
        # jalan di satu thread paho-mqtt, jadi risiko ini rendah untuk 1 broker + 1 device
        # skala demo kompetisi). Device baru sendiri sudah aman dari race lewat upsert_device_seen.
        previous = db.session.get(Device, device_id)
        previous_status = previous.status if previous is not None else None

        extra_fields = {"status": status}
        if battery_pct is not None:
            extra_fields["battery_percent"] = battery_pct
        upsert_device_seen(device_id, **extra_fields)

        if previous_status != status:
            db.session.add(
                DeviceStatusLog(
                    device_id=device_id,
                    status=status,
                    changed_at=datetime.now(timezone.utc),
                )
            )
            db.session.commit()


def _extract_device_id(topic: str) -> str | None:
    parts = topic.split("/")
    if len(parts) < 2:
        return None
    return parts[1]


def create_mqtt_client(app) -> mqtt.Client:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    username = app.config.get("MQTT_USERNAME")
    password = app.config.get("MQTT_PASSWORD")
    if username:
        # Kredensial client subscriber backend sendiri ke broker — sesuai INTEGRATION_CONTRACT.md
        # §6, broker (mosquitto.conf) sekarang allow_anonymous false, jadi ini WAJIB diisi
        # (lihat backend/mosquitto/README.md untuk cara generate password_file & user ini).
        client.username_pw_set(username, password or None)
    else:
        logger.warning(
            "MQTT_USERNAME kosong — broker sudah allow_anonymous false, koneksi subscriber "
            "backend kemungkinan akan ditolak. Lihat backend/mosquitto/README.md"
        )

    def on_connect(client, userdata, flags, reason_code, properties=None):
        if reason_code != 0:
            logger.error("gagal konek ke MQTT broker: %s", reason_code)
            return
        logger.info("terhubung ke MQTT broker, subscribe topik ppg/raw dan status")
        client.subscribe(TOPIC_PPG_RAW)
        client.subscribe(TOPIC_STATUS)

    def on_message(client, userdata, msg):
        device_id = _extract_device_id(msg.topic)
        if device_id is None:
            logger.warning("topik MQTT tidak dikenali: %s", msg.topic)
            return

        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning("payload MQTT bukan JSON valid di topik %s", msg.topic)
            return

        if msg.topic.endswith("/ppg/raw"):
            _handle_ppg_raw(app, device_id, payload)
        elif msg.topic.endswith("/status"):
            _handle_status(app, device_id, payload)

    def on_disconnect(client, userdata, flags, reason_code, properties=None):
        logger.warning("terputus dari MQTT broker: %s", reason_code)

    client.on_connect = on_connect
    client.on_message = on_message
    client.on_disconnect = on_disconnect
    return client


def start_mqtt_subscriber(app) -> mqtt.Client:
    """Buat client, connect, dan mulai background loop. Tidak raise bila broker belum jalan
    (NFR-SW-002: backend tidak boleh crash) — retry ditangani otomatis oleh paho-mqtt loop.
    """
    client = create_mqtt_client(app)
    host = app.config["MQTT_BROKER_HOST"]
    port = app.config["MQTT_BROKER_PORT"]
    try:
        client.connect(host, port)
    except (ConnectionRefusedError, OSError) as exc:
        logger.warning("Mosquitto belum bisa dihubungi di %s:%s (%s) — akan retry otomatis", host, port, exc)
    client.loop_start()
    return client
