"""Auth & Onboarding — signup (dual-role), login, logout (SDD_SOFTWARE.md §4.1,
FR-SW-056, FR-SW-061..064). Session-based via flask-login (bukan JWT) — lihat
alasan pemilihan di ringkasan sesi Fase 4.
"""

from flask import Blueprint, jsonify, request
from flask_login import login_required, login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from backend.models import db
from backend.models.device import Device, DevicePairingCode
from backend.models.patient import Patient
from backend.models.user import User

auth_bp = Blueprint("auth", __name__, url_prefix="/api/v1/auth")

VALID_ROLES = ("pasien", "clinician")


def _user_public_dict(user: User) -> dict:
    return {"id": user.id, "email": user.email, "role": user.role, "full_name": user.full_name}


@auth_bp.post("/signup")
def signup():
    body = request.get_json(silent=True) or {}

    role = body.get("role")
    email = body.get("email")
    password = body.get("password")
    full_name = body.get("full_name")

    if role not in VALID_ROLES:
        return jsonify({"error": f"role harus salah satu dari {VALID_ROLES}"}), 400
    if not email or not password or not full_name:
        return jsonify({"error": "email, password, dan full_name wajib diisi"}), 400

    if db.session.query(User).filter_by(email=email).first() is not None:
        return jsonify({"error": "email sudah terdaftar"}), 409

    # FR-SW-062: signup role pasien WAJIB validasi pairing_code sebelum akun dibuat.
    pairing = None
    if role == "pasien":
        pairing_code = body.get("pairing_code")
        if not pairing_code:
            return jsonify({"error": "pairing_code wajib untuk signup role pasien"}), 400

        pairing = db.session.query(DevicePairingCode).filter_by(pairing_code=pairing_code).first()
        if pairing is None:
            return jsonify({"error": "pairing_code tidak ditemukan"}), 404
        if pairing.used:
            return jsonify({"error": "pairing_code sudah dipakai"}), 409

    user = User(
        email=email,
        password_hash=generate_password_hash(password),  # NFR-SW-008: password ter-hash
        role=role,
        full_name=full_name,
        # FR-SW-064: str_sip_number/specialization/institution murni informasi bebas untuk
        # role clinician, tidak diverifikasi ke sistem eksternal manapun.
        specialization=body.get("specialization") if role == "clinician" else None,
        institution=body.get("institution") if role == "clinician" else None,
        str_sip_number=body.get("str_sip_number") if role == "clinician" else None,
    )
    db.session.add(user)
    db.session.flush()  # supaya user.id terisi sebelum dipakai Patient/pairing di bawah

    if role == "pasien":
        patient = Patient(user_id=user.id, name=full_name)
        db.session.add(patient)
        db.session.flush()

        pairing.used = True
        pairing.used_by_patient_id = patient.id
        device = db.session.get(Device, pairing.device_id)
        if device is not None:
            device.patient_id = patient.id

    db.session.commit()

    # FR-SW-063: auto-login setelah signup berhasil.
    login_user(user)

    return jsonify(_user_public_dict(user)), 201


@auth_bp.post("/login")
def login():
    body = request.get_json(silent=True) or {}
    email = body.get("email")
    password = body.get("password")

    if not email or not password:
        return jsonify({"error": "email dan password wajib diisi"}), 400

    user = db.session.query(User).filter_by(email=email).first()
    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "email atau password salah"}), 401

    login_user(user)
    return jsonify(_user_public_dict(user))


@auth_bp.post("/logout")
@login_required
def logout():
    logout_user()
    return jsonify({"status": "ok"})
