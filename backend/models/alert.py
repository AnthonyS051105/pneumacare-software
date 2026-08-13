import uuid

from backend.models import db


class Alert(db.Model):
    __tablename__ = "alerts"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = db.Column(db.String(64), db.ForeignKey("devices.device_id"), nullable=False)
    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), nullable=False)
    level = db.Column(db.Integer, nullable=False)  # 1/2/3
    triggers = db.Column(db.JSON, nullable=False)  # array, lihat INTEGRATION_CONTRACT.md §5
    created_at = db.Column(db.DateTime, nullable=False)
    acknowledged = db.Column(db.Boolean, nullable=False, default=False)
    acknowledged_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    acknowledged_at = db.Column(db.DateTime, nullable=True)
