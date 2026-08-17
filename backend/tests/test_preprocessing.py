import numpy as np
import torch

from backend.inference.preprocessing import (
    TARGET_SAMPLE_RATE,
    N_MEL_FILTERBANKS,
    pad_or_truncate,
    pcm_int16_to_float32,
    preprocess_segment,
    resample_to_target_rate,
    segment_to_mel_tensor,
)


def test_pcm_int16_to_float32_normalizes_to_unit_range():
    samples = [0, 32767, -32768, 16384]
    result = pcm_int16_to_float32(samples)

    assert result.dtype == np.float32
    assert result[0] == 0.0
    assert abs(result[1] - (32767 / 32768.0)) < 1e-6
    assert result[2] == -1.0
    assert abs(result[3] - 0.5) < 1e-6


def test_resample_to_target_rate_noop_when_same_rate():
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    result = resample_to_target_rate(data, source_rate=22000, target_rate=22000)
    assert np.array_equal(result, data)


def test_resample_to_target_rate_changes_length_proportionally():
    # 1 detik di 16000 Hz -> harus jadi ~1 detik di 22000 Hz (panjang bertambah)
    data = np.zeros(16000, dtype=np.float32)
    result = resample_to_target_rate(data, source_rate=16000, target_rate=22000)
    assert len(result) == int(16000 * (22000 / 16000))


def test_pad_or_truncate_pads_short_signal_with_zeros():
    data = np.array([1.0, 2.0, 3.0], dtype=np.float32)
    result = pad_or_truncate(data, target_length_samples=5)

    assert len(result) == 5
    assert list(result[:3]) == [1.0, 2.0, 3.0]
    assert list(result[3:]) == [0.0, 0.0]


def test_pad_or_truncate_truncates_long_signal():
    data = np.array([1.0, 2.0, 3.0, 4.0, 5.0], dtype=np.float32)
    result = pad_or_truncate(data, target_length_samples=3)
    assert list(result) == [1.0, 2.0, 3.0]


def test_pad_or_truncate_returns_same_array_when_exact_length():
    data = np.array([1.0, 2.0], dtype=np.float32)
    result = pad_or_truncate(data, target_length_samples=2)
    assert list(result) == [1.0, 2.0]


def test_segment_to_mel_tensor_shape():
    duration_s = 5
    t = np.linspace(0, duration_s, duration_s * TARGET_SAMPLE_RATE, dtype=np.float32)
    signal = np.sin(2 * np.pi * 440 * t).astype(np.float32)  # tone 440Hz sintetis

    tensor = segment_to_mel_tensor(signal, sample_rate=TARGET_SAMPLE_RATE)

    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape[0] == 1  # batch
    assert tensor.shape[1] == 1  # channel (sebelum auto-repeat di forward() model)
    assert tensor.shape[2] == N_MEL_FILTERBANKS  # 50 mel filterbank


def test_preprocess_segment_end_to_end_produces_valid_tensor():
    # 5 detik audio di sample rate asli firmware (16000 Hz, BUKAN 22000 target)
    n_samples = 16000 * 5
    pcm_samples = [int(1000 * np.sin(2 * np.pi * 300 * i / 16000)) for i in range(n_samples)]

    tensor = preprocess_segment(pcm_samples, source_sample_rate=16000)

    assert isinstance(tensor, torch.Tensor)
    assert tensor.shape[0] == 1
    assert tensor.shape[1] == 1
    assert tensor.shape[2] == N_MEL_FILTERBANKS
    assert not torch.isnan(tensor).any()


def test_preprocess_segment_handles_shorter_than_5_seconds():
    # segmen tepi (mis. device disconnect sebelum genap 5 detik) — harus di-pad, bukan error
    n_samples = 16000 * 3
    pcm_samples = [0] * n_samples

    tensor = preprocess_segment(pcm_samples, source_sample_rate=16000)

    assert tensor.shape[2] == N_MEL_FILTERBANKS
