from backend.ingestion.device_registry import upsert_device_seen
from backend.models import db
from backend.models.device import Device


def test_upsert_creates_new_device(app):
    with app.app_context():
        upsert_device_seen("pneumacare-a1b2")
        device = db.session.get(Device, "pneumacare-a1b2")
        assert device is not None
        assert device.status == "online"
        assert device.last_seen_at is not None


def test_upsert_updates_existing_device_without_duplicate(app):
    with app.app_context():
        upsert_device_seen("pneumacare-a1b2")
        first_seen_at = db.session.get(Device, "pneumacare-a1b2").last_seen_at

        upsert_device_seen("pneumacare-a1b2", battery_percent=42.0)

        devices = Device.query.filter_by(device_id="pneumacare-a1b2").all()
        assert len(devices) == 1
        assert devices[0].battery_percent == 42.0
        assert devices[0].last_seen_at >= first_seen_at


def test_upsert_called_twice_in_a_row_does_not_raise_integrity_error(app):
    # Mensimulasikan dua thread (websocket + mqtt_subscriber) yang sama-sama
    # melihat device_id baru nyaris bersamaan — regression test untuk race
    # condition yang sebelumnya menyebabkan UNIQUE constraint error.
    with app.app_context():
        upsert_device_seen("pneumacare-a1b2")
        upsert_device_seen("pneumacare-a1b2")
        assert Device.query.filter_by(device_id="pneumacare-a1b2").count() == 1
