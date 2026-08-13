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

    # 🔓 Ambang signifikansi tren — domain Nathanael, menunggu konfirmasi.
    TREND_SIGNIFICANCE_THRESHOLD_DEFAULT = None  # TODO_NATHANAEL_CONFIRM

    # 🔓 Ukuran rolling window trend analysis — menunggu konfirmasi Nathanael.
    TREND_ROLLING_WINDOW_SIZE = None  # TODO_NATHANAEL_CONFIRM
