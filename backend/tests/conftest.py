import pytest
from werkzeug.security import generate_password_hash

from backend.app import create_app
from backend.config import Config
from backend.models import db
from backend.models.user import User


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


@pytest.fixture
def app():
    app = create_app(TestConfig, start_mqtt=False)
    yield app
    with app.app_context():
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def create_user(app, email: str, password: str, role: str, **extra) -> str:
    """Buat user langsung di DB (tanpa lewat endpoint signup) — dipakai test yang
    butuh user sudah ada sebelum menguji endpoint lain. Return user id."""
    with app.app_context():
        user = User(
            email=email,
            password_hash=generate_password_hash(password),
            role=role,
            full_name=extra.get("full_name", "Test User"),
        )
        db.session.add(user)
        db.session.commit()
        return user.id


def login_as(client, email: str, password: str):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})
