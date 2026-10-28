"""Actual Flask-Sock transport regression, isolated app DB and token."""
from threading import Thread
from time import monotonic, sleep

import pytest
from websockets.sync.client import connect
from websockets.exceptions import ConnectionClosedError
from werkzeug.serving import make_server

from backend.tests.test_audio_receiver import message
from backend.models import db
from backend.models.classification import ReadingClassification


def test_transport_authorization_invalid_frame_and_result_storage(app):
    app.config['DEVICE_AUTH_TOKEN'] = 'test-only'
    server = make_server('127.0.0.1', 0, app, threaded=True)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    worker = app.extensions['audio_worker']
    uri = f'ws://127.0.0.1:{server.server_port}/ws/audio'
    try:
        with connect(uri, close_timeout=.2) as socket:
            with pytest.raises(ConnectionClosedError) as exc:
                socket.recv(timeout=2)
            assert exc.value.rcvd.code == 1008
        assert worker.thread is None  # unauthorized connections never start a worker
        with connect(uri, additional_headers={'Authorization':'Bearer test-only'}) as socket:
            socket.send('not valid JSON')
            for seq in range(20):
                for ch in range(1,5):
                    socket.send(message(seq,ch))
            deadline = monotonic()+5
            while worker.snapshot()['received'] < 4 and monotonic() < deadline:
                sleep(.01)
            assert worker.wait_idle(3)
            assert worker.snapshot()['completed'] == 4
            with app.app_context():
                readings = ReadingClassification.query.order_by(ReadingClassification.channel_id).all()
                assert [r.channel_id for r in readings] == [1,2,3,4]
                assert all(r.wheeze_crackle_model_version == 'mock_v2' for r in readings)
    finally:
        server.shutdown()
        server.server_close()
        thread.join(2)
