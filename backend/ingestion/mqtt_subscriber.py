"""MQTT subscriber untuk kanal PPG + status device (FR-SW-003, FR-SW-004).

Subscribe ke `pneumacare/{device_id}/ppg/raw` dan `pneumacare/{device_id}/status`
sesuai INTEGRATION_CONTRACT.md §3. Dijalankan di background thread terpisah dari
Flask dev server request-handling thread (paho-mqtt `loop_start()`).
"""

import json
import logging
from collections import deque
from datetime import datetime, timezone

import paho.mqtt.client as mqtt

from backend.ingestion.device_registry import upsert_device_seen
from backend.models import db
from backend.models.device import Device, DeviceStatusLog

logger = logging.getLogger(__name__)

TOPIC_PPG_RAW = "pneumacare/+/ppg/raw"
TOPIC_STATUS = "pneumacare/+/status"

# ⚠️ Belum ada tabel DB untuk raw PPG samples di SDD_SOFTWARE.md §3 — skema yang ada
# (`readings_vital`) hanya menyimpan HR/SpO2/RR yang SUDAH diturunkan, bukan sample mentah.
# Buffer in-memory ini sementara menampung raw samples per device untuk dikonsumsi modul
# bandpass_filter/hr_estimator/spo2_estimator di Fase 2 — TIDAK persisted, hilang saat restart.
# Kapasitas dibatasi (maxlen) supaya tidak bocor memori kalau Fase 2 belum jalan.
_RAW_PPG_BUFFER_MAXLEN = 6000  # ~60 detik pada 100 Hz (asumsi contoh §3.3, ⚠️ belum final)
raw_ppg_buffers: dict[str, deque[dict]] = {}


def _handle_ppg_raw(app, device_id: str, payload: dict) -> None:
    buffer = raw_ppg_buffers.setdefault(device_id, deque(maxlen=_RAW_PPG_BUFFER_MAXLEN))
    buffer.append(
        {
            "timestamp_ms": payload.get("timestamp_ms"),
            "sample_rate_hz": payload.get("sample_rate_hz"),
            "samples": payload.get("samples", []),
        }
    )

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
        # TODO_AUTH_NOT_IMPLEMENTED: lihat INTEGRATION_CONTRACT.md §6 — auth device belum
        # diwajibkan, ini hanya dipakai kalau broker dikonfigurasi butuh username/password.
        client.username_pw_set(username, password or None)

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
