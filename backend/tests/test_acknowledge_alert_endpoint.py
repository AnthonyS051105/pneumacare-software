from datetime import datetime, timezone

from backend.models import db
from backend.models.alert import Alert
from backend.models.device import Device
from backend.models.patient import Patient
from backend.tests.conftest import create_user, login_as


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


def _login_clinician(app, client):
    create_user(app, "dr@example.com", "password123", role="clinician")
    login_as(client, "dr@example.com", "password123")


def test_acknowledge_marks_alert_as_acknowledged(app, client):
    alert_id = _seed_alert(app)
    _login_clinician(app, client)

    response = client.post(f"/api/v1/alerts/{alert_id}/acknowledge")

    assert response.status_code == 200
    body = response.get_json()
    assert body["acknowledged"] is True
    assert body["acknowledged_at"] is not None
    assert body["acknowledged_by"] is not None

    with app.app_context():
        alert = db.session.get(Alert, alert_id)
        assert alert.acknowledged is True
        assert alert.acknowledged_at is not None


def test_acknowledge_without_login_returns_401(app, client):
    alert_id = _seed_alert(app)

    response = client.post(f"/api/v1/alerts/{alert_id}/acknowledge")

    assert response.status_code == 401


def test_acknowledge_as_patient_returns_403(app, client):
    alert_id = _seed_alert(app)
    create_user(app, "pasien@example.com", "password123", role="pasien")
    login_as(client, "pasien@example.com", "password123")

    response = client.post(f"/api/v1/alerts/{alert_id}/acknowledge")

    assert response.status_code == 403


def test_acknowledge_nonexistent_alert_returns_404(app, client):
    _login_clinician(app, client)
    response = client.post("/api/v1/alerts/does-not-exist/acknowledge")
    assert response.status_code == 404


def test_acknowledge_already_acknowledged_alert_returns_409(app, client):
    alert_id = _seed_alert(app, acknowledged=True)
    _login_clinician(app, client)

    response = client.post(f"/api/v1/alerts/{alert_id}/acknowledge")

    assert response.status_code == 409
