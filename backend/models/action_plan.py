from backend.models import db


class PatientActionPlan(db.Model):
    """Arahan/rencana tindakan individual dari tenaga medis untuk satu pasien.

    🧩 Deviasi dari SDD_SOFTWARE.md §3: tabel ini belum ada di skema SDD, ditambahkan
    karena form "Konfigurasi Ambang" (desain Care First) punya field "Rencana Tindakan
    Pasien" yang sebelumnya hanya tersimpan di localStorage. Dibuat sebagai tabel terpisah
    (bukan kolom baru di `thresholds`) supaya `db.create_all()` bisa membuatnya di database
    yang sudah ada tanpa migrasi ALTER TABLE.
    """

    __tablename__ = "patient_action_plans"

    patient_id = db.Column(db.String(36), db.ForeignKey("patients.id"), primary_key=True)
    text = db.Column(db.Text, nullable=False, default="")
    updated_by = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=True)
