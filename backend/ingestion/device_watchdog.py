"""Penanda perangkat offline berbasis timeout heartbeat (FR-SW-004).

Rompi yang mati mendadak (baterai habis, keluar jangkauan WiFi) tidak sempat mengirim status
"offline" — tanpa watchdog ini dashboard akan terus menampilkan "terhubung" selamanya.
Perangkat dianggap offline bila tidak ada pesan apa pun (status/PPG/audio, semuanya memperbarui
`last_seen_at` lewat device_registry.upsert_device_seen) lebih lama dari
`DEVICE_OFFLINE_TIMEOUT_SECONDS`.

Logika murni (`find_stale_devices`) dipisah dari I/O (`mark_stale_devices_offline`) dan dari
thread periodik (`start_device_watchdog`), sesuai pola modul lain.
"""

import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from backend.models import db
from backend.models.device import Device, DeviceStatusLog

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeviceSeen:
    device_id: str
    status: str
    last_seen_at: datetime | None


def find_stale_devices(devices: list[DeviceSeen], now: datetime, timeout_seconds: float) -> list[str]:
    """device_id yang masih tercatat "online" tetapi pesan terakhirnya lebih tua dari timeout.

    Perangkat "online" tanpa `last_seen_at` sama sekali juga dianggap basi — status online
    tanpa bukti heartbeat tidak boleh dipercaya.
    """
    cutoff = now - timedelta(seconds=timeout_seconds)
    return [
        d.device_id
        for d in devices
        if d.status == "online" and (d.last_seen_at is None or d.last_seen_at < cutoff)
    ]


def mark_stale_devices_offline(app, now: datetime | None = None) -> list[str]:
    """Tandai perangkat basi sebagai offline + catat di device_status_log. Return id yang diubah."""
    now = (now or datetime.now(timezone.utc)).replace(tzinfo=None)  # kolom DB = naive UTC
    timeout = app.config["DEVICE_OFFLINE_TIMEOUT_SECONDS"]
    with app.app_context():
        online = db.session.query(Device).filter_by(status="online").all()
        stale = find_stale_devices(
            [
                DeviceSeen(
                    d.device_id,
                    d.status,
                    d.last_seen_at.replace(tzinfo=None) if d.last_seen_at and d.last_seen_at.tzinfo else d.last_seen_at,
                )
                for d in online
            ],
            now,
            timeout,
        )
        for device in online:
            if device.device_id in stale:
                device.status = "offline"
                db.session.add(DeviceStatusLog(device_id=device.device_id, status="offline", changed_at=now))
        if stale:
            db.session.commit()
            logger.info("perangkat ditandai offline (tanpa heartbeat > %ss): %s", timeout, ", ".join(stale))
        return stale


def start_device_watchdog(app, interval_seconds: float | None = None) -> threading.Event:
    """Jalankan pengecekan berkala di thread daemon. Return Event untuk menghentikannya."""
    stop = threading.Event()
    interval = interval_seconds or max(5.0, app.config["DEVICE_OFFLINE_TIMEOUT_SECONDS"] / 3)

    def loop():
        while not stop.wait(interval):
            try:
                mark_stale_devices_offline(app)
            except Exception:  # NFR-SW-002: watchdog tidak boleh menjatuhkan backend
                logger.exception("device watchdog gagal; dicoba lagi pada interval berikutnya")

    threading.Thread(target=loop, name="device-watchdog", daemon=True).start()
    return stop
