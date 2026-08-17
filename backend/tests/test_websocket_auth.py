from werkzeug.datastructures import Headers

from backend.ingestion.websocket_server import _is_authorized


def test_no_token_configured_allows_all(app):
    app.config["DEVICE_AUTH_TOKEN"] = ""
    with app.app_context():
        assert _is_authorized(Headers()) is True


def test_correct_bearer_token_authorized(app):
    app.config["DEVICE_AUTH_TOKEN"] = "secret-token"
    with app.app_context():
        headers = Headers([("Authorization", "Bearer secret-token")])
        assert _is_authorized(headers) is True


def test_missing_header_rejected_when_token_configured(app):
    app.config["DEVICE_AUTH_TOKEN"] = "secret-token"
    with app.app_context():
        assert _is_authorized(Headers()) is False


def test_wrong_token_rejected(app):
    app.config["DEVICE_AUTH_TOKEN"] = "secret-token"
    with app.app_context():
        headers = Headers([("Authorization", "Bearer wrong-token")])
        assert _is_authorized(headers) is False


def test_non_bearer_scheme_rejected(app):
    app.config["DEVICE_AUTH_TOKEN"] = "secret-token"
    with app.app_context():
        headers = Headers([("Authorization", "Basic secret-token")])
        assert _is_authorized(headers) is False
