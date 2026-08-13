from backend.models import db


class Threshold(db.Model):
    __tablename__ = "thresholds"

    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), primary_key=True)
    # ⚠️ Semua nilai di bawah adalah placeholder — lihat config.py dan
    # INTEGRATION_CONTRACT.md §0. JANGAN diisi angka medis tanpa rujukan.
    hr_min = db.Column(db.Float, nullable=True)  # TODO_CLINICAL_VALUE
    hr_max = db.Column(db.Float, nullable=True)  # TODO_CLINICAL_VALUE
    spo2_min = db.Column(db.Float, nullable=True)  # TODO_CLINICAL_VALUE
    rr_min = db.Column(db.Float, nullable=True)  # TODO_CLINICAL_VALUE
    rr_max = db.Column(db.Float, nullable=True)  # TODO_CLINICAL_VALUE
    trend_significance_threshold = db.Column(db.Float, nullable=True)  # TODO_NATHANAEL_CONFIRM
    updated_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)
