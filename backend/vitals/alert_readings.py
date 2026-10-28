"""Pure quality/freshness gate shared by every ingestion alert path.

Legacy records have unknown quality and remain available as history, but must
not silently acquire trusted status when another sensor triggers an evaluation.
"""
from datetime import datetime, timezone
from math import isfinite

from backend.alerting.alert_engine import VitalReading


def vitals_for_alert(reading, max_age_seconds: float, *, now: datetime | None = None) -> VitalReading:
    """Return only explicitly good, finite values from a recent UTC reading.

    Freshness is an operational data-age limit, not a physiological threshold.
    SQLite naive timestamps are interpreted as UTC, matching storage convention.
    """
    if not isfinite(max_age_seconds) or max_age_seconds <= 0:
        raise ValueError('vital alert max age must be positive and finite')
    empty = VitalReading(hr=None,spo2=None,rr=None)
    if reading is None or not isinstance(reading.timestamp,datetime):
        return empty
    observed = reading.timestamp
    if observed.tzinfo is None:
        observed = observed.replace(tzinfo=timezone.utc)
    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    age = (current-observed).total_seconds()
    if not 0 <= age <= max_age_seconds:
        return empty

    def trusted(name):
        value = getattr(reading,name,None)
        quality = getattr(reading,name+'_confidence',None)
        if quality != 'good' or type(value) not in (int,float) or not isfinite(value):
            return None
        return value

    return VitalReading(hr=trusted('hr'),spo2=trusted('spo2'),rr=trusted('rr'))
