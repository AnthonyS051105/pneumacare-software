# Ringkasan Perubahan

Migrasi model suara paru dari 4 kelas (none/crackle/wheeze/both) menjadi 2 kelas
(normal/abnormal), dengan inference dipindahkan ke ML service FastAPI yang kini
berada di dalam repo ini (`ml-service/`).

## 1. ML Service Baru (`ml-service/`)

- Menambahkan service FastAPI hasil penggabungan dari repo
  `~/dev/pneumacare-ml-services`:
  - `main.py` — endpoint `GET /health` dan `POST /predict`.
  - `modules/model.py` — model AST (`RespiratoryAST`, `LungSoundClassifier`), disalin apa adanya.
  - `modules/weights/best.ckpt` — checkpoint 982 MB, dipindahkan (bukan disalin) dan tetap di-gitignore.
  - `samples/normal.wav`, `samples/abnormal.wav` — contoh audio untuk uji manual.
  - `requirements.txt` — dependensi service dengan index CPU PyTorch.
  - `.env.example` — contoh `CHECKPOINT_PATH` dan `PORT`.
  - `run.sh` — runner yang memilih Python dari `ML_PYTHON`, `.venv` lokal, atau Env lama.
  - `README.md` — cara menjalankan, lokasi checkpoint, kontrak API, dan catatan cache Hugging Face.
- `main.py` sekarang:
  - Memuat `ml-service/.env` secara eksplisit.
  - Meresolusi `CHECKPOINT_PATH` relatif terhadap folder `ml-service/`, bukan CWD.
  - Tetap boot tanpa checkpoint: `/health` mengembalikan `model_loaded: false`, `/predict` membalas 503.
- `modules/utils.py`, `Env/`, `.git/`, dan `__pycache__` tidak ikut dipindahkan.

## 2. Backend

### Inference

- Menambahkan `backend/inference/ml_service_client.py`:
  - Mengubah PCM int16 menjadi WAV di memori, lalu `POST /predict` ke ML service.
  - Memetakan `class` 0 → `normal`, 1 → `abnormal`.
  - Melempar `MLServiceError` bila service gagal atau respons tidak valid.
- `backend/inference/inference_service.py` kini memanggil ML service via HTTP;
  tidak lagi menjalankan model PyTorch lokal.
- `backend/inference/mock_inference.py` diubah ke 2 kelas:
  - `MODEL_VERSION` menjadi `mock_v3`.
  - Skenario `wheeze_rising` diganti `abnormal_rising`.
- `backend/ingestion/websocket_server.py`:
  - Segmen dikirim ke ML service bila `ML_SERVICE_URL` diisi.
  - Bila ML service gagal, otomatis fallback ke `mock_inference` dengan log error.
  - Penyimpanan hasil memakai field klasifikasi baru.
- Menghapus inference lokal lama:
  - `backend/inference/model_loader.py`
  - `backend/inference/model_startup.py`
  - `backend/inference/preprocessing.py`
  - `ai_reference/` (seluruh folder)
- `backend/app.py` tidak lagi memuat model saat startup.

### Database dan API

- `backend/models/classification.py`:
  - `wheeze_crackle_class/confidence/probabilities/model_version`
    diganti `predicted_class/confidence/probabilities/model_version`.
- Endpoint tenaga medis berubah:
  - `GET /patients/<id>/severity/latest` → `GET /patients/<id>/classification/latest`
  - `GET /patients/<id>/wheeze-crackle/history` → `GET /patients/<id>/classification/history`
- Payload `latest_classification` pasien memakai `predicted_class` 2 kelas.
- `backend/analytics/wheeze_crackle_history.py` diganti
  `backend/analytics/classification_history.py` (bucket `normal`/`abnormal`).

### Tren dan alert

- Rolling window hanya menghitung `abnormal_frequency`
  (sebelumnya wheeze dan crackle terpisah).
- `trend_detector` tidak lagi menerima parameter `metric`.
- Parameter alert tren berubah dari `wheeze_frequency` menjadi `abnormal_frequency`.
- Label frontend/seed demo disesuaikan.

### Konfigurasi dan dependensi

- `backend/config.py`:
  - Menghapus `REPO_ROOT`, `resolve_repo_path`, `MODEL_ARTIFACT_PATH`,
    `MODEL_A_CHECKPOINT_PATH`, dan `MODEL_A_VERSION`.
  - Menambahkan `ML_SERVICE_URL`, `ML_SERVICE_TIMEOUT_SECONDS`,
    `ML_SERVICE_MODEL_VERSION`.
- `backend/.env.example` diarahkan ke `ml-service/` dan variabel `ML_SERVICE_*`.
- `backend/requirements.txt`:
  - Menghapus `torch` dan `torchvision`.
  - Menambahkan `requests` untuk HTTP client.
- `backend/scripts/seed_auth_demo.py` dan `simulate_esp32.py` disesuaikan
  dengan istilah/format 2 kelas.

## 3. Frontend

- `src/lib/clinicianApi.ts`:
  - Tipe `Classification` memakai `predicted_class`, `confidence`,
    `probabilities`, `model_version`.
  - Tipe `WheezeCrackleHistory` diganti `ClassificationHistory` dengan bucket
    `normal`/`abnormal`.
  - Fungsi `fetchSeverity`/`fetchWheezeCrackleHistory` diganti
    `fetchClassification`/`fetchClassificationHistory`, menuju endpoint baru.
- `src/lib/patientApi.ts`: `latest_classification.predicted_class` menjadi
  `"normal" | "abnormal"`.
- `src/lib/clinicianAlerts.ts`: label `abnormal_frequency` menjadi
  "frekuensi abnormal".
- `src/components/portal/PatientDetail.tsx`:
  - Label kelas menjadi Normal/Abnormal.
  - Judul menjadi "Frekuensi Abnormal" dan "Tren Frekuensi Abnormal Terbaru".
  - Grafik dan kartu hasil skrining memakai field API baru.

## 4. Test

- Menambahkan:
  - `backend/tests/test_ml_service_client.py`
  - `backend/tests/test_classification_history.py`
  - `backend/tests/test_websocket_persistence.py`
- Menghapus test lama yang terkait model lokal 4 kelas:
  `test_model_loader.py`, `test_preprocessing.py`, `test_config.py`,
  `test_model_a_real_checkpoint.py`, `test_wheeze_crackle_history.py`.
- Seluruh test backend lulus: **216 passed**.
- Lint dan build frontend lulus.

## 5. Repositori dan konfigurasi

- `.gitignore`:
  - Tetap mengabaikan `*.ckpt` dan `.env*`.
  - Menambahkan pengecualian `!ml-service/.env.example`.
  - Menambahkan `ml-service/.venv/` dan cache Python di `ml-service/`.
  - Menghapus entri lama `ai_reference/` dan `backend/models_artifacts/`.
- Repo lama `~/dev/pneumacare-ml-services` tetap disimpan sebagai cadangan.

## 6. Catatan

- Checkpoint tidak di-commit; pada mesin baru perlu disediakan di
  `ml-service/modules/weights/best.ckpt` atau diatur lewat `CHECKPOINT_PATH`.
- Saat verifikasi, checkpoint asli tidak dimuat; service diuji dengan
  `CHECKPOINT_PATH` yang tidak ada (health `model_loaded: false`, predict 503).
- Kedua sampel WAV pernah sama-sama terprediksi `abnormal`; ini keterbatasan
  model/contoh, bukan indikasi pemetaan kelas yang salah.
