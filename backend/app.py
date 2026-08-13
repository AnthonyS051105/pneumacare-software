from flask import Flask
from flask_cors import CORS

from backend.config import Config
from backend.models import db


def create_app(config_class: type = Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    CORS(app)

    with app.app_context():
        db.create_all()

    @app.get("/api/v1/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, port=5000)
