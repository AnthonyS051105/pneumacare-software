import os

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


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

    # Durasi segmen audio yang dibutuhkan modul inference (FR-SW-002, INTEGRATION_CONTRACT.md §2.2).
    AUDIO_SEGMENT_DURATION_MS = 10_000

    # ⚠️ Nilai diusulkan di SRS_SOFTWARE.md FR-SW-004, belum divalidasi tim — timeout heartbeat
    # MQTT status sebelum device ditandai offline.
    DEVICE_OFFLINE_TIMEOUT_SECONDS = 30  # TODO_CLINICAL_VALUE (nilai operasional, bukan medis, tapi tetap diusulkan)

    # TODO_AUTH_NOT_IMPLEMENTED: INTEGRATION_CONTRACT.md §6 mengusulkan static bearer token untuk
    # autentikasi device (websocket + MQTT). Belum diimplementasikan di Fase 1 — websocket dan MQTT
    # subscriber saat ini menerima semua koneksi tanpa verifikasi token. Jangan anggap ini aman untuk
    # deployment di luar jaringan lokal demo.
    DEVICE_AUTH_TOKEN = os.environ.get("DEVICE_AUTH_TOKEN", "")

    # mock_inference.py (FR-SW-013) — skenario dummy yang dipakai.
    # "random": wheeze/crackle present dengan probabilitas rendah acak tiap segmen.
    # "wheeze_rising": confidence wheeze naik bertahap tiap segmen berturut-turut, untuk demo trend analysis.
    MOCK_INFERENCE_SCENARIO = os.environ.get("MOCK_INFERENCE_SCENARIO", "random")

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
