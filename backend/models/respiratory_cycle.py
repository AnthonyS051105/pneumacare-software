import uuid
from datetime import datetime, timezone

from backend.models import db


class RespiratoryCycle(db.Model):
    """Metadata deteksi siklus napas untuk satu hasil klasifikasi.

    Satu baris dibuat untuk setiap baris `readings_classification`, baik hasil
    klasifikasi per siklus maupun fallback seluruh segmen 5 detik. Untuk fallback,
    `cycle_index`/`cycle_start_ms`/`cycle_end_ms` NULL dan `detection_status`
    menjelaskan alasannya.
    """

    __tablename__ = "respiratory_cycles"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    classification_id = db.Column(
        db.String(36),
        db.ForeignKey("readings_classification.id"),
        nullable=False,
        unique=True,
    )
    device_id = db.Column(db.String(64), db.ForeignKey("devices.device_id"), nullable=False)
    channel_id = db.Column(db.Integer, nullable=False)

    # Segmen analisis 5 detik dari mana siklus dideteksi.
    analysis_start = db.Column(db.DateTime, nullable=False)
    analysis_end = db.Column(db.DateTime, nullable=False)

    detection_status = db.Column(db.String(32), nullable=False)
    cycle_index = db.Column(db.Integer, nullable=True)
    cycle_start_ms = db.Column(db.BigInteger, nullable=True)  # epoch ms absolut
    cycle_end_ms = db.Column(db.BigInteger, nullable=True)  # epoch ms absolut

    mean_dtw = db.Column(db.Float, nullable=True)
    dtw_score = db.Column(db.Float, nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
