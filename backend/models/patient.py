import uuid

from backend.models import db


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True, unique=True)
    name = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=True)
    assigned_clinician_id = db.Column(db.String(36), db.ForeignKey("users.id"), nullable=True)
