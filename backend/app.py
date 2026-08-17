from flask import Flask
from flask_cors import CORS

from backend.api.routes import api_bp
from backend.config import Config
from backend.ingestion.mqtt_subscriber import start_mqtt_subscriber
from backend.ingestion.websocket_server import register_websocket_routes
from backend.models import db


def create_app(config_class: type = Config, start_mqtt: bool = True) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app)

    with app.app_context():
        db.create_all()

    register_websocket_routes(app)
    app.register_blueprint(api_bp)

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
