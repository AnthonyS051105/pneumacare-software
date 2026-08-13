from backend.ingestion.audio_segment_buffer import AudioSegmentBuffer


def test_segment_emitted_only_when_duration_reached():
    buf = AudioSegmentBuffer(segment_duration_ms=10_000)

    for seq in range(9):
        segment, gap = buf.add_chunk(
            device_id="pneumacare-a1b2",
            channel_id=1,
            timestamp_ms=seq * 1000,
            seq_no=seq,
            chunk_duration_ms=1000,
            pcm_samples=[1, 2, 3],
        )
        assert segment is None
        assert gap is None

    segment, gap = buf.add_chunk(
        device_id="pneumacare-a1b2",
        channel_id=1,
        timestamp_ms=9000,
        seq_no=9,
        chunk_duration_ms=1000,
        pcm_samples=[1, 2, 3],
    )
    assert gap is None
    assert segment is not None
    assert segment.device_id == "pneumacare-a1b2"
    assert segment.channel_id == 1
    assert segment.segment_start_ms == 0
    assert segment.segment_end_ms == 10_000
    assert segment.pcm_samples == [1, 2, 3] * 10


def test_channels_are_independent():
    buf = AudioSegmentBuffer(segment_duration_ms=2000)

    seg1, _ = buf.add_chunk("dev1", 1, 0, 0, 1000, [1])
    seg2, _ = buf.add_chunk("dev1", 2, 0, 0, 1000, [2])
    assert seg1 is None
    assert seg2 is None

    seg1, _ = buf.add_chunk("dev1", 1, 1000, 1, 1000, [1])
    assert seg1 is not None
    assert seg1.channel_id == 1

    seg2, _ = buf.add_chunk("dev1", 2, 1000, 1, 1000, [2])
    assert seg2 is not None
    assert seg2.channel_id == 2


def test_gap_detected_on_non_sequential_seq_no():
    buf = AudioSegmentBuffer(segment_duration_ms=10_000)

    buf.add_chunk("dev1", 1, 0, 0, 1000, [1])
    _, gap = buf.add_chunk("dev1", 1, 1000, 5, 1000, [1])

    assert gap is not None
    assert gap.expected_seq_no == 1
    assert gap.received_seq_no == 5


def test_buffer_resets_after_segment_emitted():
    buf = AudioSegmentBuffer(segment_duration_ms=2000)

    buf.add_chunk("dev1", 1, 0, 0, 1000, [1])
    segment, _ = buf.add_chunk("dev1", 1, 1000, 1, 1000, [1])
    assert segment is not None

    # chunk berikutnya mulai segmen baru, bukan lanjut menumpuk dari segmen sebelumnya
    segment, gap = buf.add_chunk("dev1", 1, 2000, 2, 1000, [9])
    assert gap is None  # seq_no lanjut normal
    assert segment is None
    assert segment != [1, 1, 9]


def test_reset_channel_clears_state():
    buf = AudioSegmentBuffer(segment_duration_ms=10_000)
    buf.add_chunk("dev1", 1, 0, 0, 1000, [1])

    buf.reset_channel("dev1", 1)

    # setelah reset, seq_no boleh mulai dari mana saja tanpa terdeteksi gap
    _, gap = buf.add_chunk("dev1", 1, 0, 0, 1000, [1])
    assert gap is None
