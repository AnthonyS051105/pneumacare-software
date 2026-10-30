"""Pure assembly of contiguous PCM into configurable analysis windows.

Continuous streams default to five seconds. Explicit periodic recordings use a
separate bounded assembler; idle gaps are never concatenated. Samples retain their
source rate here. The AST service handles its own 16 kHz preprocessing.
"""

from dataclasses import dataclass, field
from array import array
import numpy as np


@dataclass
class GapEvent:
    device_id: str
    channel_id: int
    expected_seq_no: int
    received_seq_no: int
    reason: str = "sequence_gap"
    lost_samples: int | None = None
    discarded_samples: int = 0


@dataclass(frozen=True)
class Segment:
    device_id: str
    channel_id: int
    segment_start_ms: int
    segment_end_ms: int
    pcm_samples: np.ndarray
    sample_rate: int
    capture_id: int | None = None
    capture_stream_id: str | None = None
    data_origin: str = 'measured'
    source_channel_id: int | None = None
    # Backend-only identity; changes on reconnect/reset, independent of ESP boot.
    reception_session_id: str | None = None


@dataclass
class _ChannelBuffer:
    pcm_samples: array = field(default_factory=lambda: array("h"))
    segment_start_ms: int | None = None
    accumulated_ms: int = 0
    last_seq_no: int | None = None
    sample_rate: int | None = None
    next_sample: int | None = None
    stream_id: str | None = None
    next_timestamp_ms: int | None = None
    provenance: tuple | None = None


class AudioSegmentBuffer:
    """Akumulasi chunk per (device_id, channel_id) sampai genap `segment_duration_ms`.

    `add_chunk` mengembalikan (Segment | None, GapEvent | None) — Segment terisi
    hanya saat buffer sudah genap durasi segmen dan buffer direset untuk segmen berikutnya.
    """

    def __init__(self, segment_duration_ms: int = 5_000) -> None:
        self._segment_duration_ms = segment_duration_ms
        self._buffers: dict[tuple[str, int], _ChannelBuffer] = {}

    def add_chunk(
        self,
        device_id: str,
        channel_id: int,
        timestamp_ms: int,
        seq_no: int,
        chunk_duration_ms: int,
        pcm_samples: list[int],
        sample_rate: int,
        sample_start: int | None = None,
        stream_id: str | None = None,
        data_origin: str = 'measured',
        source_channel_id: int | None = None,
    ) -> tuple[Segment | None, GapEvent | None]:
        key = (device_id, channel_id)
        buf = self._buffers.setdefault(key, _ChannelBuffer())

        gap_event: GapEvent | None = None
        reason = None
        lost = None
        provenance = (data_origin, source_channel_id or channel_id)
        if buf.last_seq_no is not None:
            if buf.stream_id != stream_id:
                reason = "stream_change"
            elif buf.sample_rate is not None and buf.sample_rate != sample_rate:
                reason = "format_change"
            elif buf.provenance != provenance:
                reason = "provenance_change"
            elif seq_no != buf.last_seq_no + 1:
                reason = "sequence_gap"
            if reason is None and buf.next_sample != sample_start:
                reason = "sample_gap"
            if buf.next_sample is not None and sample_start is not None and stream_id == buf.stream_id:
                lost = max(0, sample_start - buf.next_sample)
            # Legacy timestamps are estimated at send, so tolerate 100 ms jitter.
            # Sample indexes take precedence: a later NTP jump does not lose PCM.
            if (reason is None and sample_start is None and buf.next_timestamp_ms is not None
                    and abs(timestamp_ms - buf.next_timestamp_ms) > 100):
                reason = "timestamp_gap"
            if reason:
                gap_event = GapEvent(device_id, channel_id, buf.last_seq_no + 1, seq_no,
                                     reason, lost, len(buf.pcm_samples))
                buf = _ChannelBuffer()
                self._buffers[key] = buf
        buf.last_seq_no = seq_no
        buf.provenance = provenance
        buf.next_sample = sample_start + len(pcm_samples) if sample_start is not None else None
        buf.stream_id = stream_id
        buf.next_timestamp_ms = timestamp_ms + chunk_duration_ms

        if buf.segment_start_ms is None:
            buf.segment_start_ms = timestamp_ms
            buf.sample_rate = sample_rate

        remaining_ms = self._segment_duration_ms - buf.accumulated_ms
        take_ms = min(chunk_duration_ms, remaining_ms)
        take = len(pcm_samples) if take_ms == chunk_duration_ms else sample_rate * take_ms // 1000
        buf.pcm_samples.extend(pcm_samples[:take])
        buf.accumulated_ms += take_ms

        segment: Segment | None = None
        if buf.accumulated_ms == self._segment_duration_ms:
            # Immutable bytes backing: neither caller nor the next buffer can mutate a job.
            pcm = np.frombuffer(buf.pcm_samples.tobytes(), dtype=np.int16)
            segment = Segment(device_id, channel_id, buf.segment_start_ms,
                              buf.segment_start_ms + self._segment_duration_ms, pcm, sample_rate,
                              data_origin=data_origin, source_channel_id=provenance[1])
            buf.pcm_samples = array("h", pcm_samples[take:])
            buf.segment_start_ms = segment.segment_end_ms if take < len(pcm_samples) else None
            buf.accumulated_ms = chunk_duration_ms - take_ms
        buf.sample_rate = sample_rate

        return segment, gap_event

    def reset_channel(self, device_id: str, channel_id: int) -> None:
        """Dipanggil saat websocket reconnect — state segmen boleh direset (§2.4)."""
        self._buffers.pop((device_id, channel_id), None)

    def reset_device(self, device_id: str) -> int:
        discarded = 0
        for key in list(self._buffers):
            if key[0] == device_id:
                discarded += len(self._buffers.pop(key).pcm_samples)
        return discarded
