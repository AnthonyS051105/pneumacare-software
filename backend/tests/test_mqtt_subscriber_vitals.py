import numpy as np

from backend.ingestion import mqtt_subscriber
from backend.ingestion.mqtt_subscriber import _handle_ppg_raw
from backend.models import db
from backend.models.device import Device
from backend.models.vital import ReadingVital

SAMPLE_RATE_HZ = 100


def _synthetic_channel(duration_s: float, hr_bpm: float, dc_level: float, ac_amplitude: float) -> list[float]:
    hz = hr_bpm / 60
    t = np.arange(0, duration_s, 1 / SAMPLE_RATE_HZ)
    cardiac = ac_amplitude * np.sin(2 * np.pi * hz * t)
    return (dc_level + cardiac).tolist()


def _reset_buffers():
    mqtt_subscriber.raw_ppg_buffers.clear()
    mqtt_subscriber._ir_sample_buffers.clear()
    mqtt_subscriber._red_sample_buffers.clear()


def test_accumulates_until_window_then_saves_hr_and_spo2(app):
    _reset_buffers()
    with app.app_context():
        db.session.add(Device(device_id="pneumacare-a1b2", status="online"))
        db.session.commit()

    ir_full = _synthetic_channel(duration_s=16, hr_bpm=72, dc_level=1500, ac_amplitude=15)
    red_full = _synthetic_channel(duration_s=16, hr_bpm=72, dc_level=1000, ac_amplitude=20)

    # dua batch 8 detik (800 sample) — window 15 detik (1500 sample) baru
    # terlampaui setelah batch kedua, meniru publish MQTT berkala dari firmware.
    for start in (0, 800):
        payload = {
            "timestamp_ms": 1723276800000 + start * 10,
            "sample_rate_hz": SAMPLE_RATE_HZ,
            "samples": ir_full[start : start + 800],
            "samples_red": red_full[start : start + 800],
        }
        _handle_ppg_raw(app, "pneumacare-a1b2", payload)

    with app.app_context():
        readings = ReadingVital.query.filter_by(device_id="pneumacare-a1b2").all()

    assert len(readings) == 1
    assert readings[0].hr is not None
    assert abs(readings[0].hr - 72) < 2.0
    assert readings[0].spo2 is not None
    assert readings[0].rr is None


def test_hr_only_when_firmware_omits_red_channel(app):
    _reset_buffers()
    with app.app_context():
        db.session.add(Device(device_id="pneumacare-a1b2", status="online"))
        db.session.commit()

    ir_full = _synthetic_channel(duration_s=16, hr_bpm=72, dc_level=1500, ac_amplitude=15)

    for start in (0, 800):
        payload = {
            "timestamp_ms": 1723276800000 + start * 10,
            "sample_rate_hz": SAMPLE_RATE_HZ,
            "samples": ir_full[start : start + 800],
            # tanpa "samples_red" — firmware lama (sebelum revisi §3.3)
        }
        _handle_ppg_raw(app, "pneumacare-a1b2", payload)

    with app.app_context():
        readings = ReadingVital.query.filter_by(device_id="pneumacare-a1b2").all()

    assert len(readings) == 1
    assert readings[0].hr is not None
    assert readings[0].spo2 is None
