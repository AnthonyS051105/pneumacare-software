from datetime import datetime, timezone

from backend.models import db
from backend.models.alert import Alert
from backend.models.device import Device
from backend.models.patient import Patient


def _seed_alert(app, acknowledged: bool = False) -> str:
    with app.app_context():
        device = Device(device_id="pneumacare-a1b2", status="online")
        patient = Patient(id="patient-1", name="Test Pasien")
        db.session.add_all([device, patient])
        db.session.commit()

        alert = Alert(
            id="alert-1",
            device_id=device.device_id,
            patient_id=patient.id,
            level=2,
            triggers=[{"type": "vital_threshold", "parameter": "hr", "value": 50, "threshold": 60}],
            created_at=datetime.now(timezone.utc),
            acknowledged=acknowledged,
        )
        db.session.add(alert)
        db.session.commit()
        return alert.id


def test_acknowledge_marks_alert_as_acknowledged(app, client):
    alert_id = _seed_alert(app)

    response = client.post(f"/api/v1/alerts/{alert_id}/acknowledge")

    assert response.status_code == 200
    body = response.get_json()
    assert body["acknowledged"] is True
    assert body["acknowledged_at"] is not None

    with app.app_context():
        alert = db.session.get(Alert, alert_id)
        assert alert.acknowledged is True
        assert alert.acknowledged_at is not None


def test_acknowledge_nonexistent_alert_returns_404(client):
    response = client.post("/api/v1/alerts/does-not-exist/acknowledge")
    assert response.status_code == 404


def test_acknowledge_already_acknowledged_alert_returns_409(app, client):
    alert_id = _seed_alert(app, acknowledged=True)

    response = client.post(f"/api/v1/alerts/{alert_id}/acknowledge")

    assert response.status_code == 409
