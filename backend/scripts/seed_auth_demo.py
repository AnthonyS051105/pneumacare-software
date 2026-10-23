"""Seed akun demo untuk halaman login/signup frontend (tombol "Demo pasien" /
"Demo tenaga medis" dan kode pairing contoh PC-4821).

Idempotent — aman dijalankan berkali-kali. Jalankan dari root software/:
    source backend/venv/bin/activate
    python -m backend.scripts.seed_auth_demo
Backend TIDAK perlu sedang berjalan.

Kredensial (password sama dengan DEMO_PASSWORD di src/lib/demo-data.ts):
    pasien    — budi@example.com   / Pneuma123!
    clinician — nadia@example.com  / Pneuma123!
Kode pairing belum terpakai: PC-4821 (untuk uji signup pasien).

Opsi `--sample-data`: isi akun Budi dengan perangkat demo, bacaan vital 48 jam (dengan satu
jeda data) dan 3 alert contoh, supaya portal pasien tidak kosong saat demo/uji UI. DATA INI
SIMULASI — bukan hasil pengukuran, jangan dipakai untuk klaim apapun. Aman dijalankan ulang
(bacaan dan alert contoh dibuat ulang agar tetap "segar" relatif terhadap jam sekarang).
"""

import argparse
import math
from datetime import datetime, timedelta, timezone

from werkzeug.security import generate_password_hash

from backend.app import create_app
from backend.models import db
from backend.models.alert import Alert
from backend.models.device import Device, DevicePairingCode, DeviceStatusLog
from backend.models.patient import Patient
from backend.models.user import User
from backend.models.vital import ReadingVital

DEMO_PASSWORD = "Pneuma123!"
PAIRING_DEVICE_ID = "pneumacare-demo-pair"
PAIRING_CODE = "PC-4821"
SAMPLE_DEVICE_ID = "pneumacare-demo-01"


def _get_or_create_user(email: str, role: str, full_name: str) -> User:
    user = db.session.query(User).filter_by(email=email).first()
    if user is None:
        user = User(
            email=email,
            password_hash=generate_password_hash(DEMO_PASSWORD),
            role=role,
            full_name=full_name,
        )
        db.session.add(user)
        db.session.flush()
        print(f"User dibuat: {email} (role={role})")
    else:
        print(f"User sudah ada: {email}")
    return user


def seed_sample_data(patient: Patient) -> None:
    """Perangkat + bacaan vital simulasi + alert contoh untuk satu pasien."""
    now = datetime.now(timezone.utc).replace(tzinfo=None, second=0, microsecond=0)
    device = db.session.get(Device, SAMPLE_DEVICE_ID)
    if device is None:
        device = Device(device_id=SAMPLE_DEVICE_ID)
        db.session.add(device)
    device.patient_id = patient.id
    device.status = "online"
    device.battery_percent = 78
    device.last_seen_at = now
    device.signal_quality_ppg = "good"
    db.session.flush()

    db.session.query(ReadingVital).filter_by(device_id=SAMPLE_DEVICE_ID).delete()
    db.session.query(Alert).filter_by(device_id=SAMPLE_DEVICE_ID).delete()
    db.session.query(DeviceStatusLog).filter_by(device_id=SAMPLE_DEVICE_ID).delete()

    # Satu bacaan tiap 5 menit selama 48 jam; jeda 3 jam (rompi dilepas) sekitar 9-6 jam lalu.
    for step in range(48 * 12):
        ts = now - timedelta(minutes=5 * step)
        hours_ago = step / 12
        if 6 <= hours_ago < 9:
            continue
        wave = math.sin(step / 9)
        db.session.add(
            ReadingVital(
                device_id=SAMPLE_DEVICE_ID,
                timestamp=ts,
                hr=round(78 + 4 * wave, 1),
                spo2=round(96 + 1 * math.sin(step / 13), 1),
                rr=round(18 + 1.5 * math.sin(step / 7), 1),
            )
        )

    db.session.add(DeviceStatusLog(device_id=SAMPLE_DEVICE_ID, status="online", changed_at=now - timedelta(hours=48)))
    db.session.add(DeviceStatusLog(device_id=SAMPLE_DEVICE_ID, status="offline", changed_at=now - timedelta(hours=9)))
    db.session.add(DeviceStatusLog(device_id=SAMPLE_DEVICE_ID, status="online", changed_at=now - timedelta(hours=6)))

    # Bentuk trigger mengikuti contoh INTEGRATION_CONTRACT.md §5 apa adanya — termasuk penanda
    # ambang yang belum final — supaya data contoh tidak memuat angka ambang klinis karangan.
    for hours_ago, level, triggers, ack in [
        (3, 2, [{"type": "vital_threshold", "parameter": "spo2", "value": 91, "threshold": "TODO_CLINICAL_VALUE", "severity": "breach"}], False),
        (5.5, 1, [{"type": "vital_threshold", "parameter": "rr", "value": 22, "threshold": "TODO_CLINICAL_VALUE", "severity": "near"}], True),
        (30, 2, [{"type": "trend_slope", "parameter": "abnormal_frequency", "value": 0.14, "threshold": "TODO_NATHANAEL_CONFIRM"}], True),
    ]:
        db.session.add(
            Alert(
                device_id=SAMPLE_DEVICE_ID,
                patient_id=patient.id,
                level=level,
                triggers=triggers,
                created_at=now - timedelta(hours=hours_ago),
                acknowledged=ack,
            )
        )
    print(f"Data contoh dibuat untuk {patient.name} (perangkat {SAMPLE_DEVICE_ID})")


def seed(sample_data: bool = False) -> None:
    app = create_app(start_mqtt=False)
    with app.app_context():
        clinician = _get_or_create_user("nadia@example.com", "clinician", "dr. Nadia Putri")
        patient_user = _get_or_create_user("budi@example.com", "pasien", "Budi Santoso")

        patient = db.session.query(Patient).filter_by(user_id=patient_user.id).first()
        if patient is None:
            patient = Patient(user_id=patient_user.id, name=patient_user.full_name, assigned_clinician_id=clinician.id)
            db.session.add(patient)
            print("Patient dibuat: Budi Santoso")

        if db.session.get(Device, PAIRING_DEVICE_ID) is None:
            db.session.add(Device(device_id=PAIRING_DEVICE_ID, status="offline"))
            db.session.flush()
        if db.session.get(DevicePairingCode, PAIRING_DEVICE_ID) is None:
            db.session.add(DevicePairingCode(device_id=PAIRING_DEVICE_ID, pairing_code=PAIRING_CODE))
            print(f"Kode pairing dibuat: {PAIRING_CODE}")

        if sample_data:
            seed_sample_data(patient)

        db.session.commit()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--sample-data", action="store_true", help="isi akun Budi dengan data pemantauan simulasi")
    seed(sample_data=parser.parse_args().sample_data)
