"""Portal Tenaga Medis — SDD_SOFTWARE.md §4.2.

Semua endpoint di sini WAJIB role `clinician` (FR-SW-059, NFR-SW-007) kecuali
dicatat lain secara eksplisit.
"""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash

from backend.analytics.classification_history import ClassifiedSegment, bucket_classifications
from backend.api.serializers import device_dict, iso_or_none
from backend.auth.decorators import role_required
from backend.models import db
from backend.models.action_plan import PatientActionPlan
from backend.models.alert import Alert
from backend.models.device import Device
from backend.models.patient import Patient
from backend.models.classification import ReadingClassification
from backend.models.threshold import Threshold
from backend.models.trend import TrendEvent
from backend.models.user import User
from backend.models.vital import ReadingVital
from backend.ingestion.capture_evidence import latest_capture_evidence

clinician_bp = Blueprint("clinician", __name__, url_prefix="/api/v1")

MIN_PASSWORD_LENGTH = 8

# Rentang riwayat klasifikasi dan lebar bucket-nya (FR-SW-053). Lebar bucket dipilih
# supaya grafik tetap ~24-30 titik, bukan nilai klinis.
_HISTORY_RANGES = {
    "24h": (timedelta(hours=24), timedelta(hours=1)),
    "7d": (timedelta(days=7), timedelta(hours=6)),
    "30d": (timedelta(days=30), timedelta(days=1)),
}

THRESHOLD_FIELDS = ("hr_min", "hr_max", "spo2_min", "rr_min", "rr_max", "trend_significance_threshold")


class _BadRequest(Exception):
    pass


def _parse_datetime_param(name: str) -> datetime | None:
    """Query param ISO-8601 -> naive UTC (kolom DB disimpan naive UTC). 400 bila format salah."""
    raw = request.args.get(name)
    if not raw:
        return None
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise _BadRequest(f"{name} harus berformat ISO-8601") from exc
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


def _parse_level_param() -> int | None:
    raw = request.args.get("level")
    if not raw:
        return None
    if raw not in ("1", "2", "3"):
        raise _BadRequest("level harus 1, 2, atau 3")
    return int(raw)


@clinician_bp.errorhandler(_BadRequest)
def _handle_bad_request(error: _BadRequest):
    return jsonify({"error": str(error)}), 400


def _patient_dict(patient: Patient) -> dict:
    latest_alert = (
        db.session.query(Alert)
        .filter_by(patient_id=patient.id)
        .order_by(Alert.level.desc(), Alert.created_at.desc())
        .first()
    )
    # Status pasien di daftar mengikuti alert yang BELUM ditinjau dengan level tertinggi —
    # alert lama yang sudah di-acknowledge tidak boleh membuat pasien tetap tampil "urgent".
    open_alert = (
        db.session.query(Alert)
        .filter_by(patient_id=patient.id, acknowledged=False)
        .order_by(Alert.level.desc(), Alert.created_at.desc())
        .first()
    )
    device = db.session.query(Device).filter_by(patient_id=patient.id).first()
    latest_vital = (
        db.session.query(ReadingVital)
        .filter_by(device_id=device.device_id)
        .order_by(ReadingVital.timestamp.desc())
        .first()
        if device is not None
        else None
    )
    user = db.session.get(User, patient.user_id) if patient.user_id else None
    return {
        "id": patient.id,
        "name": patient.name,
        "email": user.email if user else None,
        "date_of_birth": iso_or_none(patient.date_of_birth),
        "latest_alert_level": latest_alert.level if latest_alert else None,
        "latest_alert_acknowledged": latest_alert.acknowledged if latest_alert else None,
        "open_alert_level": open_alert.level if open_alert else None,
        "device": device_dict(device),
        "latest_vitals": {
            "hr": latest_vital.hr if latest_vital else None,
            "spo2": latest_vital.spo2 if latest_vital else None,
            "rr": latest_vital.rr if latest_vital else None,
            "timestamp": iso_or_none(latest_vital.timestamp) if latest_vital else None,
        },
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
    rows.sort(key=lambda r: (-(r["open_alert_level"] or 0), r["name"].lower()))
    return jsonify(rows)


@clinician_bp.get("/patients/<patient_id>")
@role_required("clinician")
def get_patient(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient
    return jsonify(_patient_dict(patient))


@clinician_bp.get('/patients/<patient_id>/audio-experiment/latest')
@role_required('clinician')
def get_audio_experiment(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient
    device = db.session.query(Device).filter_by(patient_id=patient.id).first()
    return jsonify(latest_capture_evidence(
        current_app.config['AUDIO_CAPTURE_DIRECTORY'], device.device_id if device else None,
        current_app.config['AUDIO_PERIODIC_PATIENT_ALERTS_ENABLED']))


@clinician_bp.post("/patients")
@role_required("clinician")
def add_patient():
    body = request.get_json(silent=True) or {}
    email = (body.get("email") or "").strip().lower()
    if not email:
        return jsonify({"error": "email wajib diisi"}), 400

    user = db.session.query(User).filter_by(email=email, role="pasien").first()
    if user is None:
        return jsonify({"error": "tidak ada akun pasien dengan email tersebut"}), 404

    patient = db.session.query(Patient).filter_by(user_id=user.id).first()
    if patient is None:
        return jsonify({"error": "data pasien tidak ditemukan"}), 404

    # Menautkan pasien = memberi akses ke data medisnya, jadi pasien yang sudah didampingi
    # tenaga medis lain TIDAK boleh "diambil alih" hanya dengan mengetahui emailnya.
    if patient.assigned_clinician_id == current_user.id:
        return jsonify({"error": "pasien sudah ada di daftar Anda"}), 409
    if patient.assigned_clinician_id is not None:
        return jsonify({"error": "pasien sudah didampingi tenaga medis lain"}), 409

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

    from_dt = _parse_datetime_param("from")
    to_dt = _parse_datetime_param("to")
    if from_dt:
        query = query.filter(ReadingVital.timestamp >= from_dt)
    if to_dt:
        query = query.filter(ReadingVital.timestamp <= to_dt)

    readings = query.order_by(ReadingVital.timestamp.asc()).all()
    return jsonify(
        [{"hr": r.hr, "spo2": r.spo2, "rr": r.rr, "timestamp": r.timestamp.isoformat()} for r in readings]
    )


@clinician_bp.get("/patients/<patient_id>/classification/latest")
@role_required("clinician")
def patient_classification_latest(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient

    device = db.session.query(Device).filter_by(patient_id=patient.id).first()
    if device is None:
        return jsonify(None)

    latest = (
        db.session.query(ReadingClassification)
        .filter_by(device_id=device.device_id)
        .order_by(ReadingClassification.segment_end.desc())
        .first()
    )
    if latest is None:
        return jsonify(None)

    return jsonify(
        {
            "channel_id": latest.channel_id,
            "segment_start": latest.segment_start.isoformat(),
            "segment_end": latest.segment_end.isoformat(),
            "predicted_class": latest.predicted_class,
            "confidence": latest.confidence,
            "probabilities": latest.probabilities,
            "model_version": latest.model_version,
            # 🔓⏸️ Model B ditunda — selalu None sampai terintegrasi (INTEGRATION_CONTRACT.md §4.2)
            "severity_class": latest.severity_class,
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

    level = _parse_level_param()
    if level is not None:
        query = query.filter(Alert.level == level)

    from_dt = _parse_datetime_param("from")
    to_dt = _parse_datetime_param("to")
    if from_dt:
        query = query.filter(Alert.created_at >= from_dt)
    if to_dt:
        query = query.filter(Alert.created_at <= to_dt)

    alerts = query.order_by(Alert.created_at.desc()).all()
    return jsonify([_alert_dict(a, patient.name) for a in alerts])


def _alert_dict(alert: Alert, patient_name: str | None = None) -> dict:
    return {
        "id": alert.id,
        "device_id": alert.device_id,
        "patient_id": alert.patient_id,
        "patient_name": patient_name,
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
    names = {
        p.id: p.name for p in db.session.query(Patient).filter_by(assigned_clinician_id=current_user.id).all()
    }
    query = db.session.query(Alert).filter(Alert.patient_id.in_(list(names)))

    level = _parse_level_param()
    if level is not None:
        query = query.filter(Alert.level == level)

    patient_id_param = request.args.get("patient_id")
    if patient_id_param:
        query = query.filter(Alert.patient_id == patient_id_param)

    acknowledged_param = request.args.get("acknowledged")
    if acknowledged_param is not None:
        query = query.filter(Alert.acknowledged == (acknowledged_param.lower() == "true"))

    from_dt = _parse_datetime_param("from")
    to_dt = _parse_datetime_param("to")
    if from_dt:
        query = query.filter(Alert.created_at >= from_dt)
    if to_dt:
        query = query.filter(Alert.created_at <= to_dt)

    alerts = query.order_by(Alert.created_at.desc()).all()
    return jsonify([_alert_dict(a, names.get(a.patient_id)) for a in alerts])


@clinician_bp.get("/patients/<patient_id>/classification/history")
@role_required("clinician")
def patient_classification_history(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient

    range_param = request.args.get("range", "7d")
    if range_param not in _HISTORY_RANGES:
        return jsonify({"error": "range harus salah satu dari 24h, 7d, 30d"}), 400
    span, bucket = _HISTORY_RANGES[range_param]

    end = datetime.now(timezone.utc).replace(tzinfo=None)
    start = end - span
    device = db.session.query(Device).filter_by(patient_id=patient.id).first()
    segments = []
    if device is not None:
        segments = [
            ClassifiedSegment(segment_end=row.segment_end, predicted_class=row.predicted_class)
            for row in db.session.query(ReadingClassification.segment_end, ReadingClassification.predicted_class)
            .filter(
                ReadingClassification.device_id == device.device_id,
                ReadingClassification.segment_end >= start,
                ReadingClassification.segment_end < end,
            )
            .all()
        ]

    return jsonify(
        {
            "range": range_param,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "bucket_seconds": int(bucket.total_seconds()),
            "buckets": bucket_classifications(segments, start, end, bucket),
        }
    )


def _thresholds_response(patient: Patient) -> dict:
    threshold = db.session.get(Threshold, patient.id)
    plan = db.session.get(PatientActionPlan, patient.id)
    return {
        **{field: getattr(threshold, field) if threshold else None for field in THRESHOLD_FIELDS},
        "updated_by": threshold.updated_by if threshold else None,
        "updated_at": iso_or_none(threshold.updated_at) if threshold else None,
        "action_plan": plan.text if plan else "",
    }


def _validate_thresholds(values: dict) -> str | None:
    """Validasi bentuk angka saja — BUKAN menilai apakah angkanya tepat secara klinis."""
    for field, value in values.items():
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return f"{field} harus berupa angka atau null"
        if value <= 0:
            return f"{field} harus lebih besar dari nol"
    if values.get("spo2_min") is not None and values["spo2_min"] > 100:
        return "spo2_min tidak boleh lebih dari 100"
    for low, high in (("hr_min", "hr_max"), ("rr_min", "rr_max")):
        if values.get(low) is not None and values.get(high) is not None and values[high] <= values[low]:
            return f"{high} harus lebih besar dari {low}"
    return None


@clinician_bp.get("/patients/<patient_id>/thresholds")
@role_required("clinician")
def get_thresholds(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient
    return jsonify(_thresholds_response(patient))


@clinician_bp.put("/patients/<patient_id>/thresholds")
@role_required("clinician")
def update_thresholds(patient_id: str):
    patient = _require_owned_patient(patient_id)
    if isinstance(patient, tuple):
        return patient

    body = request.get_json(silent=True) or {}
    threshold = db.session.get(Threshold, patient.id)

    # Gabungkan dengan nilai tersimpan dulu, supaya validasi min < max juga berlaku untuk
    # update parsial (mis. hanya mengirim hr_max).
    merged = {field: getattr(threshold, field) if threshold else None for field in THRESHOLD_FIELDS}
    merged.update({field: body[field] for field in THRESHOLD_FIELDS if field in body})
    error = _validate_thresholds(merged)
    if error:
        return jsonify({"error": error}), 400
    if "action_plan" in body and not isinstance(body["action_plan"], str):
        return jsonify({"error": "action_plan harus berupa teks"}), 400

    now = datetime.now(timezone.utc)
    if threshold is None:
        threshold = Threshold(patient_id=patient.id)
        db.session.add(threshold)
    for field in THRESHOLD_FIELDS:
        if field in body:
            setattr(threshold, field, body[field])
    threshold.updated_by = current_user.id
    threshold.updated_at = now

    if "action_plan" in body:
        plan = db.session.get(PatientActionPlan, patient.id)
        if plan is None:
            plan = PatientActionPlan(patient_id=patient.id)
            db.session.add(plan)
        plan.text = body["action_plan"].strip()
        plan.updated_by = current_user.id
        plan.updated_at = now

    db.session.commit()
    return jsonify(_thresholds_response(patient))


@clinician_bp.get("/devices/<device_id>/status")
@role_required("clinician")
def device_status(device_id: str):
    device = db.session.get(Device, device_id)
    # Perangkat yang tidak tertaut ke pasien milik clinician ini diperlakukan "tidak ditemukan"
    # (sama seperti _require_owned_patient) supaya status perangkat pasien lain tidak bocor.
    owner = db.session.get(Patient, device.patient_id) if device is not None and device.patient_id else None
    if device is None or owner is None or owner.assigned_clinician_id != current_user.id:
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

    if "full_name" in body and (not isinstance(body["full_name"], str) or not body["full_name"].strip()):
        return jsonify({"error": "full_name tidak boleh kosong"}), 400

    if "new_password" in body:
        current_password = body.get("current_password")
        if not current_password or not check_password_hash(current_user.password_hash, current_password):
            return jsonify({"error": "current_password salah"}), 400
        new_password = body["new_password"]
        if not isinstance(new_password, str) or len(new_password) < MIN_PASSWORD_LENGTH:
            return jsonify({"error": f"new_password minimal {MIN_PASSWORD_LENGTH} karakter"}), 400
        current_user.password_hash = generate_password_hash(new_password)

    for field in ("full_name", "specialization", "institution", "str_sip_number"):
        if field in body:
            value = body[field]
            setattr(current_user, field, value.strip() if isinstance(value, str) else value)
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
