from datetime import datetime, timezone

from backend.models import db
from backend.models.alert import Alert
from backend.models.device import Device
from backend.models.patient import Patient
from backend.models.severity import ReadingSeverity
from backend.models.threshold import Threshold
from backend.models.trend import TrendEvent
from backend.models.vital import ReadingVital
from backend.tests.conftest import create_user, login_as


def _seed_clinician_with_patient(app) -> tuple[str, str]:
    """Return (clinician_user_id, patient_id)."""
    clinician_id = create_user(app, "dr@example.com", "password123", role="clinician")
    with app.app_context():
        device = Device(device_id="pneumacare-a1b2", status="online", battery_percent=80)
        patient = Patient(id="patient-1", name="Test Pasien", assigned_clinician_id=clinician_id)
        device.patient_id = patient.id
        db.session.add_all([device, patient])
        db.session.commit()
    return clinician_id, "patient-1"


def _login_clinician(client):
    return login_as(client, "dr@example.com", "password123")


def test_list_patients_requires_login(client):
    response = client.get("/api/v1/patients")
    assert response.status_code == 401


def test_list_patients_returns_only_own_patients(app, client):
    _seed_clinician_with_patient(app)
    _login_clinician(client)

    response = client.get("/api/v1/patients")

    assert response.status_code == 200
    body = response.get_json()
    assert len(body) == 1
    assert body[0]["id"] == "patient-1"


def test_list_patients_as_patient_role_returns_403(app, client):
    _seed_clinician_with_patient(app)
    create_user(app, "pasien@example.com", "password123", role="pasien")
    login_as(client, "pasien@example.com", "password123")

    response = client.get("/api/v1/patients")

    assert response.status_code == 403


def test_vitals_latest_returns_data(app, client):
    _seed_clinician_with_patient(app)
    with app.app_context():
        db.session.add(
            ReadingVital(device_id="pneumacare-a1b2", timestamp=datetime.now(timezone.utc), hr=75, spo2=97, rr=16)
        )
        db.session.commit()
    _login_clinician(client)

    response = client.get("/api/v1/patients/patient-1/vitals/latest")

    assert response.status_code == 200
    body = response.get_json()
    assert body["hr"] == 75


def test_vitals_latest_for_unowned_patient_returns_404(app, client):
    _seed_clinician_with_patient(app)
    with app.app_context():
        db.session.add(Patient(id="other-patient", name="Bukan Pasienku"))
        db.session.commit()
    _login_clinician(client)

    response = client.get("/api/v1/patients/other-patient/vitals/latest")

    assert response.status_code == 404


def test_severity_latest_returns_data(app, client):
    _seed_clinician_with_patient(app)
    with app.app_context():
        db.session.add(
            ReadingSeverity(
                id="seg-1",
                device_id="pneumacare-a1b2",
                channel_id=1,
                segment_start=datetime.now(timezone.utc),
                segment_end=datetime.now(timezone.utc),
                wheeze_present=True,
                wheeze_confidence=0.8,
                crackle_present=False,
                crackle_confidence=0.1,
                model_version="mock_v1",
            )
        )
        db.session.commit()
    _login_clinician(client)

    response = client.get("/api/v1/patients/patient-1/severity/latest")

    assert response.status_code == 200
    assert response.get_json()["wheeze_present"] is True


def test_trend_returns_data(app, client):
    _seed_clinician_with_patient(app)
    with app.app_context():
        db.session.add(
            TrendEvent(
                device_id="pneumacare-a1b2",
                window_start=datetime.now(timezone.utc),
                window_end=datetime.now(timezone.utc),
                slope=0.2,
                significant=True,
            )
        )
        db.session.commit()
    _login_clinician(client)

    response = client.get("/api/v1/patients/patient-1/trend")

    assert response.status_code == 200
    assert response.get_json()["significant"] is True


def test_patient_alerts_list(app, client):
    _seed_clinician_with_patient(app)
    with app.app_context():
        db.session.add(
            Alert(
                id="alert-1",
                device_id="pneumacare-a1b2",
                patient_id="patient-1",
                level=2,
                triggers=[{"type": "vital_threshold", "parameter": "hr", "value": 50, "threshold": 60}],
                created_at=datetime.now(timezone.utc),
            )
        )
        db.session.commit()
    _login_clinician(client)

    response = client.get("/api/v1/patients/patient-1/alerts")

    assert response.status_code == 200
    assert len(response.get_json()) == 1


def test_clinician_alerts_center_cross_patient(app, client):
    clinician_id, _ = _seed_clinician_with_patient(app)
    with app.app_context():
        device2 = Device(device_id="pneumacare-b2c3", status="online")
        patient2 = Patient(id="patient-2", name="Pasien Kedua", assigned_clinician_id=clinician_id)
        db.session.add_all([device2, patient2])
        db.session.add_all(
            [
                Alert(
                    id="alert-1",
                    device_id="pneumacare-a1b2",
                    patient_id="patient-1",
                    level=2,
                    triggers=[],
                    created_at=datetime.now(timezone.utc),
                ),
                Alert(
                    id="alert-2",
                    device_id="pneumacare-b2c3",
                    patient_id="patient-2",
                    level=3,
                    triggers=[],
                    created_at=datetime.now(timezone.utc),
                ),
            ]
        )
        db.session.commit()
    _login_clinician(client)

    response = client.get("/api/v1/clinician/alerts")

    assert response.status_code == 200
    assert len(response.get_json()) == 2


def test_get_thresholds_returns_null_defaults_when_not_set(app, client):
    _seed_clinician_with_patient(app)
    _login_clinician(client)

    response = client.get("/api/v1/patients/patient-1/thresholds")

    assert response.status_code == 200
    body = response.get_json()
    assert body["hr_min"] is None


def test_put_thresholds_updates_values(app, client):
    _seed_clinician_with_patient(app)
    _login_clinician(client)

    response = client.put("/api/v1/patients/patient-1/thresholds", json={"hr_min": 60, "hr_max": 100})

    assert response.status_code == 200
    body = response.get_json()
    assert body["hr_min"] == 60
    assert body["hr_max"] == 100
    assert body["updated_by"] is not None

    with app.app_context():
        threshold = db.session.get(Threshold, "patient-1")
        assert threshold.hr_min == 60


def test_put_thresholds_as_patient_returns_403(app, client):
    _seed_clinician_with_patient(app)
    create_user(app, "pasien2@example.com", "password123", role="pasien")
    login_as(client, "pasien2@example.com", "password123")

    response = client.put("/api/v1/patients/patient-1/thresholds", json={"hr_min": 60})

    assert response.status_code == 403


def test_device_status_returns_data(app, client):
    _seed_clinician_with_patient(app)
    _login_clinician(client)

    response = client.get("/api/v1/devices/pneumacare-a1b2/status")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status"] == "online"
    assert body["battery_percent"] == 80


def test_device_status_not_found(app, client):
    _seed_clinician_with_patient(app)
    _login_clinician(client)

    response = client.get("/api/v1/devices/does-not-exist/status")

    assert response.status_code == 404


def test_get_and_update_clinician_profile(app, client):
    _seed_clinician_with_patient(app)
    _login_clinician(client)

    get_response = client.get("/api/v1/clinician/profile")
    assert get_response.status_code == 200
    assert get_response.get_json()["email"] == "dr@example.com"

    put_response = client.put("/api/v1/clinician/profile", json={"institution": "RS Contoh"})
    assert put_response.status_code == 200
    assert put_response.get_json()["institution"] == "RS Contoh"
