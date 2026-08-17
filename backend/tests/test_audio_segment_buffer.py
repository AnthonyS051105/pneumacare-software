from backend.ingestion.audio_segment_buffer import AudioSegmentBuffer

SAMPLE_RATE = 16_000  # native rate mikrofon firmware, INTEGRATION_CONTRACT.md §2.3


def test_segment_emitted_only_when_duration_reached():
    buf = AudioSegmentBuffer(segment_duration_ms=5_000)

    for seq in range(4):
        segment, gap = buf.add_chunk(
            device_id="pneumacare-a1b2",
            channel_id=1,
            timestamp_ms=seq * 1000,
            seq_no=seq,
            chunk_duration_ms=1000,
            pcm_samples=[1, 2, 3],
            sample_rate=SAMPLE_RATE,
        )
        assert segment is None
        assert gap is None

    segment, gap = buf.add_chunk(
        device_id="pneumacare-a1b2",
        channel_id=1,
        timestamp_ms=4000,
        seq_no=4,
        chunk_duration_ms=1000,
        pcm_samples=[1, 2, 3],
        sample_rate=SAMPLE_RATE,
    )
    assert gap is None
    assert segment is not None
    assert segment.device_id == "pneumacare-a1b2"
    assert segment.channel_id == 1
    assert segment.segment_start_ms == 0
    assert segment.segment_end_ms == 5_000
    assert segment.pcm_samples == [1, 2, 3] * 5
    assert segment.sample_rate == SAMPLE_RATE


def test_channels_are_independent():
    buf = AudioSegmentBuffer(segment_duration_ms=2000)

    seg1, _ = buf.add_chunk("dev1", 1, 0, 0, 1000, [1], SAMPLE_RATE)
    seg2, _ = buf.add_chunk("dev1", 2, 0, 0, 1000, [2], SAMPLE_RATE)
    assert seg1 is None
    assert seg2 is None

    seg1, _ = buf.add_chunk("dev1", 1, 1000, 1, 1000, [1], SAMPLE_RATE)
    assert seg1 is not None
    assert seg1.channel_id == 1

    seg2, _ = buf.add_chunk("dev1", 2, 1000, 1, 1000, [2], SAMPLE_RATE)
    assert seg2 is not None
    assert seg2.channel_id == 2


def test_gap_detected_on_non_sequential_seq_no():
    buf = AudioSegmentBuffer(segment_duration_ms=5_000)

    buf.add_chunk("dev1", 1, 0, 0, 1000, [1], SAMPLE_RATE)
    _, gap = buf.add_chunk("dev1", 1, 1000, 5, 1000, [1], SAMPLE_RATE)

    assert gap is not None
    assert gap.expected_seq_no == 1
    assert gap.received_seq_no == 5


def test_buffer_resets_after_segment_emitted():
    buf = AudioSegmentBuffer(segment_duration_ms=2000)

    buf.add_chunk("dev1", 1, 0, 0, 1000, [1], SAMPLE_RATE)
    segment, _ = buf.add_chunk("dev1", 1, 1000, 1, 1000, [1], SAMPLE_RATE)
    assert segment is not None

    # chunk berikutnya mulai segmen baru, bukan lanjut menumpuk dari segmen sebelumnya
    segment, gap = buf.add_chunk("dev1", 1, 2000, 2, 1000, [9], SAMPLE_RATE)
    assert gap is None  # seq_no lanjut normal
    assert segment is None
    assert segment != [1, 1, 9]


def test_reset_channel_clears_state():
    buf = AudioSegmentBuffer(segment_duration_ms=5_000)
    buf.add_chunk("dev1", 1, 0, 0, 1000, [1], SAMPLE_RATE)

    buf.reset_channel("dev1", 1)

    # setelah reset, seq_no boleh mulai dari mana saja tanpa terdeteksi gap
    _, gap = buf.add_chunk("dev1", 1, 0, 0, 1000, [1], SAMPLE_RATE)
    assert gap is None


def test_sample_rate_captured_from_first_chunk_of_segment():
    buf = AudioSegmentBuffer(segment_duration_ms=2000)

    buf.add_chunk("dev1", 1, 0, 0, 1000, [1], sample_rate=16_000)
    # chunk kedua kirim sample_rate berbeda (skenario tepi, seharusnya tidak terjadi
    # normal — tapi buffer tetap pakai sample_rate dari chunk PERTAMA segmen ini)
    segment, _ = buf.add_chunk("dev1", 1, 1000, 1, 1000, [1], sample_rate=8_000)

    assert segment is not None
    assert segment.sample_rate == 16_000
