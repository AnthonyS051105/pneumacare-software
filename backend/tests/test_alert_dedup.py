from datetime import datetime, timedelta

from backend.alerting.alert_engine import ExistingAlert, is_repeat_alert, trigger_signature

NOW = datetime(2026, 10, 22, 12, 0)
HR_LOW = [{"type": "vital_threshold", "parameter": "hr", "value": 78, "threshold": 100, "severity": "breach"}]


def _old(level=2, triggers=HR_LOW, acknowledged=False, minutes_ago=1):
    return ExistingAlert(level=level, triggers=triggers, acknowledged=acknowledged, created_at=NOW - timedelta(minutes=minutes_ago))


def test_signature_ignores_value():
    other_value = [{**HR_LOW[0], "value": 70}]
    assert trigger_signature(HR_LOW) == trigger_signature(other_value)


def test_same_open_alert_is_repeat_regardless_of_age():
    assert is_repeat_alert(2, HR_LOW, [_old(minutes_ago=600)], NOW, cooldown_seconds=600)


def test_acknowledged_alert_within_cooldown_is_repeat():
    assert is_repeat_alert(2, HR_LOW, [_old(acknowledged=True, minutes_ago=5)], NOW, cooldown_seconds=600)


def test_acknowledged_alert_after_cooldown_is_new():
    assert not is_repeat_alert(2, HR_LOW, [_old(acknowledged=True, minutes_ago=11)], NOW, cooldown_seconds=600)


def test_escalation_to_higher_level_is_never_suppressed():
    assert not is_repeat_alert(3, HR_LOW, [_old(level=2)], NOW, cooldown_seconds=600)


def test_different_parameter_is_new_alert():
    spo2 = [{"type": "vital_threshold", "parameter": "spo2", "value": 91, "threshold": 92, "severity": "breach"}]
    assert not is_repeat_alert(2, spo2, [_old()], NOW, cooldown_seconds=600)


def test_near_vs_breach_are_different_conditions():
    near = [{**HR_LOW[0], "severity": "near"}]
    assert not is_repeat_alert(2, near, [_old()], NOW, cooldown_seconds=600)


def test_no_existing_alerts():
    assert not is_repeat_alert(2, HR_LOW, [], NOW, cooldown_seconds=600)
