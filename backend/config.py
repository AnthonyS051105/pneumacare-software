import os

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Path eksplisit (bukan auto-search load_dotenv() ke atas dari cwd) — auto-search
# bisa salah menemukan .env lain di direktori leluhur (mis. ~/.env milik tool lain)
# duluan sebelum mencapai backend/.env, membuat semua config di sini diam-diam kosong.
load_dotenv(os.path.join(BASE_DIR, ".env"))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-key")

    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'pneumacare.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    MQTT_BROKER_HOST = os.environ.get("MQTT_BROKER_HOST", "localhost")
    MQTT_BROKER_PORT = int(os.environ.get("MQTT_BROKER_PORT", 1883))
    MQTT_USERNAME = os.environ.get("MQTT_USERNAME", "")
    MQTT_PASSWORD = os.environ.get("MQTT_PASSWORD", "")

    MODEL_ARTIFACT_PATH = os.environ.get("MODEL_ARTIFACT_PATH", "")

    # ⚠️ Ambang klinis default — BELUM final, lihat INTEGRATION_CONTRACT.md §0 dan
    # SDD_SOFTWARE.md §3 (tabel `thresholds`). JANGAN dianggap sebagai nilai medis
    # yang sudah divalidasi. Menunggu rujukan literatur/dosen pembimbing.
    HR_MIN_DEFAULT = None  # TODO_CLINICAL_VALUE
    HR_MAX_DEFAULT = None  # TODO_CLINICAL_VALUE
    SPO2_MIN_DEFAULT = None  # TODO_CLINICAL_VALUE
    RR_MIN_DEFAULT = None  # TODO_CLINICAL_VALUE
    RR_MAX_DEFAULT = None  # TODO_CLINICAL_VALUE

    # 🔓 Ambang signifikansi |slope| (perubahan frekuensi wheeze/crackle per menit) yang
    # memicu trend_event(significant=true) — SDD_SOFTWARE.md §6. Nilai di bawah HANYA
    # placeholder operasional supaya modul bisa dites end-to-end, BUKAN nilai klinis yang
    # sudah divalidasi Nathanael. WAJIB dikonfirmasi sebelum dipakai di luar development/demo.
    TREND_SIGNIFICANCE_THRESHOLD_DEFAULT = 0.05  # TODO_NATHANAEL_CONFIRM

    # 🔓 Ukuran rolling window trend analysis, dalam JUMLAH SEGMEN klasifikasi (bukan detik) —
    # SDD_SOFTWARE.md §6. Placeholder operasional, sama seperti di atas.
    TREND_ROLLING_WINDOW_SIZE = 6  # TODO_NATHANAEL_CONFIRM

    # 🔓 Ukuran window moving average (dalam jumlah titik frekuensi rolling-window) yang
    # dipakai sebelum regresi linear — meredam noise segmen-ke-segmen (SDD_SOFTWARE.md §6).
    TREND_MOVING_AVERAGE_WINDOW = 3  # TODO_NATHANAEL_CONFIRM

    # --- Ingestion (Fase 1) ---

    # ✅ Durasi segmen audio Model A — 5 detik, dikoreksi dari asumsi awal 10 detik
    # (terverifikasi dari ai_reference/model.py, INTEGRATION_CONTRACT.md §4.1).
    AUDIO_SEGMENT_DURATION_MS = 5_000

    # ⚠️ Nilai diusulkan di SRS_SOFTWARE.md FR-SW-004, belum divalidasi tim — timeout heartbeat
    # MQTT status sebelum device ditandai offline.
    DEVICE_OFFLINE_TIMEOUT_SECONDS = 30  # TODO_CLINICAL_VALUE (nilai operasional, bukan medis, tapi tetap diusulkan)

    # Token statis sesuai INTEGRATION_CONTRACT.md §6 — divalidasi di /ws/audio (header
    # `Authorization: Bearer <token>`, lihat websocket_server.py). Untuk MQTT, device
    # mengirim token yang SAMA sebagai password MQTT (lihat backend/mosquitto/README.md
    # untuk setup password_file broker). Baseline demo, BUKAN autentikasi kelas produksi
    # (tidak ada rotasi/expiry per device). Jangan anggap aman untuk deployment di luar
    # jaringan lokal demo.
    DEVICE_AUTH_TOKEN = os.environ.get("DEVICE_AUTH_TOKEN", "")

    # mock_inference.py (FR-SW-013) — skenario dummy yang dipakai.
    # "random": probabilitas 4-kelas acak (dinormalisasi supaya total 1.0) tiap segmen.
    # "wheeze_rising": probabilitas kelas "wheeze" naik bertahap tiap segmen berturut-turut, untuk demo trend analysis.
    MOCK_INFERENCE_SCENARIO = os.environ.get("MOCK_INFERENCE_SCENARIO", "random")

    # --- Model A: Wheeze/Crackle CNN (Fase 6) ---

    # Path checkpoint PyTorch Lightning Model A (INTEGRATION_CONTRACT.md §4.1). Kosong
    # (default) berarti checkpoint belum tersedia di environment ini — backend HARUS
    # fallback otomatis ke mock_inference dengan log warning jelas (SDD_SOFTWARE.md §9),
    # bukan crash saat startup.
    MODEL_A_CHECKPOINT_PATH = os.environ.get("MODEL_A_CHECKPOINT_PATH", "")

    # Dipakai untuk mengisi kolom wheeze_crackle_model_version di DB dan field
    # model_version di skema output (§4.1) — identifikasi checkpoint mana yang dipakai
    # untuk keperluan traceability/debug demo, TIDAK mengklaim model ini final/optimal
    # (val_loss checkpoint epoch 5 masih menurun, lihat INTEGRATION_CONTRACT.md §4.1).
    MODEL_A_VERSION = os.environ.get("MODEL_A_VERSION", "mobilenet_v3_small_epoch05_valloss0.9021")

    # --- Vitals / PPG (Fase 2) ---

    # ⚠️ Sample rate PPG mengikuti contoh di INTEGRATION_CONTRACT.md §3.3 (BELUM final,
    # perlu disesuaikan datasheet sensor Alfito). Dipakai sebagai default desain filter
    # bila sample_rate_hz tidak disertakan di payload MQTT.
    PPG_SAMPLE_RATE_HZ_DEFAULT = 100  # TODO_NATHANAEL_CONFIRM (sebenarnya domain hardware/Alfito, bukan Nathanael — lihat catatan ringkasan)

    # ⚠️ Rentang cutoff band-pass filter kardiak, sesuai proposal SDD_SOFTWARE.md §7
    # ("~1–2 Hz kardiak"). Nilai fisiologis kasar (mendekati 60–120 bpm), BUKAN rujukan
    # literatur klinis spesifik — perlu direview sebelum submit final.
    CARDIAC_BANDPASS_LOW_HZ = 1.0  # TODO_CLINICAL_VALUE
    CARDIAC_BANDPASS_HIGH_HZ = 2.0  # TODO_CLINICAL_VALUE

    # ⚠️ Rentang cutoff band-pass filter napas, sesuai proposal SDD_SOFTWARE.md §7
    # ("~0,2–0,5 Hz napas"). Sama seperti di atas, bukan rujukan literatur spesifik.
    RESPIRATORY_BANDPASS_LOW_HZ = 0.2  # TODO_CLINICAL_VALUE
    RESPIRATORY_BANDPASS_HIGH_HZ = 0.5  # TODO_CLINICAL_VALUE

    # Orde filter Butterworth IIR (SDD_SOFTWARE.md §7) — nilai umum untuk band-pass sinyal
    # fisiologis, bukan nilai medis, tidak perlu TODO_CLINICAL_VALUE.
    BANDPASS_FILTER_ORDER = 4

    # ⚠️ Batas plausibilitas HR (bpm) untuk menandai hasil estimasi sebagai tidak valid —
    # SDD_SOFTWARE.md §8 ("bukan menampilkan angka HR palsu dengan percaya diri"). Rentang
    # longgar sekadar sanity check (deteksi puncak yang jelas keliru), BUKAN ambang klinis.
    HR_PLAUSIBLE_MIN_BPM = 30  # TODO_CLINICAL_VALUE
    HR_PLAUSIBLE_MAX_BPM = 220  # TODO_CLINICAL_VALUE

    # 🚨🚨 SANGAT BELUM AKURAT — JANGAN DIPAKAI UNTUK KLAIM KLINIS APAPUN 🚨🚨
    # Koefisien kurva kalibrasi rasio-R → persen SpO2 untuk sensor MAX30102 (dikonfirmasi
    # Tony 2026-08-13, dual-wavelength — lihat SDD_SOFTWARE.md §7). Rumus linear umum
    # `SpO2 = A + B * R` yang banyak dipakai di project open-source berbasis MAX30102,
    # BUKAN hasil kalibrasi khusus terhadap sensor/kondisi tim ini, dan BUKAN rujukan
    # literatur medis. Sebelum dipakai di luar development/demo, WAJIB dikalibrasi ulang
    # (mis. dibandingkan bacaan pulse oximeter medis rujukan pada beberapa subjek sehat).
    SPO2_CALIBRATION_COEFF_A = 110.0  # TODO_CLINICAL_VALUE — belum dikalibrasi, hanya placeholder
    SPO2_CALIBRATION_COEFF_B = -25.0  # TODO_CLINICAL_VALUE — belum dikalibrasi, hanya placeholder

    # ⚠️ Rentang plausibilitas SpO2 (%) untuk sanity check hasil estimasi — bukan ambang
    # klinis alert (lihat SPO2_MIN_DEFAULT di atas untuk itu). SpO2 secara fisiologis
    # tidak mungkin > 100%; batas bawah longgar sekadar filter noise ekstrem.
    SPO2_PLAUSIBLE_MIN_PERCENT = 50  # TODO_CLINICAL_VALUE
    SPO2_PLAUSIBLE_MAX_PERCENT = 100

    # --- Alert Engine (Fase 3) ---

    # 🧩 Jumlah evaluasi trend_event berturut-turut dengan significant=true yang dibutuhkan
    # supaya trigger trend_slope dieskalasi ke alert level 3 sendirian (tanpa trigger lain) —
    # INTEGRATION_CONTRACT.md §5.1 v2, SDD_SOFTWARE.md §7.2. Ini PARAMETER TUNING SISTEM,
    # BUKAN nilai medis final — dipilih 3 sebagai keseimbangan awal antara sensitif terhadap
    # tren nyata vs tidak gampang false-alarm dari 1 kali salah baca model AI (akurasi ~73%).
    # WAJIB divalidasi ulang setelah ada data simulasi yang representatif.
    TREND_PERSISTENCE_MIN_CONSECUTIVE = 3  # TODO_CLINICAL_VALUE (parameter tuning, bukan medis)

    # 🧩 Margin "near-threshold" untuk Level 1 (informasi) — INTEGRATION_CONTRACT.md §5.1 v3,
    # SDD_SOFTWARE.md §7.5. Didefinisikan RELATIF terhadap ambang (bukan angka absolut) karena
    # ambang klinis sendiri masih TODO_CLINICAL_VALUE — begitu ambang final diisi, margin ini
    # otomatis ikut menyesuaikan. Ini HEURISTIK TUNING, BUKAN nilai medis yang divalidasi —
    # WAJIB direview ulang begitu ambang klinis sungguhan tersedia, idealnya oleh orang dengan
    # latar belakang medis, bukan diputuskan sendiri oleh tim teknis.
    LEVEL1_MARGIN_PCT = 0.10  # TODO_CLINICAL_VALUE — untuk HR/RR (parameter dua-sisi, min & max)
    LEVEL1_MARGIN_SPO2_ABS = 2  # TODO_CLINICAL_VALUE — poin persentase SpO2 (parameter satu-sisi, hanya min)
