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

## 7. Pembaruan: Integrasi Deteksi Siklus Napas

Menambahkan deteksi boundary siklus napas dari `resp_cycle.py` ke pipeline backend.
Mekanisme chunk/segmen **tidak diubah**: tetap tumbling 5 detik per channel, tanpa
overlap dan tanpa windowing baru.

### Alur baru

1. Segmen 5 detik terbentuk seperti sebelumnya.
2. Backend menjalankan detektor siklus pada PCM segmen tersebut.
3. Setiap siklus `(start_s, end_s)` dipotong tepat pada batasnya, lalu WAV potongan
   itu dikirim ke ML service (durasi tidak selalu 5 detik).
4. Jika tidak ada siklus, sample rate tidak didukung, atau detektor error, backend
   memakai fallback: seluruh segmen 5 detik diklasifikasikan seperti mekanisme lama.
5. Setiap hasil klasifikasi disimpan di `readings_classification`, dengan metadata
   deteksi di tabel baru `respiratory_cycles`.
6. Trend analysis dan alert engine tetap dijalankan **sekali per segmen analisis**,
   setelah semua klasifikasi siklus pada segmen itu tersimpan.

### File backend yang ditambahkan/diubah

- `backend/analysis/resp_cycle.py`
  - Dipindahkan dari `ml-service/modules/resp_cycle.py` agar bisa di-import backend
    (folder `ml-service` mengandung tanda hubung sehingga bukan package Python).
  - Algoritma deteksi tidak diubah.
  - `dtw_per_cycle` tetap dikembalikan seperti sebelumnya.
  - Menambahkan field `cycle_scores` yang sejajar 1:1 dengan `cycles`; posisi siklus
    model bernilai `None` karena tidak diuji terhadap dirinya sendiri.
  - Menambahkan helper `_align_cycle_scores()`.
- `backend/analysis/cycle_segmenter.py` (baru)
  - Normalisasi PCM int16 ke float, memanggil detektor, memotong PCM per siklus.
  - Menolak deteksi bila `sample_rate <= 2000 Hz`.
  - Mengembalikan status `detected`, `no_cycles`, `unsupported_sample_rate`, atau
    `error` beserta `mean_dtw` dan skor per siklus.
- `backend/models/respiratory_cycle.py` (baru)
  - Tabel `respiratory_cycles`, satu baris per baris `readings_classification`.
  - Menyimpan `analysis_start`/`analysis_end`, `detection_status`, `cycle_index`,
    `cycle_start_ms`/`cycle_end_ms` (epoch ms absolut), `mean_dtw`, dan `dtw_score`.
  - Baris fallback tetap disimpan dengan boundary `NULL`.
- `backend/models/__init__.py`
  - Import `RespiratoryCycle` agar tabel dibuat otomatis oleh `db.create_all()`
    tanpa migrasi ALTER TABLE.
- `backend/ingestion/websocket_server.py`
  - `_handle_segment()` sekarang mendeteksi siklus sebelum klasifikasi.
  - Logika pemilihan ML service/mock diekstrak ke `_classify_input()`.
  - `_persist_cycle_metadata()` menyimpan boundary/status tiap klasifikasi.
  - Log baru mencatat jumlah siklus, `mean_dtw`, dan durasi deteksi per segmen.
  - Perilaku fallback `MLServiceError` ke `mock_inference` dipertahankan per potongan.
  - `_persist_segment_result()` tidak berubah, sehingga test lama tetap kompatibel.

### Dampak ke ML service

- ML service sekarang bisa menerima WAV dengan durasi bervariasi (mengikuti durasi
  siklus), bukan selalu 5 detik.
- `ml-service/modules/model.py` menangani ini lewat `fix_length`: audio > 5 detik
  di-center-crop; audio < 2,5 detik di-tile lalu di-zero-pad; audio 2,5-5 detik
  di-zero-pad di ujung.
- Tidak ada perubahan kontrak API `/predict`.

### Test

- Menambahkan `backend/tests/test_cycle_segmenter.py`:
  pemotongan PCM, status `no_cycles`/`unsupported_sample_rate`/`error`, dan
  penyejajaran `cycle_scores`.
- Menambahkan `backend/tests/test_websocket_cycles.py`:
  - 2 siklus menghasilkan 2 klasifikasi + 2 baris `respiratory_cycles`;
  - fallback tanpa siklus menghasilkan 1 klasifikasi dengan boundary `NULL`;
  - 3 segmen × 3 siklus menghasilkan 9 klasifikasi dan 1 `trend_event` setelah
    histori cukup untuk rolling window.
- `backend/tests/test_websocket_persistence.py` tidak diubah.
- Seluruh test backend lulus: **225 passed**.
- Uji manual dengan audio nyata (`ml-service/samples/data.wav`) dan ML service aktif:
  - 3 segmen × 3 siklus → 9 klasifikasi, 9 baris `respiratory_cycles`, 1 `trend_event`;
  - `model_version` = `ast_model_v1.0`;
  - deteksi ~9-14 ms per segmen setelah panggilan pertama (JIT numba ~147 ms).

### Dokumentasi

- Menambahkan `README_DATA_FLOW.md` berisi diagram aliran data, deteksi siklus,
  fallback, durasi WAV variabel, dan daftar tabel database.
- Menambahkan tautan ke `README_DATA_FLOW.md` di `README.md`.

### Catatan perilaku

- Satu segmen 5 detik dapat menghasilkan beberapa baris klasifikasi (satu per siklus).
  Rolling window trend berukuran 6 event karenanya bisa hanya mencakup ~9-10 detik,
  bukan ~30 detik. Frekuensi abnormal per menit menjadi lebih besar dan ambang tren
  0,05/menit lebih mudah terlampaui. Perilaku ini didokumentasikan, belum diubah.
- Deteksi pada segmen 5 detik bisa sering jatuh ke fallback karena detektor
  membutuhkan beberapa siklus yang jelas. Fallback bukan error.
- Detektor memakai DTW; `numba` bersifat opsional. Tanpa numba, deteksi bisa lebih
  lambat dan menahan loop WebSocket.
- `resp_cycle.py` tidak lagi berada di `ml-service/modules/`; kode eksternal yang
  mengimpor path lama perlu disesuaikan.
