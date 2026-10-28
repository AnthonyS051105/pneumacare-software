"""Start the two-class demo without reloader, with an isolated DB and readiness check.

Optional --env-file is loaded by dotenv at runtime; credentials are never printed.
--allow-unavailable-model is for transport diagnostics only, not inference demo.
"""
import argparse
import json
from pathlib import Path
import os
import urllib.request

from dotenv import load_dotenv


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--env-file', type=Path)
    parser.add_argument('--database', type=Path, default=Path('backend/demo-two-class.db'))
    parser.add_argument('--check', action='store_true')
    parser.add_argument('--allow-unavailable-model', action='store_true')
    parser.add_argument('--tcp-quickack', action='store_true', help='Linux transport diagnostic A/B only')
    parser.add_argument('--receive-only', action='store_true', help='transport diagnostic; never saves classifications')
    args = parser.parse_args()
    if args.env_file:
        load_dotenv(args.env_file, override=False)
    database = args.database.resolve()
    # Deliberately override DATABASE_URL loaded from a different checkout.
    os.environ['DATABASE_URL'] = 'sqlite:///' + str(database)
    # Readiness checks use the same non-mutating schema guard as server startup.
    from flask import Flask
    from backend.models import db
    from backend.database_schema import assert_compatible_schema
    schema_app = Flask(__name__)
    schema_app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
    db.init_app(schema_app)
    with schema_app.app_context():
        try:
            assert_compatible_schema()
        finally:
            db.session.remove()
            db.engine.dispose()
    url = os.environ.get('ML_SERVICE_URL', 'http://127.0.0.1:8000')
    loaded = False
    if url:
        try:
            with urllib.request.urlopen(url.rstrip('/')+'/health', timeout=3) as response:
                loaded = json.load(response).get('model_loaded') is True
        except Exception:
            pass
    status = {'source': 'feat/ai-integration', 'classes': ['normal', 'abnormal'],
              'database': str(database), 'model_loaded': loaded,
              'mock_explicit': not bool(url),
              'device_auth_configured': bool(os.environ.get('DEVICE_AUTH_TOKEN'))}
    print(json.dumps(status), flush=True)
    if args.check:
        return 0 if loaded else 2
    if not loaded and not args.allow_unavailable_model and not args.receive_only:
        parser.error('AST not ready: start ML service with real checkpoint first; no mock substitution')
    if not loaded:
        print('TRANSPORT DIAGNOSTICS ONLY: model unavailable, no real inference validation.', flush=True)
    if args.tcp_quickack:
        import socket
        if not args.receive_only or not hasattr(socket, "TCP_QUICKACK"):
            parser.error("QUICKACK experiment requires receive-only mode on Linux")
        from simple_websocket.ws import Base
        original_receive = Base.receive
        class QuickAckSocket:
            def __init__(self, raw):
                self.raw = raw
            def __getattr__(self, key):
                return getattr(self.raw, key)
            def recv(self, *pos, **kw):
                data = self.raw.recv(*pos, **kw)
                self.raw.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
                return data
        def quickack_receive(ws, *pos, **kw):
            if not isinstance(ws.sock, QuickAckSocket):
                ws.sock = QuickAckSocket(ws.sock)
                ws.sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
            return original_receive(ws, *pos, **kw)
        Base.receive = quickack_receive
        print('EXPERIMENT tcp_quickack=per_recv; no firmware/protocol change.', flush=True)
    from backend.app import create_app
    app = create_app()
    if args.receive_only:
        import logging
        app.extensions['audio_worker'].process = lambda job: logging.getLogger(__name__).info(
            "audio_receive_only device=%s channel=%s samples=%d", job.segment.device_id,
            job.segment.channel_id, len(job.segment.pcm_samples))
        print('RECEIVE ONLY: classification, cycle analysis, trends and audio alerts disabled.', flush=True)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
