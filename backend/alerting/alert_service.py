"""Layer I/O untuk alert_engine.py — query threshold/histori dari DB, panggil
evaluate_alert() (fungsi murni), simpan Alert bila ada hasil. Dipanggil dari
ingestion layer (mqtt_subscriber.py untuk vitals, websocket_server.py untuk
trend wheeze/crackle) — FR-SW-040..044, INTEGRATION_CONTRACT.md §5.
"""

import logging
import uuid
from datetime import datetime, timezone

from backend.alerting.alert_engine import Thresholds, VitalReading, evaluate_alert
from backend.models import db
from backend.models.alert import Alert
from backend.models.device import Device
from backend.models.threshold import Threshold
from backend.models.trend import TrendEvent
from backend.trend_analysis.trend_detector import TrendResult

logger = logging.getLogger(__name__)


def _thresholds_for_patient(patient_id: str) -> Thresholds:
    row = db.session.get(Threshold, patient_id)
    if row is None:
        # Belum pernah diisi clinician — semua None, evaluate_vitals()
        # otomatis skip semua parameter (by design, lihat alert_engine.py).
        return Thresholds(hr_min=None, hr_max=None, spo2_min=None, rr_min=None, rr_max=None)
    return Thresholds(
        hr_min=row.hr_min, hr_max=row.hr_max, spo2_min=row.spo2_min, rr_min=row.rr_min, rr_max=row.rr_max
    )


def _trend_significance_threshold_for_patient(patient_id: str, default: float) -> float:
    row = db.session.get(Threshold, patient_id)
    if row is not None and row.trend_significance_threshold is not None:
        return row.trend_significance_threshold
    return default


def _recent_trend_significant_flags(device_id: str, min_consecutive: int) -> list[bool]:
    """N `TrendEvent.significant` TERBARU untuk device ini, urut lama->baru
    (dibutuhkan compute_trend_persistence — lihat alert_engine.py)."""
    rows = (
        db.session.query(TrendEvent)
        .filter_by(device_id=device_id)
        .order_by(TrendEvent.window_end.desc())
        .limit(min_consecutive)
        .all()
    )
    return [row.significant for row in reversed(rows)]


def evaluate_and_save_alert(
    app,
    device_id: str,
    vitals: VitalReading,
    trend_result: TrendResult | None,
) -> Alert | None:
    """Entry point I/O utama — query threshold/histori device, evaluasi, simpan Alert.

    Return None (tanpa menyimpan apa pun) bila device belum tertaut ke patient manapun
    (device baru/belum di-pairing — lihat Device.patient_id di patient_routes.py
    /device/repair) ATAU bila evaluate_alert() sendiri mengembalikan None (tidak ada
    kondisi yang memicu alert).
    """
    cfg = app.config

    device = db.session.get(Device, device_id)
    if device is None or device.patient_id is None:
        logger.debug("alert dilewati: device=%s belum tertaut ke patient manapun", device_id)
        return None

    patient_id = device.patient_id
    thresholds = _thresholds_for_patient(patient_id)
    significance_threshold = _trend_significance_threshold_for_patient(
        patient_id, cfg["TREND_SIGNIFICANCE_THRESHOLD_DEFAULT"]
    )
    min_consecutive = cfg["TREND_PERSISTENCE_MIN_CONSECUTIVE"]
    recent_flags = _recent_trend_significant_flags(device_id, min_consecutive)
    if trend_result is not None:
        recent_flags = recent_flags[-(min_consecutive - 1) :] + [trend_result.significant]

    result = evaluate_alert(
        vitals=vitals,
        trend_result=trend_result,
        recent_trend_significant_flags=recent_flags,
        thresholds=thresholds,
        trend_significance_threshold=significance_threshold,
        min_consecutive=min_consecutive,
        level1_margin_pct=cfg["LEVEL1_MARGIN_PCT"],
        level1_margin_spo2_abs=cfg["LEVEL1_MARGIN_SPO2_ABS"],
    )

    if result is None:
        return None

    alert = Alert(
        id=str(uuid.uuid4()),
        device_id=device_id,
        patient_id=patient_id,
        level=result.level,
        triggers=[
            {
                "type": t.type,
                "parameter": t.parameter,
                "value": t.value,
                "threshold": t.threshold,
                "severity": t.severity,
            }
            for t in result.triggers
        ],
        created_at=datetime.now(timezone.utc),
        acknowledged=False,
    )
    db.session.add(alert)
    db.session.commit()
    logger.info(
        "alert level=%d dibuat device=%s patient=%s triggers=%d",
        result.level,
        device_id,
        patient_id,
        len(result.triggers),
    )
    return alert
