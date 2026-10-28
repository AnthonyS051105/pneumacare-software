from backend.ingestion.websocket_server import _persist_segment_result
from backend.models import db
from backend.models.classification import ReadingClassification
from backend.models.device import Device


def test_persist_segment_result_writes_classification_columns(app):
    with app.app_context():
        db.session.add(Device(device_id="pneumacare-a1b2", status="online"))
        db.session.commit()

        _persist_segment_result(
            {
                "segment_id": "segment-1",
                "device_id": "pneumacare-a1b2",
                "channel_id": 1,
                "segment_start_ms": 1_700_000_000_000,
                "segment_end_ms": 1_700_000_005_000,
                "classification": {
                    "predicted_class": "abnormal",
                    "confidence": 0.91,
                    "probabilities": {"normal": 0.09, "abnormal": 0.91},
                },
                "model_version": "ast_model_v1.0",
            }
        )

        row = db.session.get(ReadingClassification, "segment-1")
        assert row.predicted_class == "abnormal"
        assert row.confidence == 0.91
        assert row.probabilities == {"normal": 0.09, "abnormal": 0.91}
        assert row.model_version == "ast_model_v1.0"
