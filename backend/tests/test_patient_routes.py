from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from backend.models import db
from backend.models.alert import Alert
from backend.models.classification import ReadingClassification
from backend.models.device import Device, DevicePairingCode, DeviceStatusLog
from backend.models.patient import Patient
from backend.models.user import User
from backend.models.vital import ReadingVital
from backend.tests.conftest import create_user, login_as


def _seed_patient_with_device(app) -> str:
    """Return patient user id."""
    with app.app_context():
        user = User(
            email="pasien@example.com",
            password_hash=generate_password_hash("password123"),
            role="pasien",
            full_name="Pasien Test",
        )
        db.session.add(user)
        db.session.flush()

        device = Device(device_id="pneumacare-a1b2", status="online")
        patient = Patient(id="patient-1", user_id=user.id, name="Pasien Test")
        device.patient_id = patient.id
        db.session.add_all([device, patient])
        db.session.commit()
        return user.id


def _login_patient(client):
    return login_as(client, "pasien@example.com", "password123")


def test_summary_requires_login(client):
    response = client.get("/api/v1/patient/me/summary")
    assert response.status_code == 401


def test_summary_returns_own_data(app, client):
    _seed_patient_with_device(app)
    with app.app_context():
        db.session.add(
            ReadingVital(device_id="pneumacare-a1b2", timestamp=datetime.now(timezone.utc), hr=75, spo2=97, rr=16)
        )
        db.session.commit()
    _login_patient(client)

    response = client.get("/api/v1/patient/me/summary")

    assert response.status_code == 200
    body = response.get_json()
    assert body["status_label"] == "stable"
    assert body["device_connected"] is True
    assert body["latest_vitals"]["hr"] == 75
    assert body["today_range"]["hr"] == {"min": 75, "max": 75}
    assert body["wear_compliance_today_hours"] is not None
    assert body["patient_id"] == "patient-1"
    assert body["latest_classification"] is None


def test_summary_includes_latest_classification(app, client):
    _seed_patient_with_device(app)
    with app.app_context():
        now = datetime.now(timezone.utc)
        db.session.add(
            ReadingClassification(
                id="segment-1",
                device_id="pneumacare-a1b2",
                channel_id=1,
                segment_start=now - timedelta(seconds=5),
                segment_end=now,
                wheeze_crackle_class="wheeze",
                wheeze_crackle_confidence=0.87,
                wheeze_crackle_probabilities=[0.05, 0.03, 0.87, 0.05],
                wheeze_crackle_model_version="mobilenet_v3_small_epoch05_valloss0.9021",
            )
        )
        db.session.commit()
    _login_patient(client)

    response = client.get("/api/v1/patient/me/summary")

    assert response.status_code == 200
    body = response.get_json()
    assert body["latest_classification"]["predicted_class"] == "wheeze"
    assert body["latest_classification"]["confidence"] == 0.87


def test_summary_as_clinician_returns_403(app, client):
    _seed_patient_with_device(app)
    create_user(app, "dr@example.com", "password123", role="clinician")
    login_as(client, "dr@example.com", "password123")

    response = client.get("/api/v1/patient/me/summary")

    assert response.status_code == 403


def test_history_default_range(app, client):
    _seed_patient_with_device(app)
    with app.app_context():
        db.session.add(
            ReadingVital(device_id="pneumacare-a1b2", timestamp=datetime.now(timezone.utc), hr=80, spo2=96, rr=18)
        )
        db.session.commit()
    _login_patient(client)

    response = client.get("/api/v1/patient/me/history")

    assert response.status_code == 200
    body = response.get_json()
    assert len(body["readings"]) == 1
    assert body["stats"]["hr"]["current"] == 80
    assert "wear_compliance_by_day" in body


def test_history_invalid_range_returns_400(app, client):
    _seed_patient_with_device(app)
    _login_patient(client)

    response = client.get("/api/v1/patient/me/history?range=invalid")

    assert response.status_code == 400


def test_alerts_returns_plain_language(app, client):
    _seed_patient_with_device(app)
    with app.app_context():
        db.session.add(
            Alert(
                id="alert-1",
                device_id="pneumacare-a1b2",
                patient_id="patient-1",
                level=2,
                triggers=[{"type": "vital_threshold", "parameter": "spo2", "value": 91, "threshold": 92, "severity": "breach"}],
                created_at=datetime.now(timezone.utc),
            )
        )
        db.session.commit()
    _login_patient(client)

    response = client.get("/api/v1/patient/me/alerts")

    assert response.status_code == 200
    body = response.get_json()
    assert len(body) == 1
    assert body[0]["level_label"] == "Perlu Diperhatikan"
    assert "messages" in body[0]
    assert "triggers" not in body[0]  # tidak boleh bocorkan trigger teknis mentah ke pasien


def test_get_profile(app, client):
    _seed_patient_with_device(app)
    _login_patient(client)

    response = client.get("/api/v1/patient/me/profile")

    assert response.status_code == 200
    body = response.get_json()
    assert body["email"] == "pasien@example.com"
    assert body["device_paired"] is True


def test_update_profile_full_name(app, client):
    _seed_patient_with_device(app)
    _login_patient(client)

    response = client.put("/api/v1/patient/me/profile", json={"full_name": "Nama Baru"})

    assert response.status_code == 200
    with app.app_context():
        patient = db.session.get(Patient, "patient-1")
        assert patient.name == "Nama Baru"


def test_update_profile_wrong_current_password_returns_400(app, client):
    _seed_patient_with_device(app)
    _login_patient(client)

    response = client.put(
        "/api/v1/patient/me/profile",
        json={"new_password": "newpass123", "current_password": "wrong"},
    )

    assert response.status_code == 400


def test_update_profile_password_success(app, client):
    _seed_patient_with_device(app)
    _login_patient(client)

    response = client.put(
        "/api/v1/patient/me/profile",
        json={"new_password": "newpass123", "current_password": "password123"},
    )

    assert response.status_code == 200


def test_device_repair_with_valid_code(app, client):
    _seed_patient_with_device(app)
    with app.app_context():
        new_device = Device(device_id="pneumacare-c3d4", status="offline")
        db.session.add(new_device)
        db.session.add(DevicePairingCode(device_id="pneumacare-c3d4", pairing_code="NEWCODE"))
        db.session.commit()
    _login_patient(client)

    response = client.post("/api/v1/patient/me/device/repair", json={"pairing_code": "NEWCODE"})

    assert response.status_code == 200
    with app.app_context():
        device = db.session.get(Device, "pneumacare-c3d4")
        assert device.patient_id == "patient-1"


def test_device_repair_invalid_code_returns_404(app, client):
    _seed_patient_with_device(app)
    _login_patient(client)

    response = client.post("/api/v1/patient/me/device/repair", json={"pairing_code": "NOPE"})

    assert response.status_code == 404


def test_patient_cannot_access_clinician_only_endpoint(app, client):
    _seed_patient_with_device(app)
    _login_patient(client)

    response = client.get("/api/v1/patients")

    assert response.status_code == 403


def test_summary_wear_compliance_reflects_status_log(app, client):
    _seed_patient_with_device(app)
    with app.app_context():
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        db.session.add(
            DeviceStatusLog(device_id="pneumacare-a1b2", status="online", changed_at=today_start + timedelta(hours=2))
        )
        db.session.add(
            DeviceStatusLog(device_id="pneumacare-a1b2", status="offline", changed_at=today_start + timedelta(hours=6))
        )
        db.session.commit()
    _login_patient(client)

    response = client.get("/api/v1/patient/me/summary")

    assert response.status_code == 200
    assert response.get_json()["wear_compliance_today_hours"] == 4.0


def test_history_wear_compliance_by_day_and_pattern_insight(app, client):
    _seed_patient_with_device(app)
    with app.app_context():
        now = datetime.now(timezone.utc)
        for hour, hr in [(8, 70), (9, 71), (20, 60), (21, 90)]:
            db.session.add(
                ReadingVital(
                    device_id="pneumacare-a1b2",
                    timestamp=now.replace(hour=hour, minute=0, second=0, microsecond=0),
                    hr=hr,
                    spo2=97,
                    rr=16,
                )
            )
        db.session.commit()
    _login_patient(client)

    response = client.get("/api/v1/patient/me/history?range=24h")

    assert response.status_code == 200
    body = response.get_json()
    assert len(body["wear_compliance_by_day"]) == 1
    assert body["pattern_insight"] is not None
