"""Experimental predictions with optional informational patient notifications."""
import logging
from time import monotonic

from backend.ingestion.capture_archive import archive_capture, annotate_capture
from backend.ingestion.audio_worker import Cancelled
from backend.alerting.periodic_audio_alerts import notify_periodic_audio

logger = logging.getLogger(__name__)


def process_periodic_capture(segment, config, classify, job=None):
    quota = config['AUDIO_CAPTURE_QUOTA_BYTES']
    target = archive_capture(segment, config['AUDIO_CAPTURE_DIRECTORY'], quota)
    if segment.data_origin != 'measured':
        annotate_capture(target, {'inference_status': 'excluded_simulation'}, quota)
        return
    if not (config.get('AUDIO_PERIODIC_SHADOW_INFERENCE_ENABLED', False)
            or config.get('AUDIO_PERIODIC_PATIENT_ALERTS_ENABLED', False)):
        return
    if not config.get('ML_SERVICE_URL'):
        annotate_capture(target, {'inference_status': 'unavailable'}, quota)
        return
    started = monotonic()
    try:
        if job:
            job.check_cancelled()
        result = classify(pcm_samples=segment.pcm_samples, sample_rate=segment.sample_rate,
                          device_id=segment.device_id, channel_id=segment.channel_id,
                          segment_start_ms=segment.segment_start_ms,
                          segment_end_ms=segment.segment_end_ms)
        if job:
            job.check_cancelled()
        prediction = result['classification']
        signal = ({'type': 'experimental_audio_abnormal', 'clinical_alert': False,
                   'message': 'Prediksi eksperimental abnormal; tinjau rekaman audio.'}
                  if prediction['predicted_class'] == 'abnormal' else None)
        annotate_capture(target, {'inference_status': 'completed',
                                 'experimental_classification': prediction,
                                 'model_version': result['model_version'],
                                 'review_signal': signal,
                                 'inference_ms': (monotonic() - started) * 1000}, quota)
        # Archive prediction first; never publish a patient notification for a
        # capture whose evidence could not be saved. Replay is idempotent in DB.
        notification = notify_periodic_audio(segment, result, config, job)
        annotate_capture(target, {'patient_notification': notification}, quota)
        logger.info('audio_experimental_result device=%s channel=%s capture=%s predicted_class=%s '
                    'review_signal=%s clinical_alert=false inference_ms=%.3f',
                    segment.device_id, segment.channel_id, segment.capture_id,
                    prediction['predicted_class'], signal is not None, (monotonic()-started)*1000)
    except Cancelled:
        annotate_capture(target, {'inference_status': 'cancelled'}, quota)
        raise
    except Exception:
        annotate_capture(target, {'inference_status': 'failed'}, quota)
        raise
