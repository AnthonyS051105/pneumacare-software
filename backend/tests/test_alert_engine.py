from datetime import datetime

from backend.alerting.alert_engine import (
    Thresholds,
    VitalReading,
    compute_trend_persistence,
    determine_alert_level,
    evaluate_alert,
    evaluate_vitals,
    make_trend_trigger,
)
from backend.trend_analysis.trend_detector import TrendResult

MIN_CONSECUTIVE = 3
SIGNIFICANCE_THRESHOLD = 0.05
LEVEL1_MARGIN_PCT = 0.10
LEVEL1_MARGIN_SPO2_ABS = 2

# HR: rentang 60-100, margin 10% = 4 -> near [60,64) dan (96,100], breach <60 atau >100.
# RR: rentang 12-20, margin 10% = 0.8 -> near [12,12.8) dan (19.2,20], breach <12 atau >20.
# SpO2: min=92, margin_abs=2 -> near [92,94), breach <92.
FULL_THRESHOLDS = Thresholds(hr_min=60, hr_max=100, spo2_min=92, rr_min=12, rr_max=20)
NO_THRESHOLDS = Thresholds(hr_min=None, hr_max=None, spo2_min=None, rr_min=None, rr_max=None)


def _trend_result(slope: float, significant: bool) -> TrendResult:
    return TrendResult(
        window_start=datetime(2026, 1, 1, 8, 0),
        window_end=datetime(2026, 1, 1, 8, 5),
        slope=slope,
        significant=significant,
    )


def _eval_vitals(vitals: VitalReading, thresholds: Thresholds = FULL_THRESHOLDS):
    return evaluate_vitals(vitals, thresholds, LEVEL1_MARGIN_PCT, LEVEL1_MARGIN_SPO2_ABS)


def _eval_alert(vitals, trend_result, recent_flags, thresholds=FULL_THRESHOLDS, min_consecutive=MIN_CONSECUTIVE):
    return evaluate_alert(
        vitals,
        trend_result=trend_result,
        recent_trend_significant_flags=recent_flags,
        thresholds=thresholds,
        trend_significance_threshold=SIGNIFICANCE_THRESHOLD,
        min_consecutive=min_consecutive,
        level1_margin_pct=LEVEL1_MARGIN_PCT,
        level1_margin_spo2_abs=LEVEL1_MARGIN_SPO2_ABS,
    )


# --- evaluate_vitals: breach ---


def test_evaluate_vitals_no_violation_returns_empty():
    vitals = VitalReading(hr=75, spo2=97, rr=16)
    assert _eval_vitals(vitals) == []


def test_evaluate_vitals_hr_below_min_is_breach():
    vitals = VitalReading(hr=50, spo2=97, rr=16)
    triggers = _eval_vitals(vitals)
    assert len(triggers) == 1
    assert triggers[0].parameter == "hr"
    assert triggers[0].value == 50
    assert triggers[0].threshold == 60
    assert triggers[0].severity == "breach"


def test_evaluate_vitals_hr_above_max_is_breach():
    vitals = VitalReading(hr=150, spo2=97, rr=16)
    triggers = _eval_vitals(vitals)
    assert len(triggers) == 1
    assert triggers[0].parameter == "hr"
    assert triggers[0].threshold == 100
    assert triggers[0].severity == "breach"


def test_evaluate_vitals_spo2_below_min_is_breach():
    vitals = VitalReading(hr=75, spo2=88, rr=16)
    triggers = _eval_vitals(vitals)
    assert len(triggers) == 1
    assert triggers[0].parameter == "spo2"
    assert triggers[0].severity == "breach"


def test_evaluate_vitals_multi_parameter_violation():
    vitals = VitalReading(hr=150, spo2=88, rr=16)
    triggers = _eval_vitals(vitals)
    parameters = {t.parameter for t in triggers}
    assert parameters == {"hr", "spo2"}
    assert all(t.severity == "breach" for t in triggers)


def test_evaluate_vitals_skips_parameter_when_threshold_is_none():
    vitals = VitalReading(hr=200, spo2=50, rr=100)
    assert evaluate_vitals(vitals, NO_THRESHOLDS, LEVEL1_MARGIN_PCT, LEVEL1_MARGIN_SPO2_ABS) == []


def test_evaluate_vitals_skips_parameter_when_vital_is_none():
    # RR belum tersedia (belum ada estimator) -> None -> tidak boleh crash atau trigger palsu
    vitals = VitalReading(hr=75, spo2=97, rr=None)
    triggers = _eval_vitals(vitals)
    assert triggers == []


# --- evaluate_vitals: near-threshold (Level 1) ---


def test_evaluate_vitals_value_far_from_threshold_no_trigger():
    # hr=75 jauh dari [60,64) dan (96,100] -> tidak ada trigger sama sekali
    vitals = VitalReading(hr=75, spo2=97, rr=16)
    assert _eval_vitals(vitals) == []


def test_evaluate_vitals_hr_within_near_margin_above_min():
    # hr=62 -> dalam [60, 64) -> near, bukan breach
    vitals = VitalReading(hr=62, spo2=97, rr=16)
    triggers = _eval_vitals(vitals)
    assert len(triggers) == 1
    assert triggers[0].parameter == "hr"
    assert triggers[0].severity == "near"
    assert triggers[0].threshold == 60


def test_evaluate_vitals_hr_within_near_margin_below_max():
    # hr=98 -> dalam (96, 100] -> near
    vitals = VitalReading(hr=98, spo2=97, rr=16)
    triggers = _eval_vitals(vitals)
    assert len(triggers) == 1
    assert triggers[0].severity == "near"
    assert triggers[0].threshold == 100


def test_evaluate_vitals_spo2_within_near_margin():
    # spo2=93 -> dalam [92, 94) -> near
    vitals = VitalReading(hr=75, spo2=93, rr=16)
    triggers = _eval_vitals(vitals)
    assert len(triggers) == 1
    assert triggers[0].parameter == "spo2"
    assert triggers[0].severity == "near"


def test_evaluate_vitals_rr_within_near_margin():
    # rr=20 tepat di threshold_max, rr=19.5 dalam (19.2, 20] -> near
    vitals = VitalReading(hr=75, spo2=97, rr=19.5)
    triggers = _eval_vitals(vitals)
    assert len(triggers) == 1
    assert triggers[0].parameter == "rr"
    assert triggers[0].severity == "near"


# --- compute_trend_persistence ---


def test_persistence_false_when_fewer_flags_than_min_consecutive():
    assert compute_trend_persistence([True, True], min_consecutive=MIN_CONSECUTIVE) is False


def test_persistence_true_when_last_n_all_significant():
    assert compute_trend_persistence([True, True, True], min_consecutive=MIN_CONSECUTIVE) is True


def test_persistence_true_when_extra_history_before_the_streak():
    assert compute_trend_persistence([False, True, True, True], min_consecutive=MIN_CONSECUTIVE) is True


def test_persistence_false_when_streak_broken_in_the_middle():
    # signifikan-tidak-signifikan-signifikan -> BUKAN 3x berturut-turut, streak reset
    assert compute_trend_persistence([True, False, True], min_consecutive=MIN_CONSECUTIVE) is False


# --- determine_alert_level ---


def test_zero_triggers_returns_none():
    assert determine_alert_level([], trend_persistent=False) is None


def test_only_near_trigger_is_level_1():
    vitals = VitalReading(hr=62, spo2=97, rr=16)  # near-threshold saja, tidak breach
    triggers = _eval_vitals(vitals)
    assert determine_alert_level(triggers, trend_persistent=False) == 1


def test_single_breach_trigger_is_level_2():
    vitals = VitalReading(hr=50, spo2=97, rr=16)
    triggers = _eval_vitals(vitals)
    assert determine_alert_level(triggers, trend_persistent=False) == 2


def test_single_trend_trigger_not_persistent_is_level_2():
    trigger = make_trend_trigger(_trend_result(slope=0.1, significant=True), SIGNIFICANCE_THRESHOLD)
    assert determine_alert_level([trigger], trend_persistent=False) == 2


def test_single_trend_trigger_persistent_is_level_3():
    trigger = make_trend_trigger(_trend_result(slope=0.1, significant=True), SIGNIFICANCE_THRESHOLD)
    assert determine_alert_level([trigger], trend_persistent=True) == 3


def test_multi_breach_trigger_is_level_3_regardless_of_persistence():
    vitals = VitalReading(hr=150, spo2=88, rr=16)
    triggers = _eval_vitals(vitals)
    assert len(triggers) == 2
    assert determine_alert_level(triggers, trend_persistent=False) == 3


def test_near_plus_breach_ignores_near_stays_level_2():
    # 1 near (hr) + 1 breach (spo2) -> breach mendominasi, near diabaikan dari perhitungan level -> level 2
    vitals = VitalReading(hr=62, spo2=88, rr=16)
    triggers = _eval_vitals(vitals)
    parameters = {(t.parameter, t.severity) for t in triggers}
    assert parameters == {("hr", "near"), ("spo2", "breach")}
    assert determine_alert_level(triggers, trend_persistent=False) == 2


def test_two_near_triggers_without_breach_still_level_1():
    # near tidak ikut dihitung untuk aturan >=2-trigger -> tetap level 1, bukan level 3
    vitals = VitalReading(hr=62, spo2=93, rr=16)
    triggers = _eval_vitals(vitals)
    assert len(triggers) == 2
    assert all(t.severity == "near" for t in triggers)
    assert determine_alert_level(triggers, trend_persistent=False) == 1


# --- evaluate_alert (end-to-end pure-function) ---


def test_evaluate_alert_no_violation_no_trend_returns_none():
    vitals = VitalReading(hr=75, spo2=97, rr=16)
    result = _eval_alert(vitals, _trend_result(slope=0.0, significant=False), [])
    assert result is None


def test_evaluate_alert_near_threshold_only_is_level_1():
    vitals = VitalReading(hr=62, spo2=97, rr=16)
    result = _eval_alert(vitals, _trend_result(slope=0.0, significant=False), [])
    assert result is not None
    assert result.level == 1
    assert len(result.triggers) == 1
    assert result.triggers[0].severity == "near"


def test_evaluate_alert_single_vital_violation_is_level_2():
    vitals = VitalReading(hr=50, spo2=97, rr=16)
    result = _eval_alert(vitals, _trend_result(slope=0.0, significant=False), [])
    assert result is not None
    assert result.level == 2
    assert len(result.triggers) == 1


def test_evaluate_alert_vital_plus_significant_trend_is_level_3():
    vitals = VitalReading(hr=50, spo2=88, rr=16)
    result = _eval_alert(vitals, _trend_result(slope=0.2, significant=True), [False])
    assert result is not None
    assert result.level == 3
    assert len(result.triggers) == 3  # hr + spo2 + trend_slope


def test_evaluate_alert_near_plus_breach_stays_level_2():
    vitals = VitalReading(hr=62, spo2=88, rr=16)
    result = _eval_alert(vitals, _trend_result(slope=0.0, significant=False), [])
    assert result is not None
    assert result.level == 2
    assert len(result.triggers) == 2


def test_evaluate_alert_trend_appears_once_stays_level_2():
    # Skenario user-request: trend_slope signifikan muncul 1x (belum ada riwayat) -> level 2
    vitals = VitalReading(hr=75, spo2=97, rr=16)  # tidak ada pelanggaran vital
    result = _eval_alert(vitals, _trend_result(slope=0.1, significant=True), [True])
    assert result is not None
    assert result.level == 2
    assert result.trend_persistent is False


def test_evaluate_alert_trend_three_times_consecutive_escalates_to_level_3():
    # Skenario user-request: trend_slope signifikan 3x berturut-turut -> level 3
    vitals = VitalReading(hr=75, spo2=97, rr=16)
    result = _eval_alert(vitals, _trend_result(slope=0.1, significant=True), [True, True, True])
    assert result is not None
    assert result.level == 3
    assert result.trend_persistent is True


def test_evaluate_alert_trend_broken_streak_stays_level_2():
    # Skenario user-request: 3x tapi terputus (signifikan-tidak-signifikan-signifikan)
    # -> TETAP level 2, streak-nya reset, bukan level 3
    vitals = VitalReading(hr=75, spo2=97, rr=16)
    result = _eval_alert(vitals, _trend_result(slope=0.1, significant=True), [True, False, True])
    assert result is not None
    assert result.level == 2
    assert result.trend_persistent is False


def test_evaluate_alert_none_trend_result_does_not_crash():
    # trend_result=None terjadi saat trend_detector belum punya cukup titik data
    vitals = VitalReading(hr=50, spo2=97, rr=16)
    result = _eval_alert(vitals, None, [])
    assert result is not None
    assert result.level == 2
    assert len(result.triggers) == 1
