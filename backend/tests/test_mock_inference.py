from backend.inference.inference_service import CLASS_NAMES
from backend.inference.mock_inference import reset_rising_state, run_mock_inference


def test_random_scenario_output_schema():
    result = run_mock_inference(
        pcm_samples=[1, 2, 3],
        device_id="pneumacare-a1b2",
        channel_id=1,
        segment_start_ms=1000,
        segment_end_ms=6000,
        scenario="random",
    )

    assert result["device_id"] == "pneumacare-a1b2"
    assert result["channel_id"] == 1
    assert result["segment_start_ms"] == 1000
    assert result["segment_end_ms"] == 6000
    assert result["model_version"] == "mock_v2"
    assert "segment_id" in result

    wheeze_crackle = result["wheeze_crackle"]
    assert set(wheeze_crackle.keys()) == {"predicted_class", "confidence", "probabilities"}
    assert wheeze_crackle["predicted_class"] in CLASS_NAMES
    assert 0.0 <= wheeze_crackle["confidence"] <= 1.0
    assert set(wheeze_crackle["probabilities"].keys()) == set(CLASS_NAMES)
    # toleransi 1e-3, bukan 1e-6 — nilai sudah dibulatkan ke 4 desimal di mock_inference.py,
    # akumulasi error pembulatan wajar sampai ~1e-4 saat dijumlahkan 4 angka.
    assert abs(sum(wheeze_crackle["probabilities"].values()) - 1.0) < 1e-3
    # predicted_class HARUS argmax dari probabilities
    assert wheeze_crackle["predicted_class"] == max(
        wheeze_crackle["probabilities"], key=wheeze_crackle["probabilities"].get
    )


def test_wheeze_rising_scenario_increases_wheeze_probability():
    reset_rising_state()
    device_id, channel_id = "pneumacare-a1b2", 1

    wheeze_probabilities = []
    for i in range(5):
        result = run_mock_inference(
            pcm_samples=[],
            device_id=device_id,
            channel_id=channel_id,
            segment_start_ms=i * 5_000,
            segment_end_ms=(i + 1) * 5_000,
            scenario="wheeze_rising",
        )
        wheeze_probabilities.append(result["wheeze_crackle"]["probabilities"]["wheeze"])

    assert wheeze_probabilities == sorted(wheeze_probabilities)
    assert wheeze_probabilities[-1] > wheeze_probabilities[0]


def test_wheeze_rising_scenario_eventually_predicts_wheeze():
    reset_rising_state()
    device_id, channel_id = "pneumacare-a1b2", 1

    result = None
    for i in range(20):
        result = run_mock_inference(
            pcm_samples=[],
            device_id=device_id,
            channel_id=channel_id,
            segment_start_ms=i * 5_000,
            segment_end_ms=(i + 1) * 5_000,
            scenario="wheeze_rising",
        )

    assert result["wheeze_crackle"]["predicted_class"] == "wheeze"


def test_wheeze_rising_scenario_state_is_per_channel():
    reset_rising_state()
    run_mock_inference(
        pcm_samples=[],
        device_id="pneumacare-a1b2",
        channel_id=1,
        segment_start_ms=0,
        segment_end_ms=5_000,
        scenario="wheeze_rising",
    )
    result_ch2 = run_mock_inference(
        pcm_samples=[],
        device_id="pneumacare-a1b2",
        channel_id=2,
        segment_start_ms=0,
        segment_end_ms=5_000,
        scenario="wheeze_rising",
    )
    # channel 2 belum pernah dipanggil sebelumnya, harus mulai dari state awal (bukan lanjut ch1)
    assert result_ch2["wheeze_crackle"]["probabilities"]["wheeze"] < 0.2
