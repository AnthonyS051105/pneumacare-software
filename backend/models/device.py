import uuid

from backend.models import db


class Device(db.Model):
    __tablename__ = "devices"

    device_id = db.Column(db.String(64), primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=True)
    last_seen_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), nullable=False, default="offline")  # enum: online, offline
    # 🧩 nullable — perlu cek dulu apakah ESP32 sudah mengukur level baterai Li-Po (SDD_SOFTWARE.md §3)
    battery_percent = db.Column(db.Float, nullable=True)
    # 🧩 per-kanal: {"ant_l": "good|fair|poor", "ant_r": ..., "post_l": ..., "post_r": ...}
    signal_quality_audio = db.Column(db.JSON, nullable=True)
    signal_quality_ppg = db.Column(db.String(10), nullable=True)  # enum: good, fair, poor


class DeviceStatusLog(db.Model):
    __tablename__ = "device_status_log"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = db.Column(db.String(64), db.ForeignKey("devices.device_id"), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # enum: online, offline
    changed_at = db.Column(db.DateTime, nullable=False)


class DevicePairingCode(db.Model):
    __tablename__ = "device_pairing_codes"

    device_id = db.Column(db.String(64), db.ForeignKey("devices.device_id"), primary_key=True)
    pairing_code = db.Column(db.String(64), unique=True, nullable=False)
    used = db.Column(db.Boolean, nullable=False, default=False)
    used_by_patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=True)
