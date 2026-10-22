"""Bentuk JSON yang dipakai bersama oleh lebih dari satu blueprint."""

from datetime import datetime

from backend.models.device import Device


def iso_or_none(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def device_dict(device: Device | None) -> dict | None:
    if device is None:
        return None
    return {
        "device_id": device.device_id,
        "status": device.status,
        "battery_percent": device.battery_percent,
        "last_seen_at": iso_or_none(device.last_seen_at),
        "signal_quality_ppg": device.signal_quality_ppg,
        "signal_quality_audio": device.signal_quality_audio,
    }
