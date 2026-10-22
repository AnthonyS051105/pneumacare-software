from datetime import datetime, timedelta, timezone

from backend.models import db
from backend.models.alert import Alert
from backend.models.device import Device
from backend.models.patient import Patient
from backend.models.classification import ReadingClassification
from backend.models.threshold import Threshold
from backend.models.trend import TrendEvent
from backend.models.user import User
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
            ReadingClassification(
                id="seg-1",
                device_id="pneumacare-a1b2",
                channel_id=1,
                segment_start=datetime.now(timezone.utc),
                segment_end=datetime.now(timezone.utc),
                wheeze_crackle_class="wheeze",
                wheeze_crackle_confidence=0.8,
                wheeze_crackle_probabilities={"none": 0.1, "crackle": 0.05, "wheeze": 0.8, "both": 0.05},
                wheeze_crackle_model_version="mock_v2",
            )
        )
        db.session.commit()
    _login_clinician(client)

    response = client.get("/api/v1/patients/patient-1/severity/latest")

    assert response.status_code == 200
    assert response.get_json()["wheeze_crackle_class"] == "wheeze"


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


def _now_naive() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _add_alert(app, level: int, acknowledged: bool, hours_ago: float = 1, patient_id: str = "patient-1") -> str:
    with app.app_context():
        alert = Alert(
            device_id="pneumacare-a1b2",
            patient_id=patient_id,
            level=level,
            triggers=[{"type": "vital_threshold", "parameter": "spo2", "value": 90, "threshold": 92, "severity": "breach"}],
            created_at=_now_naive() - timedelta(hours=hours_ago),
            acknowledged=acknowledged,
        )
        db.session.add(alert)
        db.session.commit()
        return alert.id


def test_list_patients_includes_vitals_device_and_open_alert_level(app, client):
    _seed_clinician_with_patient(app)
    with app.app_context():
        db.session.add(ReadingVital(device_id="pneumacare-a1b2", timestamp=_now_naive(), hr=80, spo2=95, rr=18))
        db.session.commit()
    _add_alert(app, level=3, acknowledged=True, hours_ago=5)
    _add_alert(app, level=2, acknowledged=False, hours_ago=1)
    _login_clinician(client)

    row = client.get("/api/v1/patients").get_json()[0]

    assert row["latest_vitals"]["hr"] == 80
    assert row["device"]["device_id"] == "pneumacare-a1b2"
    # Alert level 3 sudah ditinjau -> status mengikuti alert terbuka (level 2), bukan 3.
    assert row["open_alert_level"] == 2
    assert row["latest_alert_level"] == 3


def test_list_patients_sorted_by_open_alert_level(app, client):
    clinician_id, _ = _seed_clinician_with_patient(app)
    with app.app_context():
        db.session.add(Patient(id="patient-2", name="Aaa Tanpa Alert", assigned_clinician_id=clinician_id))
        db.session.commit()
    _add_alert(app, level=3, acknowledged=False)
    _login_clinician(client)

    ids = [r["id"] for r in client.get("/api/v1/patients").get_json()]

    assert ids == ["patient-1", "patient-2"]


def test_get_patient_detail_and_unowned_404(app, client):
    _seed_clinician_with_patient(app)
    other = create_user(app, "dr2@example.com", "password123", role="clinician")
    with app.app_context():
        db.session.add(Patient(id="patient-x", name="Milik Lain", assigned_clinician_id=other))
        db.session.commit()
    _login_clinician(client)

    assert client.get("/api/v1/patients/patient-1").get_json()["name"] == "Test Pasien"
    assert client.get("/api/v1/patients/patient-x").status_code == 404


def _seed_patient_account(app, email: str, assigned_to: str | None = None) -> str:
    user_id = create_user(app, email, "password123", role="pasien")
    with app.app_context():
        patient = Patient(name="Pasien Akun", user_id=user_id, assigned_clinician_id=assigned_to)
        db.session.add(patient)
        db.session.commit()
        return patient.id


def test_add_patient_by_email(app, client):
    _seed_clinician_with_patient(app)
    _seed_patient_account(app, "baru@example.com")
    _login_clinician(client)

    response = client.post("/api/v1/patients", json={"email": " Baru@Example.com "})

    assert response.status_code == 201
    assert response.get_json()["email"] == "baru@example.com"


def test_add_patient_already_assigned_to_other_clinician_returns_409(app, client):
    _seed_clinician_with_patient(app)
    other = create_user(app, "dr2@example.com", "password123", role="clinician")
    patient_id = _seed_patient_account(app, "milik-lain@example.com", assigned_to=other)
    _login_clinician(client)

    response = client.post("/api/v1/patients", json={"email": "milik-lain@example.com"})

    assert response.status_code == 409
    with app.app_context():
        assert db.session.get(Patient, patient_id).assigned_clinician_id == other


def test_add_patient_twice_returns_409(app, client):
    clinician_id, _ = _seed_clinician_with_patient(app)
    _seed_patient_account(app, "sendiri@example.com", assigned_to=clinician_id)
    _login_clinician(client)

    assert client.post("/api/v1/patients", json={"email": "sendiri@example.com"}).status_code == 409


def test_add_patient_unknown_email_returns_404(app, client):
    _seed_clinician_with_patient(app)
    _login_clinician(client)

    assert client.post("/api/v1/patients", json={"email": "tidak-ada@example.com"}).status_code == 404


def test_vitals_history_accepts_utc_z_and_rejects_garbage(app, client):
    _seed_clinician_with_patient(app)
    with app.app_context():
        now = _now_naive()
        db.session.add(ReadingVital(device_id="pneumacare-a1b2", timestamp=now - timedelta(hours=2), hr=70))
        db.session.add(ReadingVital(device_id="pneumacare-a1b2", timestamp=now - timedelta(hours=30), hr=71))
        db.session.commit()
    _login_clinician(client)
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")

    body = client.get(f"/api/v1/patients/patient-1/vitals/history?from={since}").get_json()

    assert [r["hr"] for r in body] == [70]
    assert client.get("/api/v1/patients/patient-1/vitals/history?from=kemarin").status_code == 400


def test_alert_filters_reject_invalid_level(app, client):
    _seed_clinician_with_patient(app)
    _login_clinician(client)

    assert client.get("/api/v1/clinician/alerts?level=abc").status_code == 400
    assert client.get("/api/v1/patients/patient-1/alerts?level=9").status_code == 400


def test_clinician_alerts_include_patient_name_and_date_filter(app, client):
    _seed_clinician_with_patient(app)
    _add_alert(app, level=2, acknowledged=False, hours_ago=1)
    _add_alert(app, level=2, acknowledged=False, hours_ago=50)
    _login_clinician(client)
    since = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    body = client.get("/api/v1/clinician/alerts", query_string={"from": since}).get_json()

    assert len(body) == 1
    assert body[0]["patient_name"] == "Test Pasien"


def test_wheeze_crackle_history_buckets(app, client):
    _seed_clinician_with_patient(app)
    with app.app_context():
        end = _now_naive() - timedelta(minutes=30)
        for i, cls in enumerate(["wheeze", "none", "crackle", "none"]):
            db.session.add(
                ReadingClassification(
                    id=f"seg-{i}",
                    device_id="pneumacare-a1b2",
                    channel_id=1,
                    segment_start=end - timedelta(seconds=5),
                    segment_end=end + timedelta(seconds=i),
                    wheeze_crackle_class=cls,
                    wheeze_crackle_confidence=0.8,
                    wheeze_crackle_model_version="test",
                )
            )
        db.session.commit()
    _login_clinician(client)

    body = client.get("/api/v1/patients/patient-1/wheeze-crackle/history?range=24h").get_json()

    assert body["bucket_seconds"] == 3600
    assert len(body["buckets"]) == 24
    assert sum(b["total"] for b in body["buckets"]) == 4
    filled = [b for b in body["buckets"] if b["total"]]
    assert filled[-1]["abnormal_ratio"] == 0.5
    assert client.get("/api/v1/patients/patient-1/wheeze-crackle/history?range=1y").status_code == 400


def test_put_thresholds_validation(app, client):
    _seed_clinician_with_patient(app)
    _login_clinician(client)
    url = "/api/v1/patients/patient-1/thresholds"

    assert client.put(url, json={"hr_min": 100, "hr_max": 60}).status_code == 400
    assert client.put(url, json={"spo2_min": 120}).status_code == 400
    assert client.put(url, json={"rr_min": -1}).status_code == 400
    assert client.put(url, json={"hr_min": "60"}).status_code == 400
    # Update parsial tetap divalidasi terhadap nilai tersimpan.
    assert client.put(url, json={"hr_min": 50, "hr_max": 110}).status_code == 200
    assert client.put(url, json={"hr_max": 40}).status_code == 400
    assert client.get(url).get_json()["hr_max"] == 110


def test_put_thresholds_saves_action_plan(app, client):
    _seed_clinician_with_patient(app)
    _login_clinician(client)
    url = "/api/v1/patients/patient-1/thresholds"

    response = client.put(url, json={"action_plan": "  Hubungi klinik bila sesak.  "})

    assert response.status_code == 200
    assert client.get(url).get_json()["action_plan"] == "Hubungi klinik bila sesak."
    assert client.put(url, json={"action_plan": 5}).status_code == 400


def test_device_status_of_unowned_device_returns_404(app, client):
    _seed_clinician_with_patient(app)
    create_user(app, "dr2@example.com", "password123", role="clinician")
    login_as(client, "dr2@example.com", "password123")

    assert client.get("/api/v1/devices/pneumacare-a1b2/status").status_code == 404


def test_acknowledge_alert_of_unowned_patient_returns_404(app, client):
    _seed_clinician_with_patient(app)
    alert_id = _add_alert(app, level=2, acknowledged=False)
    create_user(app, "dr2@example.com", "password123", role="clinician")
    login_as(client, "dr2@example.com", "password123")

    assert client.post(f"/api/v1/alerts/{alert_id}/acknowledge").status_code == 404
    with app.app_context():
        assert db.session.get(Alert, alert_id).acknowledged is False


def test_acknowledge_own_alert(app, client):
    _seed_clinician_with_patient(app)
    alert_id = _add_alert(app, level=2, acknowledged=False)
    _login_clinician(client)

    assert client.post(f"/api/v1/alerts/{alert_id}/acknowledge").status_code == 200
    assert client.post(f"/api/v1/alerts/{alert_id}/acknowledge").status_code == 409


def test_clinician_profile_password_change(app, client):
    _seed_clinician_with_patient(app)
    _login_clinician(client)
    url = "/api/v1/clinician/profile"

    assert client.put(url, json={"current_password": "salah", "new_password": "newpass123"}).status_code == 400
    assert client.put(url, json={"current_password": "password123", "new_password": "short"}).status_code == 400
    assert client.put(url, json={"current_password": "password123", "new_password": "newpass123"}).status_code == 200
    client.post("/api/v1/auth/logout")
    assert login_as(client, "dr@example.com", "newpass123").status_code == 200


def test_clinician_profile_rejects_empty_name(app, client):
    _seed_clinician_with_patient(app)
    _login_clinician(client)

    assert client.put("/api/v1/clinician/profile", json={"full_name": "  "}).status_code == 400
