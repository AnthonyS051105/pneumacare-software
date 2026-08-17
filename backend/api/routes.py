"""REST API endpoint untuk frontend (SDD_SOFTWARE.md §4).

Sesi ini (Fase 3) hanya mengimplementasikan endpoint acknowledge alert
(FR-SW-043, INTEGRATION_CONTRACT.md §4.2). Endpoint lain menyusul di Fase 4.
"""

from datetime import datetime, timezone

from flask import Blueprint, jsonify

from backend.models import db
from backend.models.alert import Alert

api_bp = Blueprint("api", __name__, url_prefix="/api/v1")


# TODO_AUTH_NOT_IMPLEMENTED: FR-SW-059/NFR-SW-007 mewajibkan endpoint ini HANYA bisa
# dipanggil role `clinician` (403 untuk role lain). Sistem auth/session (Fase 4) belum
# ada di repo ini, jadi role-check sungguhan BELUM diterapkan di sini — endpoint saat
# ini menerima semua request tanpa verifikasi identitas/role apapun. JANGAN anggap
# endpoint ini aman untuk dipakai di luar development/demo sampai auth diimplementasikan.
@api_bp.post("/alerts/<alert_id>/acknowledge")
def acknowledge_alert(alert_id: str):
    alert = db.session.get(Alert, alert_id)
    if alert is None:
        return jsonify({"error": "alert tidak ditemukan"}), 404

    if alert.acknowledged:
        return jsonify({"error": "alert sudah di-acknowledge sebelumnya"}), 409

    alert.acknowledged = True
    alert.acknowledged_at = datetime.now(timezone.utc)
    # TODO_AUTH_NOT_IMPLEMENTED: seharusnya diisi user_id dari session yang login
    # (acknowledged_by, SDD_SOFTWARE.md §3 tabel `alerts`) — belum ada session, dibiarkan None.
    db.session.commit()

    return jsonify(
        {
            "alert_id": alert.id,
            "acknowledged": alert.acknowledged,
            "acknowledged_at": alert.acknowledged_at.isoformat(),
            "acknowledged_by": alert.acknowledged_by,
        }
    )
