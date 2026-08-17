"""Decorator otorisasi berbasis role — NFR-SW-007, FR-SW-059, FR-SW-070.

Otorisasi role HARUS ditegakkan di layer backend (bukan hanya disembunyikan di
frontend) — role yang tidak sesuai mendapat HTTP 403, bukan sekadar UI yang
disembunyikan.
"""

from functools import wraps

from flask import jsonify
from flask_login import current_user


def role_required(*allowed_roles: str):
    """Wajibkan `current_user` login DAN role-nya salah satu dari `allowed_roles`.

    401 bila belum login (flask-login `login_required` semantics), 403 bila login
    tapi role tidak diizinkan — dua kode status berbeda supaya frontend/test bisa
    membedakan "belum login" vs "login tapi tidak berwenang".
    """

    def decorator(view_func):
        @wraps(view_func)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "belum login"}), 401
            if current_user.role not in allowed_roles:
                return jsonify({"error": "tidak berwenang untuk aksi ini"}), 403
            return view_func(*args, **kwargs)

        return wrapped

    return decorator
