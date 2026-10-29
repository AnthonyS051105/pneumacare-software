"""Quota-limited WAV evidence for unvalidated short recordings, outside the DB."""
import hashlib
import json
import logging
import os
from pathlib import Path
import tempfile
import uuid
import wave

logger = logging.getLogger(__name__)


def archive_capture(segment, directory, quota_bytes):
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    metadata = dict(device_id=segment.device_id, channel_id=segment.channel_id,
                    capture_id=segment.capture_id, stream_id=segment.capture_stream_id, sample_rate=segment.sample_rate,
                    sample_count=len(segment.pcm_samples), start_ms=segment.segment_start_ms,
                    end_ms=segment.segment_end_ms, classification_validated=False,
                    data_origin=segment.data_origin,
                    source_channel_id=segment.source_channel_id or segment.channel_id,
                    alert_eligible=False, inference_status='disabled')
    meta = json.dumps(metadata, sort_keys=True).encode()
    needed = 44 + segment.pcm_samples.nbytes + len(meta)
    if needed > quota_bytes:
        raise ValueError('capture archive quota smaller than one recording')
    existing = sorted([p for p in root.iterdir() if p.suffix in ('.wav','.json')],
                      key=lambda p: p.stat().st_mtime_ns)
    used = sum(p.stat().st_size for p in existing)
    while used + needed > quota_bytes and existing:
        old = existing.pop(0)
        used -= old.stat().st_size
        old.unlink()
        logger.info('audio_capture_retention action=delete_oldest file=%s', old.name)
    device = hashlib.sha256(segment.device_id.encode()).hexdigest()[:12]
    stem = f'{segment.segment_start_ms}-{device}-c{segment.channel_id}-{uuid.uuid4().hex}'
    target = root / (stem + '.wav')
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=root, suffix='.tmp', delete=False) as f:
            temp = Path(f.name)
            with wave.open(f, 'wb') as w:
                w.setnchannels(1)
                w.setsampwidth(2)
                w.setframerate(segment.sample_rate)
                w.writeframes(segment.pcm_samples.astype('<i2', copy=False).tobytes())
        os.replace(temp, target)
        temp = None
        target.with_suffix('.json').write_bytes(meta)
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
    logger.info('audio_capture_saved capture=%s channel=%s samples=%d duration_ms=%d inference=disabled',
                segment.capture_id, segment.channel_id, len(segment.pcm_samples),
                segment.segment_end_ms - segment.segment_start_ms)
    return target


def annotate_capture(target, analysis, quota_bytes):
    """Replace a sidecar atomically, preserving the archive's byte quota."""
    sidecar = target.with_suffix('.json')
    metadata = json.loads(sidecar.read_text())
    metadata.update(analysis)
    meta = json.dumps(metadata, sort_keys=True).encode()
    existing = [p for p in target.parent.iterdir() if p.suffix in ('.wav', '.json')]
    used = sum(p.stat().st_size for p in existing) - sidecar.stat().st_size + len(meta)
    for old in sorted(existing, key=lambda p: p.stat().st_mtime_ns):
        if used <= quota_bytes:
            break
        if old in (target, sidecar):
            continue
        used -= old.stat().st_size
        old.unlink()
    if used > quota_bytes:
        raise ValueError('capture result exceeds archive quota')
    temp = None
    try:
        with tempfile.NamedTemporaryFile(dir=target.parent, suffix='.tmp', delete=False) as f:
            temp = Path(f.name)
            f.write(meta)
        os.replace(temp, sidecar)
        temp = None
    finally:
        if temp is not None:
            temp.unlink(missing_ok=True)
