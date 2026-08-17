"""Portal Tenaga Medis — SDD_SOFTWARE.md §4.2.

Semua endpoint di sini WAJIB role `clinician` (FR-SW-059, NFR-SW-007) kecuali
dicatat lain secara eksplisit.
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user

from backend.auth.decorators import role_required
from backend.models import db
from backend.models.alert import Alert
from backend.models.device import Device
from backend.models.patient import Patient
from backend.models.severity import ReadingSeverity
from backend.models.threshold import Threshold
from backend.models.trend import TrendEvent
from backend.models.user import User
from backend.models.vital import ReadingVital

clinician_bp = Blueprint("clinician", __name__, url_prefix="/api/v1")


def _patient_dict(patient: Patient) -> dict:
    latest_alert = (
        db.session.query(Alert)
        .filter_by(patient_id=patient.id)
        .order_by(Alert.level.desc(), Alert.created_at.desc())
        .first()
    )
    return {
        "id": patient.id,
        "name": patient.name,
        "latest_alert_level": latest_alert.level if latest_alert else None,
        "latest_alert_acknowledged": latest_alert.acknowledged if latest_alert else None,
    }


def _require_owned_patient(patient_id: str) -> Patient | tuple:
    """Ambil Patient milik clinician yang login, atau (response, status) bila tidak ditemukan.

    Constraint desain: clinician hanya boleh melihat pasien yang assigned_clinician_id
    miliknya — mencegah satu clinician melihat data pasien clinician lain lewat ID di URL.
    """
    patient = db.session.get(Patient, patient_id)
    if patient is None or patient.assigned_clinician_id != current_user.id:
        return jsonify({"error": "pasien tidak ditemukan"}), 404
    return patient


@clinician_bp.get("/patients")
@role_required("clinician")
def list_patients():
    # FR-SW-057: urut default alert level tertinggi & belum acknowledged di atas.
    patients = db.session.query(Patient).filter_by(assigned_clinician_id=current_user.id).all()
    rows = [_patient_dict(p) for p in patients]
    rows.sort(key=lambda r: (-(r["latest_alert_level"] or 0), r["latest_alert_acknowledged"] is not False))
    return jsonify(rows)


@clinician_bp.post("/patients")
@role_required("clinician")
def add_patient():
    body = request.get_json(silent=True) or {}
    email = body.get("email")
    if not email:
        return jsonify({"error": "email wajib diisi"}), 400

    user = db.session.query(User).filter_by(email=email, role="pasien").first()
    if user is None:
        return jsonify({"error": "tidak ada akun pasien dengan email tersebut"}), 404

    patient = db.session.query(Patient).filter_by(user_id=user.id).first()
    if patient is None:
        return jsonify({"error": "data pasien tidak ditemukan"}), 404

    patient.assigned_clinician_id = current_user.id
    db.session.commit()
    return jsonify(_patient_dict(patient)), 201


@clinician_bp.get("/patients/<patient_id>/vitals/latest")
@role_required("clinician")
def patient_vitals_latest(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient

    device = db.session.query(Device).filter_by(patient_id=patient.id).first()
    if device is None:
        return jsonify({"hr": None, "spo2": None, "rr": None, "timestamp": None})

    latest = (
        db.session.query(ReadingVital)
        .filter_by(device_id=device.device_id)
        .order_by(ReadingVital.timestamp.desc())
        .first()
    )
    if latest is None:
        return jsonify({"hr": None, "spo2": None, "rr": None, "timestamp": None})

    return jsonify(
        {"hr": latest.hr, "spo2": latest.spo2, "rr": latest.rr, "timestamp": latest.timestamp.isoformat()}
    )


@clinician_bp.get("/patients/<patient_id>/vitals/history")
@role_required("clinician")
def patient_vitals_history(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient

    device = db.session.query(Device).filter_by(patient_id=patient.id).first()
    if device is None:
        return jsonify([])

    query = db.session.query(ReadingVital).filter_by(device_id=device.device_id)

    from_param = request.args.get("from")
    to_param = request.args.get("to")
    if from_param:
        query = query.filter(ReadingVital.timestamp >= datetime.fromisoformat(from_param))
    if to_param:
        query = query.filter(ReadingVital.timestamp <= datetime.fromisoformat(to_param))

    readings = query.order_by(ReadingVital.timestamp.asc()).all()
    return jsonify(
        [{"hr": r.hr, "spo2": r.spo2, "rr": r.rr, "timestamp": r.timestamp.isoformat()} for r in readings]
    )


@clinician_bp.get("/patients/<patient_id>/severity/latest")
@role_required("clinician")
def patient_severity_latest(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient

    device = db.session.query(Device).filter_by(patient_id=patient.id).first()
    if device is None:
        return jsonify(None)

    latest = (
        db.session.query(ReadingSeverity)
        .filter_by(device_id=device.device_id)
        .order_by(ReadingSeverity.segment_end.desc())
        .first()
    )
    if latest is None:
        return jsonify(None)

    return jsonify(
        {
            "channel_id": latest.channel_id,
            "segment_start": latest.segment_start.isoformat(),
            "segment_end": latest.segment_end.isoformat(),
            "wheeze_present": latest.wheeze_present,
            "wheeze_confidence": latest.wheeze_confidence,
            "crackle_present": latest.crackle_present,
            "crackle_confidence": latest.crackle_confidence,
            "severity_class": latest.severity_class,
            "model_version": latest.model_version,
        }
    )


@clinician_bp.get("/patients/<patient_id>/trend")
@role_required("clinician")
def patient_trend(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient

    device = db.session.query(Device).filter_by(patient_id=patient.id).first()
    if device is None:
        return jsonify(None)

    latest = (
        db.session.query(TrendEvent)
        .filter_by(device_id=device.device_id)
        .order_by(TrendEvent.window_end.desc())
        .first()
    )
    if latest is None:
        return jsonify(None)

    return jsonify(
        {
            "window_start": latest.window_start.isoformat(),
            "window_end": latest.window_end.isoformat(),
            "slope": latest.slope,
            "significant": latest.significant,
        }
    )


@clinician_bp.get("/patients/<patient_id>/alerts")
@role_required("clinician")
def patient_alerts(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient

    query = db.session.query(Alert).filter_by(patient_id=patient.id)

    level_param = request.args.get("level")
    if level_param:
        query = query.filter(Alert.level == int(level_param))

    from_param = request.args.get("from")
    to_param = request.args.get("to")
    if from_param:
        query = query.filter(Alert.created_at >= datetime.fromisoformat(from_param))
    if to_param:
        query = query.filter(Alert.created_at <= datetime.fromisoformat(to_param))

    alerts = query.order_by(Alert.created_at.desc()).all()
    return jsonify([_alert_dict(a) for a in alerts])


def _alert_dict(alert: Alert) -> dict:
    return {
        "id": alert.id,
        "device_id": alert.device_id,
        "patient_id": alert.patient_id,
        "level": alert.level,
        "triggers": alert.triggers,
        "created_at": alert.created_at.isoformat(),
        "acknowledged": alert.acknowledged,
        "acknowledged_by": alert.acknowledged_by,
        "acknowledged_at": alert.acknowledged_at.isoformat() if alert.acknowledged_at else None,
    }


@clinician_bp.get("/clinician/alerts")
@role_required("clinician")
def clinician_alerts():
    # FR-SW-058: Alert Center lintas-pasien milik clinician yang login.
    patient_ids = [
        p.id for p in db.session.query(Patient).filter_by(assigned_clinician_id=current_user.id).all()
    ]
    query = db.session.query(Alert).filter(Alert.patient_id.in_(patient_ids))

    level_param = request.args.get("level")
    if level_param:
        query = query.filter(Alert.level == int(level_param))

    patient_id_param = request.args.get("patient_id")
    if patient_id_param:
        query = query.filter(Alert.patient_id == patient_id_param)

    acknowledged_param = request.args.get("acknowledged")
    if acknowledged_param is not None:
        query = query.filter(Alert.acknowledged == (acknowledged_param.lower() == "true"))

    alerts = query.order_by(Alert.created_at.desc()).all()
    return jsonify([_alert_dict(a) for a in alerts])


@clinician_bp.get("/patients/<patient_id>/thresholds")
@role_required("clinician")
def get_thresholds(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient

    threshold = db.session.get(Threshold, patient.id)
    if threshold is None:
        return jsonify(
            {"hr_min": None, "hr_max": None, "spo2_min": None, "rr_min": None, "rr_max": None}
        )

    return jsonify(
        {
            "hr_min": threshold.hr_min,
            "hr_max": threshold.hr_max,
            "spo2_min": threshold.spo2_min,
            "rr_min": threshold.rr_min,
            "rr_max": threshold.rr_max,
            "trend_significance_threshold": threshold.trend_significance_threshold,
            "updated_by": threshold.updated_by,
            "updated_at": threshold.updated_at.isoformat() if threshold.updated_at else None,
        }
    )


@clinician_bp.put("/patients/<patient_id>/thresholds")
@role_required("clinician")
def update_thresholds(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient

    body = request.get_json(silent=True) or {}

    threshold = db.session.get(Threshold, patient.id)
    if threshold is None:
        threshold = Threshold(patient_id=patient.id)
        db.session.add(threshold)

    for field in ("hr_min", "hr_max", "spo2_min", "rr_min", "rr_max", "trend_significance_threshold"):
        if field in body:
            setattr(threshold, field, body[field])

    threshold.updated_by = current_user.id
    threshold.updated_at = datetime.now(timezone.utc)
    db.session.commit()

    return jsonify(
        {
            "hr_min": threshold.hr_min,
            "hr_max": threshold.hr_max,
            "spo2_min": threshold.spo2_min,
            "rr_min": threshold.rr_min,
            "rr_max": threshold.rr_max,
            "trend_significance_threshold": threshold.trend_significance_threshold,
            "updated_by": threshold.updated_by,
            "updated_at": threshold.updated_at.isoformat(),
        }
    )


@clinician_bp.get("/devices/<device_id>/status")
@role_required("clinician")
def device_status(device_id: str):
    device = db.session.get(Device, device_id)
    if device is None:
        return jsonify({"error": "device tidak ditemukan"}), 404

    return jsonify(
        {
            "device_id": device.device_id,
            "status": device.status,
            "last_seen_at": device.last_seen_at.isoformat() if device.last_seen_at else None,
            "battery_percent": device.battery_percent,
        }
    )


@clinician_bp.get("/clinician/profile")
@role_required("clinician")
def get_clinician_profile():
    return jsonify(
        {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "specialization": current_user.specialization,
            "institution": current_user.institution,
            "str_sip_number": current_user.str_sip_number,
        }
    )


@clinician_bp.put("/clinician/profile")
@role_required("clinician")
def update_clinician_profile():
    body = request.get_json(silent=True) or {}
    for field in ("full_name", "specialization", "institution", "str_sip_number"):
        if field in body:
            setattr(current_user, field, body[field])
    db.session.commit()

    return jsonify(
        {
            "id": current_user.id,
            "email": current_user.email,
            "full_name": current_user.full_name,
            "specialization": current_user.specialization,
            "institution": current_user.institution,
            "str_sip_number": current_user.str_sip_number,
        }
    )
