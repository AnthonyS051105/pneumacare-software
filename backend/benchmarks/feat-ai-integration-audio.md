> **Status terbaru:** lihat [CURRENT_STATUS.md](CURRENT_STATUS.md). Pengujian fisik berikutnya membuktikan drop masih terjadi; feat/ai-integration kini acuan demo dan sudah dijalankan dari checkout terpisah. Laporan di bawah adalah rekaman tahap sebelumnya.

# Isolated latest-branch compatibility audit — 2026-10-28

Base: `origin/feat/ai-integration`, commit `b177a81` (add cycle detection).
The working branch was not switched or merged. Source was extracted with
`git archive` into `/tmp/pneumacare-latest-ai`.

## Reviewable adaptation

`feat-ai-integration-audio.patch` applies to the base commit above. It has NOT
been applied to the main working tree. `git apply --check` passed against a
second clean archive. Review it on the latest branch before adoption.

The patch keeps the latest branch's normal/abnormal HTTP inference and
RespiratoryCycle/classification persistence, and adds the bounded single worker,
strict receiver, sample continuity, ownership and cooperative cancellation from
the throughput fix. It retains per-cycle classification, checks cancellation
before/after HTTP/model calls and before persistence/trends/alerts. It also fixes
`detect_cycle_slices`'s emptiness check for immutable NumPy PCM and uses string
WebSocket close reasons, as required by the actual Flask-Sock/wsproto transport.

The latest branch still commits classification and cycle metadata separately,
as it did before this patch. This patch preserves that persistence behavior;
it is not a database migration or a claim of atomic multi-table persistence.

## Tests

- Unmodified latest focused tests: 12 passed in 0.24 s.
- Adapted latest full backend suite: 252 passed in 23.56 s.
- After the final worker/auth-reason refresh, focused receiver/worker/buffer,
  cycles and auth tests: 47 passed in 1.16 s.
- New latest-specific tests check immutable PCM and cancellation during a
  cycle model call preventing classification/cycle persistence.

Used existing backend Python venv. It lacks `requests`; tests appended
`/usr/lib/python3/dist-packages` to import existing requests 2.31.0 without
changing the venv. The harness used an in-memory DB, `ML_SERVICE_URL=''`, and
stubbed import-time MQTT/watchdog startup because this sandbox denies sockets.
The classification tests use mock/fake outputs. This validates compatibility,
not AST capacity or a physical ESP32 session.

## Actual latest-model availability

The tracked ML service contains only `.gitkeep` under `modules/weights`.
Its documented `~/dev/pneumacare-ml-services/Env` and default `best.ckpt` are
absent. A filename search under the user's home (depth <= 6) found no best.ckpt.
The old MobileNet checkpoint in ai_reference exists; it is a different model.
The backend venv also lacks FastAPI, transformers, librosa, soundfile,
PyTorch Lightning and multipart. No weights were downloaded or substituted.
Therefore real AST inference capacity has NOT been measured.

Unlike the older MobileNet pipeline (4 classes, preprocessing to 22000 Hz),
latest AST uses 2 classes and 16000 Hz. Latest cycle detection can emit multiple
HTTP classifications per 5-second analysis segment. A four-channel capacity
budget must account for that variable work rather than assuming four model
calls every five seconds.

Detector-only sample measurements, 5 s at 16 kHz, no numba:

| Sample (first 5 s) | Cycles | First run | Second run |
|---|---:|---:|---:|
| abnormal.wav | 2 | 46.71 ms | 39.00 ms |
| data.wav | 2 | 29.25 ms | 25.81 ms |
| normal.wav | 3 | 43.59 ms | 43.10 ms |

WAVs were read with scipy, mixed to mono where needed and resampled for this
isolated detector check. These timings exclude HTTP, AST feature extraction,
model forward, database, trends and alerts. They are not an end-to-end capacity
claim. Raw detector-only measurements were saved at
`/tmp/pneumacare-latest-ai-cycle-benchmark.json`.
