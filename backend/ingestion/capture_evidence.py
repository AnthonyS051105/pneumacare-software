"""Read-only experimental evidence; never joined into clinical history."""
import json
from pathlib import Path


def latest_capture_evidence(directory, device_id, patient_notifications_enabled=False):
    latest = None
    channels = {}
    for path in Path(directory).glob('*.json'):
        try:
            if path.stat().st_size > 16384:
                continue
            item = json.loads(path.read_text())
            if not isinstance(item, dict) or item.get('device_id') != device_id:
                continue
            key = (int(item['start_ms']), str(item['stream_id']), int(item['capture_id']))
            channel = item['channel_id']
            if type(channel) is not int or not 1 <= channel <= 4:
                continue
            if latest is None or key > latest:
                latest, channels = key, {}
            if key == latest:
                channels[channel] = {k: item.get(k) for k in (
                    'channel_id', 'data_origin', 'source_channel_id', 'inference_status',
                    'experimental_classification', 'model_version', 'review_signal', 'inference_ms',
                    'patient_notification')}
        except (OSError, ValueError, KeyError, TypeError):
            # Retention/atomic sidecar replacement may race with a read.
            continue
    return dict(available=latest is not None, classification_validated=False,
                patient_notifications_enabled=patient_notifications_enabled,
                clinical_alerts_enabled=False, start_ms=latest[0] if latest else None,
                capture_id=latest[2] if latest else None,
                channels=[channels[k] for k in sorted(channels)])
