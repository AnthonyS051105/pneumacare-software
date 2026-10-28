"""Malformed traffic must not poison later MQTT delivery or PPG windows."""
import json
from types import SimpleNamespace

import pytest

from backend.ingestion import mqtt_subscriber as subscriber
from backend.models import db
from backend.models.device import Device


@pytest.fixture(autouse=True)
def reset_ppg():
    subscriber.raw_ppg_buffers.clear()
    subscriber._ir_sample_buffers.clear()
    subscriber._red_sample_buffers.clear()
    yield
    subscriber.raw_ppg_buffers.clear()
    subscriber._ir_sample_buffers.clear()
    subscriber._red_sample_buffers.clear()


def deliver(client, payload, topic="pneumacare/test-device/ppg/raw"):
    client.on_message(client, None, SimpleNamespace(topic=topic, payload=json.dumps(payload).encode()))


@pytest.mark.parametrize("payload", [
    [], None, 3, "text", {},
    {"samples": "123"}, {"samples": [True]}, {"samples": [float("nan")]},
    {"samples": [float("inf")]}, {"samples": [1], "sample_rate_hz": 0},
    {"samples": [1], "sample_rate_hz": True},
    {"samples": [1], "sample_rate_hz": 1001},
    {"samples": [1], "samples_red": []},
    {"samples": [1], "samples_red": [False]},
    {"samples": [1] * 2001}, {"samples": [1], "device_id": "other-device"},
])
def test_invalid_ppg_rejected_before_mutation_and_next_message_survives(app, payload):
    client = subscriber.create_mqtt_client(app)
    deliver(client, payload)
    assert not subscriber.raw_ppg_buffers
    assert not subscriber._ir_sample_buffers
    with app.app_context():
        assert db.session.get(Device, "test-device") is None
    deliver(client, {"samples": [100, 101], "samples_red": [90, 91]})
    assert subscriber._ir_sample_buffers["test-device"] == [100, 101]


@pytest.mark.parametrize("topic", ["x/test-device/ppg/raw", "pneumacare//ppg/raw", "pneumacare/test-device/x/ppg/raw"])
def test_unrecognized_topic_rejected(app, topic):
    deliver(subscriber.create_mqtt_client(app), {"samples": [1]}, topic)
    assert not subscriber.raw_ppg_buffers


def test_bad_batch_discards_partial_window(app):
    client = subscriber.create_mqtt_client(app)
    deliver(client, {"samples": [1, 2]})
    deliver(client, {"samples": [False]})
    deliver(client, {"samples": [3]})
    assert subscriber._ir_sample_buffers["test-device"] == [3]


def test_handler_error_rolls_back_and_next_message_survives(app, monkeypatch):
    client = subscriber.create_mqtt_client(app)
    original = subscriber.upsert_device_seen

    def fail_after_pending_insert(device_id, **kwargs):
        db.session.add(Device(device_id="must-rollback", status="online"))
        raise RuntimeError("synthetic handler failure")

    monkeypatch.setattr(subscriber, "upsert_device_seen", fail_after_pending_insert)
    deliver(client, {"samples": [1, 2]})
    assert not subscriber._ir_sample_buffers
    monkeypatch.setattr(subscriber, "upsert_device_seen", original)
    deliver(client, {"samples": [3]})
    with app.app_context():
        assert db.session.get(Device, "must-rollback") is None
        assert db.session.get(Device, "test-device") is not None
    assert subscriber._ir_sample_buffers["test-device"] == [3]


def test_status_wrong_shape_does_not_stop_next_status(app):
    client = subscriber.create_mqtt_client(app)
    topic = "pneumacare/test-device/status"
    deliver(client, [], topic)
    deliver(client, {"status": "online", "battery_pct": 50}, topic)
    with app.app_context():
        assert db.session.get(Device, "test-device").status == "online"


def test_integer_too_large_for_float_does_not_escape_callback(app):
    client = subscriber.create_mqtt_client(app)
    deliver(client, {"samples": [10 ** 400]})
    assert not subscriber._ir_sample_buffers
    deliver(client, {"samples": [3]})
    assert subscriber._ir_sample_buffers["test-device"] == [3]


def test_payload_byte_limit_checked_before_json_decode(app):
    app.config["MQTT_MAX_PAYLOAD_BYTES"] = 64
    client = subscriber.create_mqtt_client(app)
    deliver(client, {"samples": [1], "unused": "x" * 100})
    assert not subscriber.raw_ppg_buffers
    deliver(client, {"samples": [3]})
    assert subscriber._ir_sample_buffers["test-device"] == [3]


def test_raw_history_retains_only_sixty_batches(app):
    client = subscriber.create_mqtt_client(app)
    for value in range(100):
        deliver(client, {"samples": [value]})
    history = subscriber.raw_ppg_buffers["test-device"]
    assert len(history) == 60
    assert history[0]["samples"] == [40]


@pytest.mark.parametrize("payload", [
    {"samples": [-1]}, {"samples": [4294967296]},
    {"samples": [1], "samples_red": [-0.5]},
    {"samples": [1], "samples_red": [4294967296]},
    {"samples": [1], "timestamp_ms": True},
    {"samples": [1], "timestamp_ms": -1},
    {"samples": [1], "timestamp_ms": 1.5},
    {"samples": [1], "timestamp_ms": "1000"},
])
def test_adc_range_and_timestamp_rejected(app, payload):
    client = subscriber.create_mqtt_client(app)
    deliver(client, payload)
    assert not subscriber.raw_ppg_buffers
    deliver(client, {"samples": [0, 1.5, 4294967295], "timestamp_ms": 0})
    assert subscriber._ir_sample_buffers["test-device"] == [0, 1.5, 4294967295]


@pytest.mark.parametrize("status", ["unknown", True, 1, [], {}, None])
def test_invalid_status_enum_rejected(app, status):
    client = subscriber.create_mqtt_client(app)
    topic = "pneumacare/test-device/status"
    deliver(client, {"status": status}, topic)
    with app.app_context():
        assert db.session.get(Device, "test-device") is None
    deliver(client, {"status": "offline", "battery_pct": -1}, topic)
    with app.app_context():
        device = db.session.get(Device, "test-device")
        assert device.status == "offline"
        assert device.battery_percent is None
