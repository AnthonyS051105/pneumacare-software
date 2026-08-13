import uuid

from backend.models import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # enum: pasien, clinician, admin
    full_name = db.Column(db.String(255), nullable=False)
    specialization = db.Column(db.String(255), nullable=True)
    institution = db.Column(db.String(255), nullable=True)
    # ⚠️ Field teks bebas tanpa verifikasi — BUKAN verifikasi profesi sungguhan (SDD_SOFTWARE.md §3)
    str_sip_number = db.Column(db.String(100), nullable=True)
