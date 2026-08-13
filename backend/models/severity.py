from backend.models import db


class ReadingSeverity(db.Model):
    __tablename__ = "readings_severity"

    id = db.Column(db.String(36), primary_key=True)  # = segment_id di INTEGRATION_CONTRACT.md §4
    device_id = db.Column(db.String(64), db.ForeignKey("devices.device_id"), nullable=False)
    channel_id = db.Column(db.Integer, nullable=False)
    segment_start = db.Column(db.DateTime, nullable=False)
    segment_end = db.Column(db.DateTime, nullable=False)
    wheeze_present = db.Column(db.Boolean, nullable=False)
    wheeze_confidence = db.Column(db.Float, nullable=False)
    crackle_present = db.Column(db.Boolean, nullable=False)
    crackle_confidence = db.Column(db.Float, nullable=False)
    # 🔓 nilai enum menunggu definisi Nathanael (INTEGRATION_CONTRACT.md §4)
    severity_class = db.Column(db.String(64), nullable=True)
    model_version = db.Column(db.String(64), nullable=False)
