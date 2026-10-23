from backend.inference.inference_service import CLASS_NAMES
from backend.inference.mock_inference import reset_rising_state, run_mock_inference


def _run(device_id="d", channel_id=1, scenario="random"):
    return run_mock_inference(
        pcm_samples=[0] * 100,
        device_id=device_id,
        channel_id=channel_id,
        segment_start_ms=0,
        segment_end_ms=5000,
        scenario=scenario,
    )


def test_output_schema():
    result = _run()
    classification = result["classification"]

    assert set(classification) == {"predicted_class", "confidence", "probabilities"}
    assert classification["predicted_class"] in CLASS_NAMES
    assert 0.0 <= classification["confidence"] <= 1.0
    assert set(classification["probabilities"]) == set(CLASS_NAMES)
    assert abs(sum(classification["probabilities"].values()) - 1.0) < 1e-3


def test_abnormal_rising_increases_abnormal_probability():
    reset_rising_state()
    values = [
        _run(scenario="abnormal_rising")["classification"]["probabilities"]["abnormal"]
        for _ in range(5)
    ]

    assert values == sorted(values)
    assert values[-1] > values[0]


def test_abnormal_rising_eventually_predicts_abnormal():
    reset_rising_state()
    result = None
    for _ in range(40):
        result = _run(scenario="abnormal_rising")

    assert result["classification"]["predicted_class"] == "abnormal"


def test_abnormal_rising_state_is_per_channel():
    reset_rising_state()
    for _ in range(5):
        _run(device_id="d", channel_id=1, scenario="abnormal_rising")

    other_channel = _run(device_id="d", channel_id=2, scenario="abnormal_rising")

    assert other_channel["classification"]["probabilities"]["abnormal"] < 0.2
