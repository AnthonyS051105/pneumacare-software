import json

from backend.tests.conftest import create_user, login_as
from backend.tests.test_clinician_routes import _seed_clinician_with_patient, _login_clinician


URL = '/api/v1/patients/patient-1/audio-experiment/latest'


def test_experimental_audio_requires_login(client):
    assert client.get(URL).status_code == 401


def test_experimental_audio_requires_own_clinician(app, client):
    _seed_clinician_with_patient(app)
    create_user(app, 'patient@example.com', 'password123', 'pasien')
    login_as(client, 'patient@example.com', 'password123')
    assert client.get(URL).status_code == 403
    create_user(app, 'other@example.com', 'password123', 'clinician')
    login_as(client, 'other@example.com', 'password123')
    assert client.get(URL).status_code == 404


def test_experimental_audio_filters_devices_and_never_claims_clinical_validity(app, client, tmp_path):
    _seed_clinician_with_patient(app)
    _login_clinician(client)
    app.config['AUDIO_CAPTURE_DIRECTORY'] = str(tmp_path)
    for ch in range(1, 5):
        m = dict(device_id='pneumacare-a1b2', capture_id=2, stream_id='boot',
                 channel_id=ch, start_ms=1700000000000, end_ms=1700000002000,
                 data_origin='simulated' if ch == 3 else 'measured',
                 source_channel_id=4 if ch == 3 else ch, inference_status='completed',
                 classification_validated=False, alert_eligible=False)
        (tmp_path/f'{ch}.json').write_text(json.dumps(m))
    (tmp_path/'foreign.json').write_text(json.dumps(dict(m, device_id='other-device', start_ms=1800000000000)))
    (tmp_path/'corrupt.json').write_text('{')
    data = client.get(URL).get_json()
    assert data['available'] is True and len(data['channels']) == 4
    assert data['clinical_alerts_enabled'] is False
    assert data['classification_validated'] is False
    assert data['channels'][2]['data_origin'] == 'simulated'
    assert data['capture_id'] == 2
    assert not any('path' in c for c in data['channels'])


def test_experimental_audio_missing_directory_returns_empty(app, client, tmp_path):
    _seed_clinician_with_patient(app)
    _login_clinician(client)
    app.config['AUDIO_CAPTURE_DIRECTORY'] = str(tmp_path/'not-created')
    assert client.get(URL).get_json()['available'] is False
