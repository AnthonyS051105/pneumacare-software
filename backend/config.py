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

    # ⚠️ Ambang klinis default — BELUM final, lihat INTEGRATION_CONTRACT.md §0 dan
    # SDD_SOFTWARE.md §3 (tabel `thresholds`). JANGAN dianggap sebagai nilai medis
    # yang sudah divalidasi. Menunggu rujukan literatur/dosen pembimbing.
    HR_MIN_DEFAULT = None  # TODO_CLINICAL_VALUE
    HR_MAX_DEFAULT = None  # TODO_CLINICAL_VALUE
    SPO2_MIN_DEFAULT = None  # TODO_CLINICAL_VALUE
    RR_MIN_DEFAULT = None  # TODO_CLINICAL_VALUE
    RR_MAX_DEFAULT = None  # TODO_CLINICAL_VALUE

    # 🔓 Ambang signifikansi |slope| (perubahan frekuensi abnormal per menit) yang
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

    # ✅ Durasi segmen audio 5 detik sesuai INTEGRATION_CONTRACT.md §4.1.
    AUDIO_SEGMENT_DURATION_MS = 5_000
    # One FIFO worker; eight queued 5s/16k int16 segments use ~1.28 MB PCM.
    AUDIO_QUEUE_CAPACITY = int(os.environ.get("AUDIO_QUEUE_CAPACITY", "8"))
    AUDIO_QUEUE_MAX_WAIT_SECONDS = float(os.environ.get("AUDIO_QUEUE_MAX_WAIT_SECONDS", "10"))
    AUDIO_MAX_DEVICES = int(os.environ.get("AUDIO_MAX_DEVICES", "8"))
    # Clean up half-open sockets after an ESP reboot; client pings alone cannot
    # clean a server socket whose client disappeared without FIN.
    SOCK_SERVER_OPTIONS = {"max_message_size": 260000, "ping_interval": 20}

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
    # "random": probabilitas 2-kelas acak tiap segmen.
    # "abnormal_rising": probabilitas kelas "abnormal" naik bertahap untuk demo trend analysis.
    MOCK_INFERENCE_SCENARIO = os.environ.get("MOCK_INFERENCE_SCENARIO", "random")

    # Operational freshness budget: three normal 15-second PPG windows.
    # This is not a clinical threshold; old values remain in history only.
    VITAL_ALERT_MAX_AGE_SECONDS = float(os.environ.get("VITAL_ALERT_MAX_AGE_SECONDS", "45"))
    # Transport/ADC limits, not clinical thresholds. Keep compatibility with
    # firmware batch100 and legacy test/simulator batches up to2000 samples.
    PPG_MAX_BATCH_SAMPLES = 2000
    PPG_MAX_SAMPLE_RATE_HZ = 1000
    PPG_MAX_SAMPLE_VALUE = 4294967295
    MQTT_MAX_PAYLOAD_BYTES = 262144


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
    # 🧩 Jendela (detik) di mana alert dengan level & trigger yang sama tidak dibuat ulang walau
    # alert sebelumnya sudah ditinjau — mencegah alert fatigue dari evaluasi tiap segmen 5 detik.
    # Alert yang BELUM ditinjau selalu menahan duplikatnya tanpa batas waktu. PARAMETER TUNING
    # SISTEM, bukan nilai medis; tidak diatur di dokumen tim, perlu disepakati.
    ALERT_REPEAT_COOLDOWN_SECONDS = 600  # TODO_CLINICAL_VALUE (parameter tuning, bukan medis)
    LEVEL1_MARGIN_SPO2_ABS = 2  # TODO_CLINICAL_VALUE — poin persentase SpO2 (parameter satu-sisi, hanya min)

    # --- ML service 2 kelas (HTTP) ---
    # Kosongkan ML_SERVICE_URL untuk memaksa mock_inference tanpa koneksi HTTP (dipakai di test).
    ML_SERVICE_URL = os.environ.get("ML_SERVICE_URL", "http://127.0.0.1:8000")
    ML_SERVICE_TIMEOUT_SECONDS = float(os.environ.get("ML_SERVICE_TIMEOUT_SECONDS", "30"))
    ML_SERVICE_MODEL_VERSION = os.environ.get("ML_SERVICE_MODEL_VERSION", "efficientnet_b0_v1.0")

    # Technical short-window capture experiment, not a validated clinical interval.
    AUDIO_PERIODIC_CAPTURE_MS = 2000
    # Permit the previous firmware during a coordinated upgrade; never join windows.
    AUDIO_PERIODIC_COMPAT_CAPTURE_MS = (500,)
    AUDIO_CAPTURE_DIRECTORY = os.environ.get("AUDIO_CAPTURE_DIRECTORY", "backend/audio_captures")
    AUDIO_CAPTURE_QUOTA_BYTES = int(os.environ.get("AUDIO_CAPTURE_QUOTA_BYTES", "67108864"))
    AUDIO_SHORT_CAPTURE_INFERENCE_ENABLED = False
    # Experimental predictions are isolated from clinical history and alerts.
    AUDIO_PERIODIC_SHADOW_INFERENCE_ENABLED = os.environ.get(
        'AUDIO_PERIODIC_SHADOW_INFERENCE_ENABLED', '0') == '1'
    # Prototype notifications with same-channel persistence escalation.
    # Enabled for the prototype demo after real-model integration verification.
    # Set 0 for archive/shadow-only diagnostics. No mock notification fallback.
    AUDIO_PERIODIC_PATIENT_ALERTS_ENABLED = os.environ.get(
        'AUDIO_PERIODIC_PATIENT_ALERTS_ENABLED', '1') == '1'
    # Engineering persistence settings, not validated clinical severity cutoffs.
    AUDIO_PERIODIC_WARNING_CONSECUTIVE = int(os.environ.get(
        'AUDIO_PERIODIC_WARNING_CONSECUTIVE', '2'))  # TODO_CLINICAL_VALUE
    AUDIO_PERIODIC_URGENT_CONSECUTIVE = int(os.environ.get(
        'AUDIO_PERIODIC_URGENT_CONSECUTIVE', '3'))  # TODO_CLINICAL_VALUE
    AUDIO_PERIODIC_STREAK_MAX_GAP_SECONDS = float(os.environ.get(
        'AUDIO_PERIODIC_STREAK_MAX_GAP_SECONDS', '60'))  # availability, not medical
