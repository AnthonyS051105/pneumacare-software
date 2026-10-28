"""Resolve the shared trend/alert threshold from the patient's configuration."""

from backend.models import db
from backend.models.threshold import Threshold


def trend_threshold_for_patient(patient_id: str | None, default: float) -> float:
    """Use the configured patient value, or the application fallback if absent."""
    row = db.session.get(Threshold, patient_id) if patient_id is not None else None
    if row is not None and row.trend_significance_threshold is not None:
        return row.trend_significance_threshold
    return default
