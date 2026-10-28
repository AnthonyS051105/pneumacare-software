"""Isolated loopback WebSocket test, 4 x 16 kHz, 250 ms, real pacing.

Creates a temporary SQLite DB. Never sends to MQTT or writes the development DB.
--baseline uses unchanged synchronous receiver from HEAD in an isolated source tree.
Reports local monotonic durations, not device-to-server latency.
"""
import argparse
import base64
import hashlib
import json
import logging
from pathlib import Path
import platform
import tempfile
from threading import Thread
from time import monotonic, sleep, time

import numpy as np


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--duration', type=int, default=60)
    parser.add_argument('--model', choices=['real', 'mock'], default='real')
    parser.add_argument('--mode', choices=['worker', 'baseline'], default='worker')
    parser.add_argument('--slow-seconds', type=float, default=0)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    if args.duration % 5:
        parser.error('duration must be multiple of 5')

    from backend.config import Config
    checkpoint = Config.MODEL_A_CHECKPOINT_PATH
    Config.MODEL_A_CHECKPOINT_PATH = ''  # no global model load during app import
    # Disable import-time background services BEFORE importing the app module.
    import backend.ingestion.mqtt_subscriber as mqtt
    import backend.ingestion.device_watchdog as watchdog
    mqtt.start_mqtt_subscriber = lambda app: None
    watchdog.start_device_watchdog = lambda app: None
    with tempfile.TemporaryDirectory(prefix='audio-load-') as tmp:
        Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///' + tmp + '/load.db'
        from backend.app import create_app
        import backend.ingestion.websocket_server as ws_module
        from backend.models import db
        from backend.models.classification import ReadingClassification
        from werkzeug.serving import make_server
        from websockets.sync.client import connect
        import torch

        class LoadConfig(Config):
            DEVICE_AUTH_TOKEN = 'isolated-load-token'
        app = create_app(LoadConfig, start_mqtt=False, load_inference_model=False)
        if args.model == 'real':
            from backend.inference.model_loader import load_model
            app.config['_INFERENCE_MODEL'] = load_model(checkpoint)
        elif args.slow_seconds:
            original_mock = ws_module.run_mock_inference
            def slow_mock(**kwargs):
                sleep(args.slow_seconds)
                return original_mock(**kwargs)
            ws_module.run_mock_inference = slow_mock

        records = []
        class Capture(logging.Handler):
            def emit(self, record):
                records.append(record.getMessage())
        capture = Capture()
        root = logging.getLogger()
        root.handlers.clear()
        root.addHandler(capture)
        root.setLevel(logging.INFO)
        # Observe handler time and completed segments without altering their work.
        handle_times = []
        original_handle = ws_module._handle_segment
        def observed(segment, *extra):
            start = monotonic()
            try:
                return original_handle(segment, *extra)
            finally:
                handle_times.append((monotonic()-start)*1000)
        ws_module._handle_segment = observed

        server = make_server('127.0.0.1', 0, app, threaded=True)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        worker = app.extensions.get('audio_worker')
        if (args.mode == 'worker') != (worker is not None):
            raise RuntimeError('mode must match source tree: baseline requires unchanged HEAD archive')
        samples = (3000*np.sin(2*np.pi*400*np.arange(4000)/16000)).astype('<i2')
        encoded = base64.b64encode(samples.tobytes()).decode()
        send_times, pacing_lag = [], []
        epoch = int(time()*1000)
        with connect(f'ws://127.0.0.1:{server.server_port}/ws/audio',
                     additional_headers={'Authorization':'Bearer isolated-load-token'}) as socket:
            start = monotonic()
            for seq in range(args.duration*4):
                deadline = start + seq*.25
                sleep(max(0, deadline-monotonic()))
                pacing_lag.append(max(0, monotonic()-deadline)*1000)
                for channel in range(1,5):
                    payload = dict(device_id='isolated-load', channel_id=channel, sample_rate=16000,
                                   bit_depth=16, timestamp_ms=epoch+seq*250, seq_no=seq,
                                   chunk_duration_ms=250, pcm_base64=encoded,
                                   stream_id='load-session', sample_start=seq*4000)
                    before = monotonic()
                    socket.send(json.dumps(payload))
                    send_times.append((monotonic()-before)*1000)
            sleep(max(0, start+args.duration-monotonic()))
            # Drain BEFORE closing: disconnect explicitly cancels unfinished session jobs.
            drain_start = monotonic()
            expected = args.duration//5*4
            while monotonic()-drain_start < 30:
                if worker:
                    stats = worker.snapshot()
                    terminal = sum(stats[k] for k in ('completed','failed','cancelled','rejected'))
                    if stats['received'] >= expected and terminal >= expected:
                        break
                elif len(handle_times) >= expected:
                    break
                sleep(.01)
            stats = worker.snapshot() if worker else {}
            drain_s = monotonic()-drain_start
            receiver = app.extensions.get('audio_receiver')
            connection = next(iter(receiver.owners.values()), None) if receiver else None
            receive = {k:getattr(connection,k) for k in
                       ('chunks','gaps','invalid','decode_ms','assemble_ms','receive_max_ms')} if connection else {}
        server.shutdown()
        server.server_close()
        if worker:
            worker.stop()
        with app.app_context():
            saved = ReadingClassification.query.count()
        def distribution(values):
            return {k:float(np.percentile(values,p)) for k,p in [('p50',50),('p95',95),('max',100)]} if values else {}
        result = dict(mode=args.mode, model=args.model, slow_seconds=args.slow_seconds,
                      duration_s=args.duration, sent=len(send_times), saved=saved, expected_segments=expected,
                      sent_chunks_per_s=len(send_times)/args.duration, drain_s=drain_s, worker=stats,
                      receive=receive, handle_ms=distribution(handle_times), send_ms=distribution(send_times),
                      pacing_lag_ms=distribution(pacing_lag), cpu=platform.processor(), threads=torch.get_num_threads(),
                      torch=torch.__version__, cuda=torch.cuda.is_available(),
                      checkpoint_sha256=hashlib.sha256(Path(checkpoint).read_bytes()).hexdigest() if args.model=='real' else None)
        Path(args.output).write_text(json.dumps(result,indent=2)+'\n')
        Path(args.output+'.log').write_text('\n'.join(records)+'\n')
        print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
