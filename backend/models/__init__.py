from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from backend.models.user import User  # noqa: E402,F401
from backend.models.patient import Patient  # noqa: E402,F401
from backend.models.device import Device, DeviceStatusLog, DevicePairingCode  # noqa: E402,F401
from backend.models.vital import ReadingVital  # noqa: E402,F401
from backend.models.classification import ReadingClassification  # noqa: E402,F401
from backend.models.trend import TrendEvent  # noqa: E402,F401
from backend.models.alert import Alert  # noqa: E402,F401
from backend.models.threshold import Threshold  # noqa: E402,F401
