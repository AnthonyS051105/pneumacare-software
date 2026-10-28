import uuid

from backend.models import db


class ReadingVital(db.Model):
    __tablename__ = "readings_vital"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = db.Column(db.String(64), db.ForeignKey("devices.device_id"), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False)
    hr = db.Column(db.Float, nullable=True)
    spo2 = db.Column(db.Float, nullable=True)
    # ⚠️ ekstraksi RR dari sinyal apa belum eksplisit — cek PPG vs audio (SDD_SOFTWARE.md §3)
    rr = db.Column(db.Float, nullable=True)

    # NULL = unknown (legacy rows), never implicitly trusted for alerts.
    hr_confidence = db.Column(db.String(16), nullable=True)
    spo2_confidence = db.Column(db.String(16), nullable=True)
    rr_confidence = db.Column(db.String(16), nullable=True)
