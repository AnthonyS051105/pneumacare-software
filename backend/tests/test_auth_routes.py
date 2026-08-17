from backend.models import db
from backend.models.device import Device, DevicePairingCode
from backend.models.patient import Patient
from backend.models.user import User
from backend.tests.conftest import create_user, login_as


def _seed_pairing_code(app, code: str = "PAIR123") -> None:
    with app.app_context():
        device = Device(device_id="pneumacare-a1b2", status="offline")
        db.session.add(device)
        db.session.add(DevicePairingCode(device_id=device.device_id, pairing_code=code))
        db.session.commit()


def test_signup_clinician_success(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "role": "clinician",
            "email": "dr@example.com",
            "password": "password123",
            "full_name": "Dr. Test",
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["role"] == "clinician"
    assert body["email"] == "dr@example.com"


def test_signup_patient_requires_valid_pairing_code(app, client):
    _seed_pairing_code(app, "PAIR123")

    response = client.post(
        "/api/v1/auth/signup",
        json={
            "role": "pasien",
            "email": "pasien@example.com",
            "password": "password123",
            "full_name": "Pasien Test",
            "pairing_code": "PAIR123",
        },
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["role"] == "pasien"

    with app.app_context():
        pairing = db.session.query(DevicePairingCode).filter_by(pairing_code="PAIR123").first()
        assert pairing.used is True
        device = db.session.get(Device, "pneumacare-a1b2")
        assert device.patient_id is not None


def test_signup_patient_missing_pairing_code_returns_400(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "role": "pasien",
            "email": "pasien2@example.com",
            "password": "password123",
            "full_name": "Pasien Test",
        },
    )
    assert response.status_code == 400


def test_signup_patient_invalid_pairing_code_returns_404(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "role": "pasien",
            "email": "pasien3@example.com",
            "password": "password123",
            "full_name": "Pasien Test",
            "pairing_code": "DOES-NOT-EXIST",
        },
    )
    assert response.status_code == 404


def test_signup_patient_already_used_pairing_code_returns_409(app, client):
    _seed_pairing_code(app, "PAIR456")
    client.post(
        "/api/v1/auth/signup",
        json={
            "role": "pasien",
            "email": "first@example.com",
            "password": "password123",
            "full_name": "First Patient",
            "pairing_code": "PAIR456",
        },
    )
    response = client.post(
        "/api/v1/auth/signup",
        json={
            "role": "pasien",
            "email": "second@example.com",
            "password": "password123",
            "full_name": "Second Patient",
            "pairing_code": "PAIR456",
        },
    )
    assert response.status_code == 409


def test_signup_duplicate_email_returns_409(client):
    payload = {
        "role": "clinician",
        "email": "dup@example.com",
        "password": "password123",
        "full_name": "Dr. Dup",
    }
    client.post("/api/v1/auth/signup", json=payload)
    response = client.post("/api/v1/auth/signup", json=payload)
    assert response.status_code == 409


def test_signup_invalid_role_returns_400(client):
    response = client.post(
        "/api/v1/auth/signup",
        json={"role": "admin", "email": "x@example.com", "password": "password123", "full_name": "X"},
    )
    assert response.status_code == 400


def test_signup_auto_login(client):
    client.post(
        "/api/v1/auth/signup",
        json={
            "role": "clinician",
            "email": "autologin@example.com",
            "password": "password123",
            "full_name": "Dr. Auto",
        },
    )
    # FR-SW-063: auto-login, panggilan endpoint terproteksi berikutnya harus sukses tanpa login manual
    response = client.get("/api/v1/clinician/profile")
    assert response.status_code == 200


def test_login_success(app, client):
    create_user(app, "login@example.com", "password123", role="clinician")

    response = login_as(client, "login@example.com", "password123")

    assert response.status_code == 200
    assert response.get_json()["email"] == "login@example.com"


def test_login_wrong_password_returns_401(app, client):
    create_user(app, "login2@example.com", "password123", role="clinician")

    response = login_as(client, "login2@example.com", "wrong-password")

    assert response.status_code == 401


def test_login_nonexistent_email_returns_401(client):
    response = login_as(client, "nobody@example.com", "password123")
    assert response.status_code == 401


def test_logout_requires_login(client):
    response = client.post("/api/v1/auth/logout")
    assert response.status_code == 401


def test_logout_then_protected_endpoint_requires_login_again(app, client):
    create_user(app, "logout@example.com", "password123", role="clinician")
    login_as(client, "logout@example.com", "password123")

    logout_response = client.post("/api/v1/auth/logout")
    assert logout_response.status_code == 200

    response = client.get("/api/v1/clinician/profile")
    assert response.status_code == 401
