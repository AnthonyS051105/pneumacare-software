"""REST API endpoint lintas-role (SDD_SOFTWARE.md §4).

Endpoint yang khusus untuk satu portal ada di `clinician_routes.py`/`patient_routes.py`;
di sini hanya endpoint yang tidak spesifik ke satu portal.
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify
from flask_login import current_user

from backend.auth.decorators import role_required
from backend.models import db
from backend.models.alert import Alert
from backend.models.patient import Patient

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


@api_bp.post("/alerts/<alert_id>/acknowledge")
@role_required("clinician")  # FR-SW-059/NFR-SW-007: hanya clinician, 403 untuk role lain
def acknowledge_alert(alert_id: str):
    alert = db.session.get(Alert, alert_id)
    patient = db.session.get(Patient, alert.patient_id) if alert is not None else None
    # Hanya tenaga medis pendamping pasien tersebut yang boleh meninjau alert-nya.
    if alert is None or patient is None or patient.assigned_clinician_id != current_user.id:
        return jsonify({"error": "alert tidak ditemukan"}), 404

    if alert.acknowledged:
        return jsonify({"error": "alert sudah di-acknowledge sebelumnya"}), 409

    alert.acknowledged = True
    alert.acknowledged_at = datetime.now(timezone.utc)
    alert.acknowledged_by = current_user.id
    db.session.commit()

    return jsonify(
        {
            "alert_id": alert.id,
            "acknowledged": alert.acknowledged,
            "acknowledged_at": alert.acknowledged_at.isoformat(),
            "acknowledged_by": alert.acknowledged_by,
        }
    )
