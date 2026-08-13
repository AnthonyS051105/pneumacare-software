from backend.inference.mock_inference import reset_rising_state, run_mock_inference


def test_random_scenario_output_schema():
    result = run_mock_inference(
        pcm_samples=[1, 2, 3],
        device_id="pneumacare-a1b2",
        channel_id=1,
        segment_start_ms=1000,
        segment_end_ms=11000,
        scenario="random",
    )

    assert result["device_id"] == "pneumacare-a1b2"
    assert result["channel_id"] == 1
    assert result["segment_start_ms"] == 1000
    assert result["segment_end_ms"] == 11000
    assert result["model_version"] == "mock_v1"
    assert "segment_id" in result

    prediction = result["prediction"]
    assert set(prediction.keys()) == {"wheeze", "crackle", "severity_class"}
    assert set(prediction["wheeze"].keys()) == {"present", "confidence"}
    assert set(prediction["crackle"].keys()) == {"present", "confidence"}
    assert 0.0 <= prediction["wheeze"]["confidence"] <= 1.0
    assert 0.0 <= prediction["crackle"]["confidence"] <= 1.0
    assert prediction["severity_class"] == "TODO_CONFIRM_WITH_NATHANAEL"


def test_wheeze_rising_scenario_increases_confidence():
    reset_rising_state()
    device_id, channel_id = "pneumacare-a1b2", 1

    confidences = []
    for i in range(5):
        result = run_mock_inference(
            pcm_samples=[],
            device_id=device_id,
            channel_id=channel_id,
            segment_start_ms=i * 10_000,
            segment_end_ms=(i + 1) * 10_000,
            scenario="wheeze_rising",
        )
        confidences.append(result["prediction"]["wheeze"]["confidence"])

    assert confidences == sorted(confidences)
    assert confidences[-1] > confidences[0]


def test_wheeze_rising_scenario_state_is_per_channel():
    reset_rising_state()
    run_mock_inference(
        pcm_samples=[],
        device_id="pneumacare-a1b2",
        channel_id=1,
        segment_start_ms=0,
        segment_end_ms=10_000,
        scenario="wheeze_rising",
    )
    result_ch2 = run_mock_inference(
        pcm_samples=[],
        device_id="pneumacare-a1b2",
        channel_id=2,
        segment_start_ms=0,
        segment_end_ms=10_000,
        scenario="wheeze_rising",
    )
    # channel 2 belum pernah dipanggil sebelumnya, harus mulai dari state awal (bukan lanjut ch1)
    assert result_ch2["prediction"]["wheeze"]["confidence"] < 0.2
