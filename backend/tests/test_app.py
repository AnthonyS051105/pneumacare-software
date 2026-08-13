def test_health_endpoint(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_db_tables_created(app):
    from backend.models import db, Patient

    with app.app_context():
        assert Patient.query.count() == 0
