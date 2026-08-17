from backend.models import db


class ReadingClassification(db.Model):
    """🔄 Direstrukturisasi 2026-08-17 (dulu `ReadingSeverity`/`readings_severity`) —
    mengikuti kontrak Model A/B di INTEGRATION_CONTRACT.md §4, SDD_SOFTWARE.md §3.
    Kolom `wheeze_present`/`crackle_present` boolean terpisah versi sebelumnya
    DIHAPUS — tidak sesuai output model aktual yang single-label 4-kelas.
    """

    __tablename__ = "readings_classification"

    id = db.Column(db.String(36), primary_key=True)  # = segment_id di kontrak §4.1
    device_id = db.Column(db.String(64), db.ForeignKey("devices.device_id"), nullable=False)
    channel_id = db.Column(db.Integer, nullable=False)
    segment_start = db.Column(db.DateTime, nullable=False)
    segment_end = db.Column(db.DateTime, nullable=False)

    # Model A — wheeze/crackle, ✅ terverifikasi (INTEGRATION_CONTRACT.md §4.1)
    wheeze_crackle_class = db.Column(db.String(16), nullable=False)  # enum: none, crackle, wheeze, both
    wheeze_crackle_confidence = db.Column(db.Float, nullable=False)  # fraksi 0-1
    wheeze_crackle_probabilities = db.Column(db.JSON, nullable=True)  # 4 nilai, fraksi 0-1
    wheeze_crackle_model_version = db.Column(db.String(64), nullable=False)

    # Model B — severity PPOK, 🔓⏸️ DITUNDA (INTEGRATION_CONTRACT.md §4.2). Nullable
    # karena model belum tersedia — JANGAN isi nilai sampai Model B benar-benar
    # terintegrasi (di luar scope checkpoint 50%).
    severity_class = db.Column(db.String(64), nullable=True)
    severity_confidence = db.Column(db.Float, nullable=True)
    severity_model_version = db.Column(db.String(64), nullable=True)
