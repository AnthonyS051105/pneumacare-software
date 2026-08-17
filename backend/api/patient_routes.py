"""Portal Pasien — SDD_SOFTWARE.md §4.3.

FR-SW-070 (constraint keamanan): semua endpoint `/patient/me/*` mengambil
`patient_id` dari session yang login (via `current_user`), TIDAK PERNAH dari
parameter URL — mencegah satu pasien mengakses data pasien lain.
"""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash

from backend.auth.alert_language import translate_alert
from backend.auth.decorators import role_required
from backend.models import db
from backend.models.alert import Alert
from backend.models.device import Device, DevicePairingCode
from backend.models.patient import Patient
from backend.models.vital import ReadingVital

patient_bp = Blueprint("patient", __name__, url_prefix="/api/v1/patient/me")

_RANGE_TO_TIMEDELTA = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}


def _current_patient() -> Patient | None:
    return db.session.query(Patient).filter_by(user_id=current_user.id).first()


@patient_bp.get("/summary")
@role_required("pasien")
def summary():
    patient = _current_patient()
    if patient is None:
        return jsonify({"error": "data pasien tidak ditemukan"}), 404

    device = db.session.query(Device).filter_by(patient_id=patient.id).first()
    latest_vital = None
    if device is not None:
        latest_vital = (
            db.session.query(ReadingVital)
            .filter_by(device_id=device.device_id)
            .order_by(ReadingVital.timestamp.desc())
            .first()
        )

    latest_alert = (
        db.session.query(Alert)
        .filter_by(patient_id=patient.id)
        .order_by(Alert.created_at.desc())
        .first()
    )
    # FR-SW-065: status traffic-light bahasa awam, BUKAN istilah klinis mentah.
    status_label = "stabil"
    if latest_alert is not None and not latest_alert.acknowledged:
        status_label = "segera_hubungi_dokter" if latest_alert.level == 3 else "perlu_diperhatikan"

    return jsonify(
        {
            "status_label": status_label,
            "device_connected": device.status == "online" if device is not None else False,
            "latest_vitals": {
                "hr": latest_vital.hr if latest_vital else None,
                "spo2": latest_vital.spo2 if latest_vital else None,
                "rr": latest_vital.rr if latest_vital else None,
                "timestamp": latest_vital.timestamp.isoformat() if latest_vital else None,
            },
        }
    )


@patient_bp.get("/history")
@role_required("pasien")
def history():
    patient = _current_patient()
    if patient is None:
        return jsonify({"error": "data pasien tidak ditemukan"}), 404

    range_param = request.args.get("range", "24h")
    delta = _RANGE_TO_TIMEDELTA.get(range_param)
    if delta is None:
        return jsonify({"error": "range harus salah satu dari 24h, 7d, 30d"}), 400

    device = db.session.query(Device).filter_by(patient_id=patient.id).first()
    if device is None:
        return jsonify([])

    since = datetime.now(timezone.utc) - delta
    readings = (
        db.session.query(ReadingVital)
        .filter(ReadingVital.device_id == device.device_id, ReadingVital.timestamp >= since)
        .order_by(ReadingVital.timestamp.asc())
        .all()
    )
    return jsonify(
        [{"hr": r.hr, "spo2": r.spo2, "rr": r.rr, "timestamp": r.timestamp.isoformat()} for r in readings]
    )


@patient_bp.get("/alerts")
@role_required("pasien")
def alerts():
    patient = _current_patient()
    if patient is None:
        return jsonify({"error": "data pasien tidak ditemukan"}), 404

    rows = (
        db.session.query(Alert)
        .filter_by(patient_id=patient.id)
        .order_by(Alert.created_at.desc())
        .all()
    )
    # FR-SW-066: dipetakan lewat alert_language.py, BUKAN triggers teknis mentah.
    return jsonify(
        [
            {
                "id": a.id,
                "created_at": a.created_at.isoformat(),
                "acknowledged": a.acknowledged,
                **translate_alert(a.level, a.triggers),
            }
            for a in rows
        ]
    )


@patient_bp.get("/profile")
@role_required("pasien")
def get_profile():
    patient = _current_patient()
    return jsonify(
        {
            "email": current_user.email,
            "full_name": current_user.full_name,
            "patient_name": patient.name if patient else None,
            "date_of_birth": patient.date_of_birth.isoformat() if patient and patient.date_of_birth else None,
            "device_paired": patient is not None
            and db.session.query(Device).filter_by(patient_id=patient.id).first() is not None,
        }
    )


@patient_bp.put("/profile")
@role_required("pasien")
def update_profile():
    body = request.get_json(silent=True) or {}
    patient = _current_patient()

    if "full_name" in body:
        current_user.full_name = body["full_name"]
        if patient is not None:
            patient.name = body["full_name"]

    if "new_password" in body:
        current_password = body.get("current_password")
        if not current_password or not check_password_hash(current_user.password_hash, current_password):
            return jsonify({"error": "current_password salah"}), 400
        current_user.password_hash = generate_password_hash(body["new_password"])

    db.session.commit()
    return jsonify({"status": "ok"})


@patient_bp.post("/device/repair")
@role_required("pasien")
def repair_device():
    body = request.get_json(silent=True) or {}
    pairing_code = body.get("pairing_code")
    if not pairing_code:
        return jsonify({"error": "pairing_code wajib diisi"}), 400

    patient = _current_patient()
    if patient is None:
        return jsonify({"error": "data pasien tidak ditemukan"}), 404

    pairing = db.session.query(DevicePairingCode).filter_by(pairing_code=pairing_code).first()
    if pairing is None:
        return jsonify({"error": "pairing_code tidak ditemukan"}), 404
    if pairing.used:
        return jsonify({"error": "pairing_code sudah dipakai"}), 409

    pairing.used = True
    pairing.used_by_patient_id = patient.id
    device = db.session.get(Device, pairing.device_id)
    if device is not None:
        device.patient_id = patient.id

    db.session.commit()
    return jsonify({"status": "ok", "device_id": pairing.device_id})
