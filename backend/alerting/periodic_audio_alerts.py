"""Same-channel persistence of complete periodic predictions drives alert levels."""
from datetime import datetime, timedelta, timezone
import logging
import uuid

from backend.models import db
from backend.models.alert import Alert
from backend.models.device import Device
from backend.models.periodic_audio_state import PeriodicAudioState

logger = logging.getLogger(__name__)
TRIGGER_TYPE = 'periodic_audio_review'


def _commit(job):
    if job:
        job.check_cancelled()
    db.session.commit()


def notify_periodic_audio(segment, result, config, job=None):
    """Persist bounded channel history and create/escalate its prototype alert.

    One ingestion worker serializes state updates. A normal result resets the
    streak but never acknowledges/lowers an existing alert. No vital is inferred.
    """
    if not config.get('AUDIO_PERIODIC_PATIENT_ALERTS_ENABLED', False):
        return {'status': 'disabled'}
    if (segment.data_origin != 'measured' or segment.capture_id is None
            or not segment.capture_stream_id or segment.sample_rate != 16000
            or len(segment.pcm_samples) != 32000
            or segment.segment_end_ms - segment.segment_start_ms != 2000):
        return {'status': 'ineligible'}
    warning = config['AUDIO_PERIODIC_WARNING_CONSECUTIVE']
    urgent = config['AUDIO_PERIODIC_URGENT_CONSECUTIVE']
    max_gap = config['AUDIO_PERIODIC_STREAK_MAX_GAP_SECONDS']
    if not 2 <= warning < urgent <= 100 or not 0 < max_gap <= 3600:
        raise ValueError('invalid periodic audio persistence configuration')
    device = db.session.get(Device, segment.device_id)
    if device is None or device.patient_id is None:
        return {'status': 'unpaired'}
    state = db.session.get(PeriodicAudioState, (segment.device_id, segment.channel_id))
    identity = str(uuid.uuid5(uuid.NAMESPACE_URL, repr((
        'pneumacare:periodic_audio_review', device.patient_id, segment.device_id,
        segment.capture_stream_id, segment.capture_id, segment.channel_id))))
    existing = db.session.get(Alert, identity)
    if existing is not None:
        return {'status': 'already_recorded', 'alert_id': existing.id, 'level': existing.level}
    if (state is not None and state.stream_id == segment.capture_stream_id
            and segment.capture_id <= state.last_capture_id):
        return {'status': 'ignored_replay'}

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    prediction = result['classification']
    continuous = (state is not None and state.patient_id == device.patient_id
                  and state.stream_id == segment.capture_stream_id
                  and state.reception_session_id == segment.reception_session_id
                  and state.model_version == result['model_version']
                  and segment.capture_id == state.last_capture_id + 1
                  and 0 < segment.segment_start_ms - state.last_start_ms <= max_gap * 1000
                  and 0 <= (now - state.last_received_at).total_seconds() <= max_gap)
    previous = state.consecutive_abnormal if continuous else 0
    evidence = list(state.evidence) if continuous else []
    abnormal = prediction['predicted_class'] == 'abnormal'
    count = min(previous + 1, urgent) if abnormal else 0
    evidence = (evidence + [dict(capture_id=segment.capture_id,
                                 segment_start_ms=segment.segment_start_ms,
                                 confidence=prediction['confidence'])])[-urgent:] if abnormal else []
    if state is None:
        state = PeriodicAudioState(device_id=segment.device_id, channel_id=segment.channel_id)
        db.session.add(state)
    state.patient_id = device.patient_id
    state.stream_id = segment.capture_stream_id
    state.reception_session_id = segment.reception_session_id
    state.model_version = result['model_version']
    state.last_capture_id = segment.capture_id
    state.last_start_ms = segment.segment_start_ms
    state.last_received_at = now
    state.consecutive_abnormal = count
    state.evidence = evidence
    summary = dict(consecutive_abnormal=count, warning_after=warning, urgent_after=urgent)
    if not abnormal:
        _commit(job)
        return {'status': 'normal', **summary}
    level = 3 if count >= urgent else 2 if count >= warning else 1
    cutoff = now - timedelta(seconds=config['ALERT_REPEAT_COOLDOWN_SECONDS'])
    recent = (db.session.query(Alert)
              .filter_by(patient_id=device.patient_id, device_id=device.device_id)
              .filter(Alert.level >= level)
              .filter((Alert.acknowledged.is_(False)) | (Alert.created_at >= cutoff))
              .order_by(Alert.level.desc(), Alert.created_at.desc()).all())
    for old in recent:
        if any(t.get('type') == TRIGGER_TYPE for t in old.triggers or []):
            _commit(job)  # suppressed notifications still advance observed history
            return {'status': 'suppressed', 'alert_id': old.id, 'level': old.level, **summary}
    trigger = dict(type=TRIGGER_TYPE, parameter='audio_classification',
                   predicted_class='abnormal', confidence=prediction['confidence'],
                   model_version=result['model_version'], channel_id=segment.channel_id,
                   capture_id=segment.capture_id, stream_id=segment.capture_stream_id,
                   segment_start_ms=segment.segment_start_ms, duration_ms=2000,
                   data_origin='measured', classification_validated=False,
                   evidence=evidence, **summary)
    alert = Alert(id=identity, device_id=device.device_id, patient_id=device.patient_id,
                  level=level, triggers=[trigger], created_at=now, acknowledged=False)
    db.session.add(alert)
    _commit(job)  # state and alert atomic; worker rolls back on failure
    logger.info('audio_patient_notification status=created alert=%s device=%s channel=%s '
                'capture=%s level=%d consecutive=%d classification_validated=false',
                identity, segment.device_id, segment.channel_id, segment.capture_id, level, count)
    return {'status': 'created', 'alert_id': identity, 'level': level, **summary}
