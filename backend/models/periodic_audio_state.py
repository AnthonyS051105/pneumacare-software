"""Constant-size persistence state per measured microphone; no PCM stored here."""
from backend.models import db


class PeriodicAudioState(db.Model):
    __tablename__ = 'periodic_audio_state'

    device_id = db.Column(db.String(64), db.ForeignKey('devices.device_id'), primary_key=True)
    channel_id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patients.id'), nullable=False)
    stream_id = db.Column(db.String(64), nullable=False)
    reception_session_id = db.Column(db.String(36), nullable=True)
    model_version = db.Column(db.String(64), nullable=False)
    last_capture_id = db.Column(db.BigInteger, nullable=False)
    last_start_ms = db.Column(db.BigInteger, nullable=False)
    last_received_at = db.Column(db.DateTime, nullable=False)
    consecutive_abnormal = db.Column(db.Integer, nullable=False)
    evidence = db.Column(db.JSON, nullable=False)
