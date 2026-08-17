"""Simulator ESP32 palsu (Fase 1, TASK_BREAKDOWN_SOFTWARE.md).

Berperan sebagai vest fisik: mengirim audio chunk via websocket dan PPG/status
via MQTT, mengikuti skema INTEGRATION_CONTRACT.md persis (termasuk keputusan
format audio base64 JSON di §2.3). Dipakai untuk mengetes pipeline ingestion
tanpa hardware fisik.

Cara pakai (dari folder backend/, dengan venv aktif):
    python -m scripts.simulate_esp32 --duration 20
    python -m scripts.simulate_esp32 --host localhost --ws-port 5000 --mqtt-port 1883

Butuh: backend Flask (`python -m backend.app`) dan Mosquitto sudah jalan.
"""

import argparse
import asyncio
import base64
import json
import logging
import random
import struct
import time

import paho.mqtt.client as mqtt
import websockets

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("simulate_esp32")

DEVICE_ID = "pneumacare-a1b2"
# ✅ Sample rate akuisisi mentah firmware (native rate mikrofon, contoh INMP441 —
# INTEGRATION_CONTRACT.md §2.3), BUKAN 22000 Hz target model. Backend resample ke
# 22000 Hz saat preprocessing (§4.1) — simulator sengaja TIDAK mengirim di 22000 Hz
# supaya jalur resample sungguhan ikut teruji, bukan cuma no-op.
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_DURATION_MS = 1000
PPG_SAMPLE_RATE_HZ = 100  # ⚠️ contoh dari INTEGRATION_CONTRACT.md §3.3, belum final
PPG_PUBLISH_INTERVAL_S = 2
STATUS_PUBLISH_INTERVAL_S = 5
CHANNEL_IDS = (1, 2, 3, 4)


def _generate_pcm_chunk(sample_rate: int, duration_ms: int) -> bytes:
    n_samples = int(sample_rate * duration_ms / 1000)
    samples = [random.randint(-3000, 3000) for _ in range(n_samples)]
    return struct.pack(f"<{n_samples}h", *samples)


async def _stream_audio(host: str, ws_port: int, duration_s: float) -> None:
    uri = f"ws://{host}:{ws_port}/ws/audio"
    seq_no_per_channel = {ch: 0 for ch in CHANNEL_IDS}

    async with websockets.connect(uri) as ws:
        logger.info("audio: terhubung ke %s", uri)
        start = time.monotonic()
        channel_cycle = iter(())
        while time.monotonic() - start < duration_s:
            try:
                channel_id = next(channel_cycle)
            except StopIteration:
                channel_cycle = iter(CHANNEL_IDS)
                channel_id = next(channel_cycle)

            pcm_bytes = _generate_pcm_chunk(AUDIO_SAMPLE_RATE, AUDIO_CHUNK_DURATION_MS)
            message = {
                "device_id": DEVICE_ID,
                "channel_id": channel_id,
                "sample_rate": AUDIO_SAMPLE_RATE,
                "bit_depth": 16,
                "timestamp_ms": int(time.time() * 1000),
                "seq_no": seq_no_per_channel[channel_id],
                "chunk_duration_ms": AUDIO_CHUNK_DURATION_MS,
                "pcm_base64": base64.b64encode(pcm_bytes).decode("ascii"),
            }
            seq_no_per_channel[channel_id] += 1

            await ws.send(json.dumps(message))
            await asyncio.sleep(AUDIO_CHUNK_DURATION_MS / 1000 / len(CHANNEL_IDS))

    logger.info("audio: selesai mengirim, koneksi ditutup")


def _publish_ppg_and_status(host: str, mqtt_port: int, duration_s: float) -> None:
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.connect(host, mqtt_port)
    client.loop_start()
    logger.info("mqtt: terhubung ke %s:%s", host, mqtt_port)

    start = time.monotonic()
    last_ppg = 0.0
    last_status = 0.0
    battery_pct = 87

    while time.monotonic() - start < duration_s:
        now = time.monotonic()

        if now - last_ppg >= PPG_PUBLISH_INTERVAL_S:
            n_samples = int(PPG_SAMPLE_RATE_HZ * PPG_PUBLISH_INTERVAL_S)
            payload = {
                "device_id": DEVICE_ID,
                "timestamp_ms": int(time.time() * 1000),
                "sample_rate_hz": PPG_SAMPLE_RATE_HZ,
                "samples": [500 + random.randint(-20, 20) for _ in range(n_samples)],
            }
            client.publish(f"pneumacare/{DEVICE_ID}/ppg/raw", json.dumps(payload))
            last_ppg = now

        if now - last_status >= STATUS_PUBLISH_INTERVAL_S:
            payload = {
                "device_id": DEVICE_ID,
                "status": "online",
                "timestamp_ms": int(time.time() * 1000),
                "battery_pct": battery_pct,
            }
            client.publish(f"pneumacare/{DEVICE_ID}/status", json.dumps(payload), retain=True)
            last_status = now

        time.sleep(0.1)

    client.loop_stop()
    client.disconnect()
    logger.info("mqtt: selesai, koneksi ditutup")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Simulator ESP32 palsu PNEUMACARE")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--ws-port", type=int, default=5000)
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument("--duration", type=float, default=20.0, help="durasi simulasi (detik)")
    args = parser.parse_args()

    loop = asyncio.get_running_loop()
    mqtt_task = loop.run_in_executor(
        None, _publish_ppg_and_status, args.host, args.mqtt_port, args.duration
    )
    await asyncio.gather(
        _stream_audio(args.host, args.ws_port, args.duration),
        mqtt_task,
    )


if __name__ == "__main__":
    asyncio.run(main())
