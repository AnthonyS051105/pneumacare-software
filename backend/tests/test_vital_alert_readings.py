"""Quality/freshness rule shared by audio and PPG alerts; values are fixtures."""
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest

from backend.vitals.alert_readings import vitals_for_alert

NOW = datetime(2026,10,28,6,0,tzinfo=timezone.utc)


def reading(**overrides):
    values = dict(timestamp=NOW,hr=75,spo2=97,rr=16,
                  hr_confidence='good',spo2_confidence='good',rr_confidence='good')
    return SimpleNamespace(**(values | overrides))


def test_fresh_good_values_pass_without_transforming_them():
    result = vitals_for_alert(reading(),45,now=NOW)
    assert (result.hr,result.spo2,result.rr) == (75,97,16)


@pytest.mark.parametrize('quality',['poor',None,'unknown','GOOD'])
def test_each_metric_requires_explicit_good_quality(quality):
    result = vitals_for_alert(reading(hr_confidence=quality,rr_confidence=quality),45,now=NOW)
    assert result.hr is None and result.rr is None
    assert result.spo2 == 97


@pytest.mark.parametrize('seconds',[-1,46,86400])
def test_future_or_stale_readings_are_not_used(seconds):
    result = vitals_for_alert(reading(timestamp=NOW-timedelta(seconds=seconds)),45,now=NOW)
    assert (result.hr,result.spo2,result.rr) == (None,None,None)


def test_sqlite_naive_utc_and_max_age_boundary_are_supported():
    value = reading(timestamp=(NOW-timedelta(seconds=45)).replace(tzinfo=None))
    assert vitals_for_alert(value,45,now=NOW).hr == 75


@pytest.mark.parametrize('value',[float('nan'),float('inf'),float('-inf'),True,None])
def test_invalid_metric_cannot_reach_alert_engine(value):
    assert vitals_for_alert(reading(hr=value),45,now=NOW).hr is None


def test_absent_reading_is_safe():
    result = vitals_for_alert(None,45,now=NOW)
    assert (result.hr,result.spo2,result.rr) == (None,None,None)


@pytest.mark.parametrize('max_age',[0,-1,float('nan'),float('inf')])
def test_invalid_freshness_configuration_is_rejected(max_age):
    with pytest.raises(ValueError):
        vitals_for_alert(reading(),max_age,now=NOW)
