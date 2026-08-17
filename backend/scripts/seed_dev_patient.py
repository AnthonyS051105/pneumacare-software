"""TEMPORARY_DEV_AUTH — skrip development untuk menyiapkan akun pasien test +
device + beberapa baris readings_vital, supaya halaman dev-login frontend
(src/app/patient/dev-login/) bisa langsung dipakai tanpa isi form signup manual.

Idempotent — aman dijalankan berkali-kali (skip kalau data sudah ada).

Cara pakai (dari folder software/ root — BUKAN dari backend/, beda dengan
simulate_esp32.py — karena skrip ini import langsung backend.app/backend.models,
bukan cuma jadi client eksternal seperti simulator ESP32):
    source backend/venv/bin/activate
    python -m backend.scripts.seed_dev_patient
Backend TIDAK perlu sedang berjalan saat skrip ini dieksekusi.

Kredensial dev yang dibuat:
    email:    dev-patient@example.com
    password: devpassword123

WAJIB DIHAPUS begitu halaman Login asli sudah ada dan dev-login tidak lagi
diperlukan untuk testing.
"""

from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from backend.app import create_app
from backend.models import db
from backend.models.device import Device, DeviceStatusLog
from backend.models.patient import Patient
from backend.models.user import User
from backend.models.vital import ReadingVital

DEV_EMAIL = "dev-patient@example.com"
DEV_PASSWORD = "devpassword123"
DEV_DEVICE_ID = "pneumacare-dev1"


def seed() -> None:
    app = create_app(start_mqtt=False)
    with app.app_context():
        user = db.session.query(User).filter_by(email=DEV_EMAIL).first()
        if user is None:
            user = User(
                email=DEV_EMAIL,
                password_hash=generate_password_hash(DEV_PASSWORD),
                role="pasien",
                full_name="Dev Test Pasien",
            )
            db.session.add(user)
            db.session.flush()
            print(f"User dibuat: {DEV_EMAIL}")
        else:
            print(f"User sudah ada: {DEV_EMAIL}")

        patient = db.session.query(Patient).filter_by(user_id=user.id).first()
        if patient is None:
            patient = Patient(user_id=user.id, name=user.full_name)
            db.session.add(patient)
            db.session.flush()
            print(f"Patient dibuat: {patient.id}")
        else:
            print(f"Patient sudah ada: {patient.id}")

        device = db.session.get(Device, DEV_DEVICE_ID)
        if device is None:
            device = Device(device_id=DEV_DEVICE_ID, status="online", battery_percent=85, patient_id=patient.id)
            db.session.add(device)
            db.session.add(
                DeviceStatusLog(device_id=DEV_DEVICE_ID, status="online", changed_at=datetime.now(timezone.utc))
            )
            print(f"Device dibuat: {DEV_DEVICE_ID}")
        elif device.patient_id != patient.id:
            device.patient_id = patient.id
            print(f"Device {DEV_DEVICE_ID} ditautkan ulang ke patient {patient.id}")
        else:
            print(f"Device sudah ada & tertaut: {DEV_DEVICE_ID}")

        existing_readings = db.session.query(ReadingVital).filter_by(device_id=DEV_DEVICE_ID).count()
        if existing_readings == 0:
            now = datetime.now(timezone.utc)
            for hours_ago in range(48, 0, -2):
                db.session.add(
                    ReadingVital(
                        device_id=DEV_DEVICE_ID,
                        timestamp=now - timedelta(hours=hours_ago),
                        hr=70 + (hours_ago % 10),
                        spo2=96 + (hours_ago % 3) * 0.5,
                        rr=15 + (hours_ago % 4) * 0.3,
                    )
                )
            print("Readings vital dummy dibuat (48 jam terakhir, tiap 2 jam)")
        else:
            print(f"Readings vital sudah ada ({existing_readings} baris), skip seed")

        db.session.commit()

    print("\nSelesai. Login dev via halaman /patient/dev-login dengan:")
    print(f"  email:    {DEV_EMAIL}")
    print(f"  password: {DEV_PASSWORD}")


if __name__ == "__main__":
    seed()
