import pytest

from backend.analysis.cycle_segmenter import CycleDetectionResult, CycleSlice
from backend.ingestion import websocket_server
from backend.ingestion.audio_segment_buffer import Segment
from backend.models import db
from backend.models.classification import ReadingClassification
from backend.models.device import Device
from backend.models.respiratory_cycle import RespiratoryCycle
from backend.models.trend import TrendEvent

DEVICE_ID = "pneumacare-a1b2"
ANALYSIS_START_MS = 1_700_000_000_000


def _segment(offset_ms: int = 0) -> Segment:
    return Segment(
        device_id=DEVICE_ID,
        channel_id=1,
        segment_start_ms=ANALYSIS_START_MS + offset_ms,
        segment_end_ms=ANALYSIS_START_MS + offset_ms + 5_000,
        pcm_samples=[0] * 80_000,
        sample_rate=16_000,
    )


def _fake_classify(
    pcm_samples,
    sample_rate,
    device_id,
    channel_id,
    segment_start_ms,
    segment_end_ms,
):
    return {
        "segment_id": f"cls-{segment_start_ms}",
        "device_id": device_id,
        "channel_id": channel_id,
        "segment_start_ms": segment_start_ms,
        "segment_end_ms": segment_end_ms,
        "classification": {
            "predicted_class": "normal",
            "confidence": 0.9,
            "probabilities": {"normal": 0.9, "abnormal": 0.1},
        },
        "model_version": "test",
    }


def test_handle_segment_classifies_each_cycle_and_persists_boundaries(app, monkeypatch):
    detection = CycleDetectionResult(
        status="detected",
        cycles=[
            CycleSlice(
                index=1,
                start_s=0.5,
                end_s=2.0,
                pcm_samples=[1] * 24_000,
                dtw_score=0.11,
            ),
            CycleSlice(
                index=2,
                start_s=2.0,
                end_s=4.5,
                pcm_samples=[2] * 40_000,
                dtw_score=0.22,
            ),
        ],
        mean_dtw=0.165,
    )

    with app.app_context():
        db.session.add(Device(device_id=DEVICE_ID, status="online"))
        db.session.commit()

        monkeypatch.setattr(websocket_server, "detect_cycle_slices", lambda *_: detection)
        monkeypatch.setattr(websocket_server, "_classify_input", _fake_classify)

        websocket_server._handle_segment(_segment())

        classifications = (
            db.session.query(ReadingClassification)
            .order_by(ReadingClassification.segment_start)
            .all()
        )
        cycle_rows = (
            db.session.query(RespiratoryCycle)
            .order_by(RespiratoryCycle.cycle_start_ms)
            .all()
        )

    assert len(classifications) == 2
    assert len(cycle_rows) == 2

    first, second = cycle_rows
    assert first.detection_status == "detected"
    assert first.cycle_index == 1
    assert first.cycle_start_ms == ANALYSIS_START_MS + 500
    assert first.cycle_end_ms == ANALYSIS_START_MS + 2_000
    assert first.classification_id == classifications[0].id
    assert first.mean_dtw == pytest.approx(0.165)
    assert first.dtw_score == pytest.approx(0.11)

    assert second.cycle_index == 2
    assert second.cycle_start_ms == ANALYSIS_START_MS + 2_000
    assert second.cycle_end_ms == ANALYSIS_START_MS + 4_500
    assert second.dtw_score == pytest.approx(0.22)


def test_handle_segment_falls_back_to_full_segment_without_cycles(app, monkeypatch):
    detection = CycleDetectionResult(status="no_cycles")

    with app.app_context():
        db.session.add(Device(device_id=DEVICE_ID, status="online"))
        db.session.commit()

        monkeypatch.setattr(websocket_server, "detect_cycle_slices", lambda *_: detection)
        monkeypatch.setattr(websocket_server, "_classify_input", _fake_classify)

        websocket_server._handle_segment(_segment())

        classifications = db.session.query(ReadingClassification).all()
        cycle_rows = db.session.query(RespiratoryCycle).all()

    assert len(classifications) == 1

    assert len(cycle_rows) == 1
    fallback = cycle_rows[0]
    assert fallback.detection_status == "no_cycles"
    assert fallback.classification_id == classifications[0].id
    assert fallback.cycle_index is None
    assert fallback.cycle_start_ms is None
    assert fallback.cycle_end_ms is None
    assert fallback.mean_dtw is None
    assert fallback.dtw_score is None


def test_handle_segment_feeds_cycle_classifications_into_trend_analysis(app, monkeypatch):
    detection = CycleDetectionResult(
        status="detected",
        cycles=[
            CycleSlice(index=1, start_s=0.5, end_s=2.0, pcm_samples=[1] * 100, dtw_score=None),
            CycleSlice(index=2, start_s=2.0, end_s=3.5, pcm_samples=[2] * 100, dtw_score=None),
            CycleSlice(index=3, start_s=3.5, end_s=4.5, pcm_samples=[3] * 100, dtw_score=None),
        ],
        mean_dtw=0.2,
    )

    with app.app_context():
        db.session.add(Device(device_id=DEVICE_ID, status="online"))
        db.session.commit()

        monkeypatch.setattr(websocket_server, "detect_cycle_slices", lambda *_: detection)
        monkeypatch.setattr(websocket_server, "_classify_input", _fake_classify)

        # 3 klasifikasi per segmen; trend baru punya >=2 titik rolling window
        # setelah 7+ klasifikasi (window 6).
        websocket_server._handle_segment(_segment())
        websocket_server._handle_segment(_segment(offset_ms=5_000))
        assert db.session.query(TrendEvent).count() == 0

        websocket_server._handle_segment(_segment(offset_ms=10_000))

        assert db.session.query(ReadingClassification).count() == 9
        assert db.session.query(RespiratoryCycle).count() == 9
        assert db.session.query(TrendEvent).count() == 1
