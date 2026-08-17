"""Portal Pasien — SDD_SOFTWARE.md §4.3.

FR-SW-070 (constraint keamanan): semua endpoint `/patient/me/*` mengambil
`patient_id` dari session yang login (via `current_user`), TIDAK PERNAH dari
parameter URL — mencegah satu pasien mengakses data pasien lain.
"""

from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, request
from flask_login import current_user
from werkzeug.security import check_password_hash, generate_password_hash

from backend.analytics.pattern_insight import VitalPoint, generate_pattern_insight
from backend.analytics.wear_time import StatusChange, compute_daily_online_hours
from backend.auth.alert_language import translate_alert
from backend.auth.decorators import role_required
from backend.models import db
from backend.models.alert import Alert
from backend.models.classification import ReadingClassification
from backend.models.device import Device, DevicePairingCode, DeviceStatusLog
from backend.models.patient import Patient
from backend.models.vital import ReadingVital

patient_bp = Blueprint("patient", __name__, url_prefix="/api/v1/patient/me")

_RANGE_TO_TIMEDELTA = {"24h": timedelta(hours=24), "7d": timedelta(days=7), "30d": timedelta(days=30)}


def _current_patient() -> Patient | None:
    return db.session.query(Patient).filter_by(user_id=current_user.id).first()


def _vital_range(values: list[float]) -> dict:
    return {"min": min(values), "max": max(values)} if values else {"min": None, "max": None}


def _today_range(device_id: str) -> dict:
    now = datetime.now(timezone.utc)
    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    readings = (
        db.session.query(ReadingVital)
        .filter(ReadingVital.device_id == device_id, ReadingVital.timestamp >= day_start)
        .all()
    )
    return {
        "hr": _vital_range([r.hr for r in readings if r.hr is not None]),
        "spo2": _vital_range([r.spo2 for r in readings if r.spo2 is not None]),
        "rr": _vital_range([r.rr for r in readings if r.rr is not None]),
    }


def _wear_compliance_for_day(device_id: str, day_start: datetime) -> float:
    # SQLite/SQLAlchemy menyimpan datetime sebagai naive (tanpa tzinfo) meski yang
    # ditulis adalah aware UTC (lihat ingestion/mqtt_subscriber.py) — dibaca kembali
    # tanpa tzinfo. Samakan day_start/day_end ke naive UTC di sini SEBELUM
    # dibandingkan langsung dengan row.changed_at, supaya tidak TypeError.
    day_start_naive = day_start.replace(tzinfo=None) if day_start.tzinfo else day_start
    day_end_naive = day_start_naive + timedelta(days=1)

    changes_query = (
        db.session.query(DeviceStatusLog)
        .filter(DeviceStatusLog.device_id == device_id, DeviceStatusLog.changed_at < day_end_naive)
        .order_by(DeviceStatusLog.changed_at.asc())
        .all()
    )

    # status_before_range: status terakhir SEBELUM day_start (baris paling akhir yang
    # changed_at < day_start), default "offline" bila belum ada riwayat sama sekali.
    status_before = "offline"
    changes_in_range: list[StatusChange] = []
    for row in changes_query:
        if row.changed_at < day_start_naive:
            status_before = row.status
        else:
            changes_in_range.append(StatusChange(row.status, row.changed_at))

    return compute_daily_online_hours(
        changes_in_range, day_start_naive, day_end_naive, status_before_range=status_before
    )


@patient_bp.get("/summary")
@role_required("pasien")
def summary():
    patient = _current_patient()
    if patient is None:
        return jsonify({"error": "data pasien tidak ditemukan"}), 404

    device = db.session.query(Device).filter_by(patient_id=patient.id).first()
    latest_vital = None
    latest_classification = None
    if device is not None:
        latest_vital = (
            db.session.query(ReadingVital)
            .filter_by(device_id=device.device_id)
            .order_by(ReadingVital.timestamp.desc())
            .first()
        )
        latest_classification = (
            db.session.query(ReadingClassification)
            .filter_by(device_id=device.device_id)
            .order_by(ReadingClassification.segment_end.desc())
            .first()
        )

    latest_alert = (
        db.session.query(Alert)
        .filter_by(patient_id=patient.id)
        .order_by(Alert.created_at.desc())
        .first()
    )
    # FR-SW-065: status traffic-light bahasa awam, BUKAN istilah klinis mentah.
    # Nilai "stable"/"attention"/"urgent" dipilih SESUAI StatusLevel di
    # src/components/patient/StatusHeroCard.tsx (frontend) — bukan "stabil"/dst.
    status_label = "stable"
    if latest_alert is not None and not latest_alert.acknowledged:
        status_label = "urgent" if latest_alert.level == 3 else "attention"

    today_range = _today_range(device.device_id) if device is not None else None
    wear_hours_today = _wear_compliance_for_day(
        device.device_id, datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    ) if device is not None else None

    return jsonify(
        {
            "patient_id": patient.id,
            "patient_name": patient.name,
            "status_label": status_label,
            "device_connected": device.status == "online" if device is not None else False,
            "latest_vitals": {
                "hr": latest_vital.hr if latest_vital else None,
                "spo2": latest_vital.spo2 if latest_vital else None,
                "rr": latest_vital.rr if latest_vital else None,
                "timestamp": latest_vital.timestamp.isoformat() if latest_vital else None,
            },
            "today_range": today_range,
            "wear_compliance_today_hours": wear_hours_today,
            # Hasil terbaru Model A (wheeze/crackle CNN) — FR-SW checkpoint 50%,
            # ditampilkan apa adanya sebagai indikasi skrining, BUKAN diagnosis
            # (lihat batasan framing di keputusan_terkunci.md).
            "latest_classification": {
                "predicted_class": latest_classification.wheeze_crackle_class,
                "confidence": latest_classification.wheeze_crackle_confidence,
                "timestamp": latest_classification.segment_end.isoformat(),
            }
            if latest_classification is not None
            else None,
        }
    )


def _stats_for(values: list[float]) -> dict:
    if not values:
        return {"current": None, "avg": None, "min": None, "max": None}
    return {
        "current": round(values[-1], 1),
        "avg": round(sum(values) / len(values), 1),
        "min": round(min(values), 1),
        "max": round(max(values), 1),
    }


@patient_bp.get("/history")
@role_required("pasien")
def history():
    """Response diperluas dari versi sebelumnya (array readings polos) menjadi objek
    dengan `readings` + `stats` + `wear_compliance_by_day` + `pattern_insight` — lihat
    ringkasan sesi Fase 5 untuk detail perbedaan field yang dilaporkan ke Tony."""
    patient = _current_patient()
    if patient is None:
        return jsonify({"error": "data pasien tidak ditemukan"}), 404

    range_param = request.args.get("range", "24h")
    delta = _RANGE_TO_TIMEDELTA.get(range_param)
    if delta is None:
        return jsonify({"error": "range harus salah satu dari 24h, 7d, 30d"}), 400

    device = db.session.query(Device).filter_by(patient_id=patient.id).first()
    if device is None:
        return jsonify(
            {"readings": [], "stats": {}, "wear_compliance_by_day": [], "pattern_insight": None}
        )

    now = datetime.now(timezone.utc)
    since = now - delta
    readings = (
        db.session.query(ReadingVital)
        .filter(ReadingVital.device_id == device.device_id, ReadingVital.timestamp >= since)
        .order_by(ReadingVital.timestamp.asc())
        .all()
    )

    hr_values = [r.hr for r in readings if r.hr is not None]
    spo2_values = [r.spo2 for r in readings if r.spo2 is not None]
    rr_values = [r.rr for r in readings if r.rr is not None]

    day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    n_days = max(1, delta.days) if delta.days > 0 else 1
    wear_compliance_by_day = [
        {
            "date": (day_start - timedelta(days=offset)).date().isoformat(),
            "hours": _wear_compliance_for_day(device.device_id, day_start - timedelta(days=offset)),
        }
        for offset in range(n_days - 1, -1, -1)
    ]

    pattern_insight = generate_pattern_insight(
        [VitalPoint(timestamp=r.timestamp, hr=r.hr) for r in readings]
    )

    return jsonify(
        {
            "readings": [
                {"hr": r.hr, "spo2": r.spo2, "rr": r.rr, "timestamp": r.timestamp.isoformat()}
                for r in readings
            ],
            "stats": {"hr": _stats_for(hr_values), "spo2": _stats_for(spo2_values), "rr": _stats_for(rr_values)},
            "wear_compliance_by_day": wear_compliance_by_day,
            "pattern_insight": pattern_insight,
        }
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
