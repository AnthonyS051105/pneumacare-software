"""Audio-triggered alert checks use persisted per-metric confidence and age."""
from datetime import datetime,timedelta,timezone

import numpy as np
import pytest

from backend.analysis.cycle_segmenter import CycleDetectionResult
from backend.ingestion import websocket_server as audio
from backend.ingestion.audio_segment_buffer import Segment
from backend.models import db
from backend.models.alert import Alert
from backend.models.threshold import Threshold
from backend.models.vital import ReadingVital
from backend.tests.test_patient_routes import _seed_patient_with_device


@pytest.mark.parametrize('quality,age,expected',[
    ('good',0,1),('poor',0,0),(None,0,0),('unknown',0,0),('good',60,0),('good',-60,0),
])
def test_audio_alert_requires_fresh_explicitly_trusted_vital(app,monkeypatch,quality,age,expected):
    _seed_patient_with_device(app)
    monkeypatch.setattr(audio,'detect_cycle_slices',lambda *args:CycleDetectionResult(status='no_cycles'))
    now=datetime.now(timezone.utc)
    with app.app_context():
        db.session.add(Threshold(patient_id='patient-1',hr_min=60,hr_max=100))
        db.session.add(ReadingVital(device_id='pneumacare-a1b2',timestamp=now-timedelta(seconds=age),
                                   hr=25,hr_confidence=quality,spo2=None))
        db.session.commit()
        epoch=int(now.timestamp()*1000)
        audio._handle_segment(Segment('pneumacare-a1b2',1,epoch-5000,epoch,np.zeros(80000,dtype=np.int16),16000))
        assert Alert.query.count()==expected
