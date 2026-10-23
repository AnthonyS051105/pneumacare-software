from backend.models import db


class ReadingClassification(db.Model):
    """Hasil klasifikasi suara paru per segmen 5 detik (Model A, 2 kelas).

    `predicted_class` berisi "normal" atau "abnormal" sesuai output ML service.
    Model B (severity) tetap ditunda dan disimpan di kolom `severity_*`.
    """

    __tablename__ = "readings_classification"

    id = db.Column(db.String(36), primary_key=True)  # = segment_id di kontrak §4.1
    device_id = db.Column(db.String(64), db.ForeignKey("devices.device_id"), nullable=False)
    channel_id = db.Column(db.Integer, nullable=False)
    segment_start = db.Column(db.DateTime, nullable=False)
    segment_end = db.Column(db.DateTime, nullable=False)

    # Model A — 2 kelas: normal/abnormal
    predicted_class = db.Column(db.String(16), nullable=False)  # "normal" | "abnormal"
    confidence = db.Column(db.Float, nullable=False)  # fraksi 0-1
    probabilities = db.Column(db.JSON, nullable=True)  # {"normal": 0-1, "abnormal": 0-1}
    model_version = db.Column(db.String(64), nullable=False)

    # Model B — severity PPOK, 🔓⏸️ DITUNDA (INTEGRATION_CONTRACT.md §4.2). Nullable
    # karena model belum tersedia — JANGAN isi nilai sampai Model B benar-benar
    # terintegrasi (di luar scope checkpoint 50%).
    severity_class = db.Column(db.String(64), nullable=True)
    severity_confidence = db.Column(db.Float, nullable=True)
    severity_model_version = db.Column(db.String(64), nullable=True)
