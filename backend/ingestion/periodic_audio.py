"""Bounded, four-channel, explicit recording windows. Idle gaps are not audio."""
from dataclasses import replace
from time import time

from backend.ingestion.audio_segment_buffer import AudioSegmentBuffer
from backend.ingestion.audio_provenance import parse_provenance
import numpy as np


class PeriodicCaptureAssembler:
    def __init__(self, duration_ms, compatible_durations=()):
        self.duration_ms = duration_ms
        self.allowed_durations = {duration_ms, *compatible_durations}
        self.window_duration_ms = duration_ms
        self.capture_id = 0
        self.discarded_samples = 0
        self.invalidate()

    def invalidate(self):
        self.discarded_samples += sum(self.offsets.values()) if hasattr(self, 'offsets') else 0
        self.buffer = AudioSegmentBuffer(self.window_duration_ms)
        self.offsets = {}
        self.segments = {}
        self.provenance = {}
        self.failed = True
        self.start_ms = None
        self.wire_start_ms = None

    def add(self, h, pcm):
        try:
            for k in ('capture_id','capture_duration_ms','capture_offset_samples','capture_start_ms'):
                if type(h.get(k)) is not int:
                    raise ValueError('capture integers')
            cid, ch, offset = h['capture_id'], h['channel_id'], h['capture_offset_samples']
            duration = h['capture_duration_ms']
            provenance = parse_provenance(h)
            if (not 0 < cid < 2**32 or duration not in self.allowed_durations
                    or h['sample_rate'] != 16000 or not h.get('stream_id')
                    or h.get('sample_start') is None or offset < 0
                    or not 0 <= h['capture_start_ms'] < 253402300799000):
                raise ValueError('capture format')
            if cid > self.capture_id:
                self.window_duration_ms = duration
                self.invalidate()
                self.capture_id, self.failed = cid, False
                self.wire_start_ms = h['capture_start_ms']
                self.start_ms = (self.wire_start_ms if self.wire_start_ms >= 1700000000000
                                 else int(time()*1000) - h['chunk_duration_ms'])
            if (cid != self.capture_id or self.failed or ch in self.segments
                    or duration != self.window_duration_ms
                    or h['capture_start_ms'] != self.wire_start_ms
                    or self.provenance.get(ch, provenance) != provenance
                    or offset != self.offsets.get(ch, 0)
                    or offset + len(pcm) > self.window_duration_ms * 16):
                raise ValueError('capture order/boundary')
            self.provenance[ch] = provenance
            segment, gap = self.buffer.add_chunk(
                h['device_id'], ch, self.start_ms + offset // 16, h['seq_no'],
                h['chunk_duration_ms'], pcm, h['sample_rate'], h['sample_start'], h['stream_id'],
                *provenance)
            if gap:
                raise ValueError('capture discontinuity')
            self.offsets[ch] = offset + len(pcm)
            if segment is not None:
                self.segments[ch] = replace(segment, capture_id=cid, capture_stream_id=h['stream_id'])
            if len(self.segments) == 4:
                result = [self.segments[ch] for ch in range(1, 5)]
                for segment in result:
                    if segment.data_origin == 'simulated':
                        source = self.segments[segment.source_channel_id]
                        if source.data_origin != 'measured' or not np.array_equal(
                                source.pcm_samples, segment.pcm_samples):
                            raise ValueError('simulation must copy its declared measured source')
                self.failed = True  # completed ID cannot be replayed
                self.offsets = {}
                self.segments = {}
                return result
            return None
        except (ValueError, KeyError):
            self.invalidate()
            raise ValueError('invalid recording window') from None
