import uuid

from backend.models import db


class TrendEvent(db.Model):
    __tablename__ = "trend_events"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    device_id = db.Column(db.String(64), db.ForeignKey("devices.device_id"), nullable=False)
    window_start = db.Column(db.DateTime, nullable=False)
    window_end = db.Column(db.DateTime, nullable=False)
    slope = db.Column(db.Float, nullable=False)
    significant = db.Column(db.Boolean, nullable=False)
