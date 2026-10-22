import logging
import os

from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

from backend.api.clinician_routes import clinician_bp
from backend.api.patient_routes import patient_bp
from backend.api.routes import api_bp
from backend.auth.auth_routes import auth_bp
from backend.config import Config
from backend.inference.model_startup import load_model_a_or_none
from backend.ingestion.mqtt_subscriber import start_mqtt_subscriber
from backend.ingestion.websocket_server import register_websocket_routes
from backend.models import db
from backend.models.user import User

login_manager = LoginManager()


def create_app(config_class: type = Config, start_mqtt: bool = True, load_inference_model: bool = True) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    # supports_credentials=True: session cookie flask-login perlu dikirim lintas origin
    # (Next.js dev server beda port dari Flask) — frontend HARUS set fetch credentials:"include".
    CORS(app, supports_credentials=True)

    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, user_id)

    @login_manager.unauthorized_handler
    def unauthorized():
        from flask import jsonify

        return jsonify({"error": "belum login"}), 401

    with app.app_context():
        db.create_all()

    # SDD_SOFTWARE.md §9: model gagal load -> fallback otomatis ke mock_inference
    # dengan log warning jelas, bukan crash startup. Disimpan di app.config supaya
    # websocket_server.py bisa akses via current_app tanpa import langsung app.py.
    app.config["_INFERENCE_MODEL"] = (
        load_model_a_or_none(app.config.get("MODEL_A_CHECKPOINT_PATH", "")) if load_inference_model else None
    )

    register_websocket_routes(app)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(clinician_bp)
    app.register_blueprint(patient_bp)

    if start_mqtt:
        # NFR-SW-002: tidak boleh crash bila broker belum jalan — lihat start_mqtt_subscriber.
        app.mqtt_client = start_mqtt_subscriber(app)

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    return app


def _is_reloader_parent() -> bool:
    """`python -m backend.app` (debug=True) menjalankan modul ini DUA kali: proses induk reloader
    Werkzeug (hanya memantau perubahan file) dan proses anak yang benar-benar melayani request
    (WERKZEUG_RUN_MAIN=true). Tanpa pengecekan ini kedua proses membuka subscriber MQTT sendiri,
    sehingga setiap pesan PPG/status dari rompi diproses dua kali, dan model dimuat dua kali.
    Bila modul di-import server lain (mis. gunicorn), ini False dan semuanya berjalan normal.
    """
    return __name__ == "__main__" and os.environ.get("WERKZEUG_RUN_MAIN") != "true"


_serving = not _is_reloader_parent()
app = create_app(start_mqtt=_serving, load_inference_model=_serving)

if __name__ == "__main__":
    # host=0.0.0.0: harus bisa diakses dari device lain di jaringan lokal (ESP32),
    # bukan cuma localhost — default Flask (127.0.0.1) menolak koneksi LAN.
    app.run(host="0.0.0.0", debug=True, port=5000)
