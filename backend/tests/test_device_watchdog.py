from datetime import datetime, timedelta

from backend.ingestion.device_watchdog import DeviceSeen, find_stale_devices, mark_stale_devices_offline
from backend.models import db
from backend.models.device import Device, DeviceStatusLog

NOW = datetime(2026, 10, 22, 12, 0, 0)


def test_find_stale_devices_by_timeout():
    devices = [
        DeviceSeen("fresh", "online", NOW - timedelta(seconds=10)),
        DeviceSeen("stale", "online", NOW - timedelta(seconds=31)),
        DeviceSeen("already-offline", "offline", NOW - timedelta(hours=5)),
        DeviceSeen("never-seen", "online", None),
    ]

    assert find_stale_devices(devices, NOW, timeout_seconds=30) == ["stale", "never-seen"]


def test_boundary_exactly_at_timeout_is_not_stale():
    assert find_stale_devices([DeviceSeen("d", "online", NOW - timedelta(seconds=30))], NOW, 30) == []


def test_mark_stale_devices_offline_updates_status_and_log(app):
    with app.app_context():
        db.session.add_all(
            [
                Device(device_id="mati", status="online", last_seen_at=NOW - timedelta(minutes=2)),
                Device(device_id="hidup", status="online", last_seen_at=NOW - timedelta(seconds=5)),
            ]
        )
        db.session.commit()

    changed = mark_stale_devices_offline(app, now=NOW)

    assert changed == ["mati"]
    with app.app_context():
        assert db.session.get(Device, "mati").status == "offline"
        assert db.session.get(Device, "hidup").status == "online"
        log = db.session.query(DeviceStatusLog).filter_by(device_id="mati").one()
        assert log.status == "offline"
    # Idempoten: pemanggilan kedua tidak mencatat ulang.
    assert mark_stale_devices_offline(app, now=NOW) == []
