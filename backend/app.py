from flask import Flask
from flask_cors import CORS
from flask_login import LoginManager

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


def create_app(config_class: type = Config, start_mqtt: bool = True) -> Flask:
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
    app.config["_INFERENCE_MODEL"] = load_model_a_or_none(app.config.get("MODEL_A_CHECKPOINT_PATH", ""))

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


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
