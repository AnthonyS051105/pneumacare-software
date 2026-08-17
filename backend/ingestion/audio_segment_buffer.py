"""Logika murni penyusunan ulang chunk audio kecil menjadi segmen 5 detik
(INTEGRATION_CONTRACT.md §2.2, §4.1 — durasi segmen model dikoreksi dari asumsi
awal 10 detik menjadi 5 detik, terverifikasi dari kode preprocessing asli Nathanael).

Dipisahkan dari I/O (websocket) supaya mudah di-unit-test (FR-SW-002) — lihat pola
yang sama di trend_analysis (SDD_SOFTWARE.md §6).

⚠️ Sample rate yang disimpan di sini adalah sample rate ASLI FIRMWARE (mis. 16000 Hz,
dari header chunk — INTEGRATION_CONTRACT.md §2.3), BUKAN 22000 Hz target model.
Resample ke 22000 Hz dilakukan SEKALI di `inference/preprocessing.py` atas segmen
5 detik penuh, bukan per-chunk kecil — lihat docstring modul itu untuk alasannya.
"""

from dataclasses import dataclass, field


@dataclass
class GapEvent:
    device_id: str
    channel_id: int
    expected_seq_no: int
    received_seq_no: int


@dataclass
class Segment:
    device_id: str
    channel_id: int
    segment_start_ms: int
    segment_end_ms: int
    pcm_samples: list[int]
    sample_rate: int


@dataclass
class _ChannelBuffer:
    pcm_samples: list[int] = field(default_factory=list)
    segment_start_ms: int | None = None
    accumulated_ms: int = 0
    last_seq_no: int | None = None
    sample_rate: int | None = None


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
    ) -> tuple[Segment | None, GapEvent | None]:
        key = (device_id, channel_id)
        buf = self._buffers.setdefault(key, _ChannelBuffer())

        gap_event: GapEvent | None = None
        if buf.last_seq_no is not None and seq_no != buf.last_seq_no + 1:
            gap_event = GapEvent(
                device_id=device_id,
                channel_id=channel_id,
                expected_seq_no=buf.last_seq_no + 1,
                received_seq_no=seq_no,
            )
        buf.last_seq_no = seq_no

        if buf.segment_start_ms is None:
            buf.segment_start_ms = timestamp_ms
            buf.sample_rate = sample_rate

        buf.pcm_samples.extend(pcm_samples)
        buf.accumulated_ms += chunk_duration_ms

        segment: Segment | None = None
        if buf.accumulated_ms >= self._segment_duration_ms:
            segment = Segment(
                device_id=device_id,
                channel_id=channel_id,
                segment_start_ms=buf.segment_start_ms,
                segment_end_ms=buf.segment_start_ms + buf.accumulated_ms,
                pcm_samples=buf.pcm_samples,
                sample_rate=buf.sample_rate,
            )
            self._buffers[key] = _ChannelBuffer(last_seq_no=buf.last_seq_no)

        return segment, gap_event

    def reset_channel(self, device_id: str, channel_id: int) -> None:
        """Dipanggil saat websocket reconnect — state segmen boleh direset (§2.4)."""
        self._buffers.pop((device_id, channel_id), None)
