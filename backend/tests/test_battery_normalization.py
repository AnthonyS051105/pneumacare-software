from backend.ingestion.mqtt_subscriber import _handle_status, normalize_battery_pct
from backend.models import db
from backend.models.device import Device


def test_normalize_battery_pct():
    assert normalize_battery_pct(87) == 87.0
    assert normalize_battery_pct(0) == 0.0
    assert normalize_battery_pct(100) == 100.0
    # -1 = penanda firmware "sensor baterai belum ada"
    assert normalize_battery_pct(-1) is None
    assert normalize_battery_pct(101) is None
    assert normalize_battery_pct("87") is None
    assert normalize_battery_pct(True) is None


def test_status_with_firmware_sentinel_stores_unknown_battery(app):
    _handle_status(app, "pneumacare-hw", {"status": "online", "battery_pct": -1})

    with app.app_context():
        device = db.session.get(Device, "pneumacare-hw")
        assert device.status == "online"
        assert device.battery_percent is None


def test_status_with_valid_battery_is_stored(app):
    _handle_status(app, "pneumacare-hw", {"status": "online", "battery_pct": 64})

    with app.app_context():
        assert db.session.get(Device, "pneumacare-hw").battery_percent == 64.0
