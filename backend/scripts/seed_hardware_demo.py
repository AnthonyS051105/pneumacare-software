"""TEMPORARY_DEV_AUTH — skrip demo untuk menautkan device_id hardware ASLI
(bukan device dummy seed_dev_patient.py) ke akun pasien + clinician test,
supaya data dari board ESP32 sungguhan langsung muncul di dashboard clinician
saat demo 50%.

Idempotent — aman dijalankan berkali-kali (skip kalau data sudah ada).

Cara pakai (dari folder software/ root, backend TIDAK perlu sedang berjalan):
    source backend/venv/bin/activate
    python -m backend.scripts.seed_hardware_demo

Kredensial dev yang dibuat:
    clinician — email: dev-clinician@example.com   password: devpassword123
    pasien    — email: dev-patient-hw@example.com  password: devpassword123

WAJIB DIHAPUS begitu alur pairing_code asli (patient_routes.py /device/repair)
dipakai sebagai jalur satu-satunya untuk demo/submit final.
"""

from werkzeug.security import generate_password_hash

from backend.app import create_app
from backend.models import db
from backend.models.device import Device
from backend.models.patient import Patient
from backend.models.user import User

# Harus SAMA PERSIS dengan DEVICE_ID di hardware/include/config.h
HARDWARE_DEVICE_ID = "pneumacare-a1b2"

CLINICIAN_EMAIL = "dev-clinician@example.com"
PATIENT_EMAIL = "dev-patient-hw@example.com"
DEV_PASSWORD = "devpassword123"


def _get_or_create_user(email: str, role: str, full_name: str) -> User:
    user = db.session.query(User).filter_by(email=email).first()
    if user is None:
        user = User(
            email=email,
            password_hash=generate_password_hash(DEV_PASSWORD),
            role=role,
            full_name=full_name,
        )
        db.session.add(user)
        db.session.flush()
        print(f"User dibuat: {email} (role={role})")
    else:
        print(f"User sudah ada: {email}")
    return user


def seed() -> None:
    app = create_app(start_mqtt=False)
    with app.app_context():
        clinician = _get_or_create_user(CLINICIAN_EMAIL, "clinician", "Dev Test Clinician")
        patient_user = _get_or_create_user(PATIENT_EMAIL, "pasien", "Dev Test Pasien Hardware")

        patient = db.session.query(Patient).filter_by(user_id=patient_user.id).first()
        if patient is None:
            patient = Patient(
                user_id=patient_user.id,
                name=patient_user.full_name,
                assigned_clinician_id=clinician.id,
            )
            db.session.add(patient)
            db.session.flush()
            print(f"Patient dibuat: {patient.id}")
        elif patient.assigned_clinician_id != clinician.id:
            patient.assigned_clinician_id = clinician.id
            print(f"Patient {patient.id} ditautkan ulang ke clinician {clinician.id}")
        else:
            print(f"Patient sudah ada & tertaut ke clinician: {patient.id}")

        device = db.session.get(Device, HARDWARE_DEVICE_ID)
        if device is None:
            device = Device(device_id=HARDWARE_DEVICE_ID, status="offline", patient_id=patient.id)
            db.session.add(device)
            print(f"Device dibuat: {HARDWARE_DEVICE_ID}")
        elif device.patient_id != patient.id:
            device.patient_id = patient.id
            print(f"Device {HARDWARE_DEVICE_ID} ditautkan ulang ke patient {patient.id}")
        else:
            print(f"Device sudah ada & tertaut: {HARDWARE_DEVICE_ID}")

        db.session.commit()

    print("\nSelesai. Login untuk demo:")
    print(f"  Clinician — email: {CLINICIAN_EMAIL}  password: {DEV_PASSWORD}")
    print(f"  Pasien    — email: {PATIENT_EMAIL}  password: {DEV_PASSWORD}")
    print(f"  Device ID: {HARDWARE_DEVICE_ID} (harus sama dengan DEVICE_ID di hardware/include/config.h)")


if __name__ == "__main__":
    seed()
