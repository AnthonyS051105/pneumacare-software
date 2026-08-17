"""Adaptasi `process_wav_to_segments` (ai_reference/model.py) untuk menerima audio
buffer dari memori (int16 PCM hasil rakitan chunk websocket), bukan file .wav dari
disk — SDD_SOFTWARE.md §5.

Logika inti (normalisasi amplitude, resample ke 22000 Hz, ekstraksi mel-spectrogram
50 filterbank/window 512/175 baris frekuensi pertama) TETAP PERSIS SAMA dengan
`ai_reference/model.py` — bagian yang diganti HANYA cara data audio masuk (array
in-memory, bukan `scipy.io.wavfile.read(file_path)`).

⚠️ Urutan operasi (dikonfirmasi Tony, 2026-08-17): resample dilakukan SEKALI atas
seluruh segmen 5 detik di SAMPLE RATE ASLI FIRMWARE, BUKAN per-chunk kecil sebelum
diakumulasi — ini paling dekat secara matematis dengan `process_wav_to_segments`
asli (yang resample 1x untuk keseluruhan file), menghindari edge effect resample
berulang di titik sambungan antar chunk. Tanggung jawab pemanggilan resample-sekali
ini ada di caller (lihat `ingestion/audio_segment_buffer.py` — akumulasi di sample
rate asli, BUKAN 22000 Hz).
"""

import numpy as np
import scipy.signal
import torch

from ai_reference.model import FFT2MelSpectrogram

TARGET_SAMPLE_RATE = 22000
SEGMENT_DURATION_S = 5
N_MEL_FILTERBANKS = 50
N_WINDOW = 512
N_FREQUENCY_ROWS = 175


def pcm_int16_to_float32(pcm_samples: list[int]) -> np.ndarray:
    """Normalisasi PCM int16 ke float32 range [-1.0, 1.0].

    Persis logic cabang `data.dtype == np.int16` di `process_wav_to_segments`
    (`model.py` baris 82-83) — INTEGRATION_CONTRACT.md §2.3 menetapkan PCM firmware
    SELALU int16 little-endian, jadi cabang dtype lain (uint8/int32/fallback) di
    kode asli tidak relevan di sini dan sengaja tidak direplikasi.
    """
    array = np.asarray(pcm_samples, dtype=np.float32)
    return array / 32768.0


def resample_to_target_rate(data: np.ndarray, source_rate: int, target_rate: int = TARGET_SAMPLE_RATE) -> np.ndarray:
    """Resample via interpolasi linear — PERSIS `process_wav_to_segments` (`model.py`
    baris 104-107), termasuk penggunaan `np.linspace(0, 100, ...)` sebagai sumbu
    interpolasi (bukan sumbu waktu sungguhan dalam detik) — detail ini dipertahankan
    apa adanya karena mengubahnya akan membuat hasil resample tidak identik dengan
    yang dipakai saat training model.
    """
    if source_rate == target_rate:
        return data
    x_original = np.linspace(0, 100, len(data))
    x_resampled = np.linspace(0, 100, int(len(data) * (target_rate / source_rate)))
    return np.interp(x_resampled, x_original, data).astype(np.float32)


def segment_to_mel_tensor(segment_audio: np.ndarray, sample_rate: int = TARGET_SAMPLE_RATE) -> torch.Tensor:
    """Ekstraksi mel-spectrogram dari satu segmen audio (SUDAH di-resample ke
    `sample_rate`, SUDAH dipotong/di-pad ke durasi 5 detik oleh caller) — persis
    logic di dalam loop `while` `process_wav_to_segments` (`model.py` baris 128-135),
    disalin apa adanya minus bagian baca-file/chunking (itu tanggung jawab
    `ingestion/audio_segment_buffer.py`).

    Return tensor shape `[1, 1, 50, T]` — siap dikirim langsung ke `RespiratoryMobileNet`
    (normalisasi ImageNet + auto-repeat channel 1->3 sudah ditangani di dalam `forward()`
    model, SDD_SOFTWARE.md §5 — TIDAK perlu diulang di sini).
    """
    f, t, Sxx = scipy.signal.spectrogram(segment_audio, fs=sample_rate, nfft=N_WINDOW, nperseg=N_WINDOW)
    Sxx = Sxx[:N_FREQUENCY_ROWS, :]
    mel_spec = FFT2MelSpectrogram(f[:N_FREQUENCY_ROWS], Sxx, sample_rate, n_filterbanks=N_MEL_FILTERBANKS)
    return torch.from_numpy(mel_spec).permute(2, 0, 1).unsqueeze(0).float()


def pad_or_truncate(data: np.ndarray, target_length_samples: int) -> np.ndarray:
    """Pad dengan nol di akhir bila lebih pendek, potong bila lebih panjang —
    persis logic padding di `process_wav_to_segments` (`model.py` baris 122-126).
    Segmen dari `AudioSegmentBuffer` seharusnya SELALU pas 5 detik (buffer baru
    di-flush setelah genap), tapi fungsi ini tetap defensif untuk kasus tepi
    (mis. segmen terakhir sebelum device disconnect, lebih pendek dari 5 detik).
    """
    if len(data) == target_length_samples:
        return data
    if len(data) > target_length_samples:
        return data[:target_length_samples]
    padded = np.zeros(target_length_samples, dtype=np.float32)
    padded[: len(data)] = data
    return padded


def preprocess_segment(pcm_samples: list[int], source_sample_rate: int) -> torch.Tensor:
    """Entry point utama — dari PCM int16 mentah (sample rate ASLI firmware, SUDAH
    diakumulasi jadi ~5 detik oleh AudioSegmentBuffer) ke tensor mel-spectrogram
    siap-inference. Menggabungkan seluruh langkah di atas sesuai urutan
    `process_wav_to_segments` asli: normalisasi -> resample -> pad/truncate -> mel-spectrogram.
    """
    float_audio = pcm_int16_to_float32(pcm_samples)
    resampled = resample_to_target_rate(float_audio, source_sample_rate, TARGET_SAMPLE_RATE)
    target_length_samples = int(SEGMENT_DURATION_S * TARGET_SAMPLE_RATE)
    padded = pad_or_truncate(resampled, target_length_samples)
    return segment_to_mel_tensor(padded, TARGET_SAMPLE_RATE)
