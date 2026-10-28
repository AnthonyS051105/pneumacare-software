"""Layer I/O untuk rolling_window.py + trend_detector.py — query histori
readings_classification dari DB, hitung trend, simpan trend_events. Dipanggil
dari websocket_server.py setelah tiap segmen audio diklasifikasi Model A
(FR-SW-020..024, SDD_SOFTWARE.md §6).
"""

import logging
import uuid

from backend.models import db
from backend.models.classification import ReadingClassification
from backend.models.device import Device
from backend.models.trend import TrendEvent
from backend.trend_analysis.rolling_window import ClassificationEvent, compute_rolling_frequency
from backend.trend_analysis.trend_detector import TrendResult, detect_trend
from backend.trend_analysis.threshold_service import trend_threshold_for_patient

logger = logging.getLogger(__name__)

# Berapa banyak segmen histori terbaru yang di-query — cukup untuk mengisi
# TREND_ROLLING_WINDOW_SIZE + beberapa titik regresi tambahan. Dipilih longgar
# (bukan pas window_size) supaya trend_detector punya beberapa titik untuk
# regresi, bukan cuma 1 titik rolling-window tunggal.
_HISTORY_LOOKBACK_MULTIPLIER = 5


def compute_and_save_trend(
    app,
    device_id: str,
    channel_id: int,
) -> TrendResult | None:
    """Query histori klasifikasi terbaru untuk device+channel ini, hitung rolling
    frequency abnormal + trend, simpan TrendEvent bila ada hasil (>=2 titik rolling window).

    Return None (tanpa menyimpan) bila histori belum cukup — sama seperti
    detect_trend() sendiri, caller (websocket_server.py) tidak perlu menangani
    ini sebagai error.
    """
    cfg = app.config
    window_size = cfg["TREND_ROLLING_WINDOW_SIZE"]
    moving_average_window = cfg["TREND_MOVING_AVERAGE_WINDOW"]
    device = db.session.get(Device, device_id)
    significance_threshold = trend_threshold_for_patient(
        device.patient_id if device is not None else None,
        cfg["TREND_SIGNIFICANCE_THRESHOLD_DEFAULT"],
    )

    lookback = window_size * _HISTORY_LOOKBACK_MULTIPLIER
    rows = (
        db.session.query(ReadingClassification)
        .filter_by(device_id=device_id, channel_id=channel_id)
        .order_by(ReadingClassification.segment_end.desc())
        .limit(lookback)
        .all()
    )
    rows.reverse()  # query desc untuk ambil N-terbaru, tapi rolling_window butuh urut lama->baru

    events = [
        ClassificationEvent(timestamp=row.segment_end, predicted_class=row.predicted_class)
        for row in rows
    ]

    points = compute_rolling_frequency(events, window_size)
    trend_result = detect_trend(points, moving_average_window, significance_threshold)

    if trend_result is None:
        return None

    db.session.add(
        TrendEvent(
            id=str(uuid.uuid4()),
            device_id=device_id,
            window_start=trend_result.window_start,
            window_end=trend_result.window_end,
            slope=trend_result.slope,
            significant=trend_result.significant,
        )
    )
    db.session.commit()
    logger.info(
        "trend dihitung device=%s channel=%s slope=%.4f significant=%s",
        device_id,
        channel_id,
        trend_result.slope,
        trend_result.significant,
    )
    return trend_result
