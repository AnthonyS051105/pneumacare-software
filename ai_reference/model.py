import torch
import torch.nn as nn
from torchvision.models import mobilenet_v3_small
import numpy as np
import scipy.signal
import wave
import scipy.io.wavfile as wf

class RespiratoryMobileNet(nn.Module):
    def __init__(self, num_classes=4):
        super().__init__()
        backbone = mobilenet_v3_small(weights=None)
        
        self.register_buffer('mean', torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer('std', torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

        in_features = backbone.classifier[-1].in_features
        backbone.classifier[-1] = nn.Linear(in_features, num_classes)
        self.model = backbone

    def forward(self, x):
        if x.shape[1] == 1:
            x = x.repeat(1, 3, 1, 1)
        x = (x - self.mean) / self.std
        return self.model(x)


# --- Fungsi Preprocessing & Mel-Spectrogram ---
def Freq2Mel(freq):
    return 1125 * np.log(1 + freq / 700)

def Mel2Freq(mel):
    return 700 * (np.exp(mel / 1125) - 1)

def GenerateMelFilterBanks(mel_space_freq, fft_bin_frequencies):
    n_filters = len(mel_space_freq) - 2
    coeff = []
    for mel_index in range(n_filters):
        m = int(mel_index + 1)
        filter_bank = []
        for f in fft_bin_frequencies:
            if(f < mel_space_freq[m-1]):
                hm = 0
            elif(f < mel_space_freq[m]):
                hm = (f - mel_space_freq[m-1]) / (mel_space_freq[m] - mel_space_freq[m-1])
            elif(f < mel_space_freq[m + 1]):
                hm = (mel_space_freq[m+1] - f) / (mel_space_freq[m + 1] - mel_space_freq[m])
            else:
                hm = 0
            filter_bank.append(hm)
        coeff.append(filter_bank)
    return np.array(coeff, dtype = np.float32)

def FFT2MelSpectrogram(f, Sxx, sample_rate, n_filterbanks=50):
    (max_mel, min_mel)  = (Freq2Mel(max(f)), Freq2Mel(min(f)))
    mel_bins = np.linspace(min_mel, max_mel, num = (n_filterbanks + 2))
    mel_freq = Mel2Freq(mel_bins)
    filter_banks = GenerateMelFilterBanks(mel_freq, f)
    mel_spectrum = np.matmul(filter_banks, Sxx)
    mel_log = np.log10(mel_spectrum + float(10e-12))
    
    mel_min = np.min(mel_log)
    mel_max = np.max(mel_log)
    diff = mel_max - mel_min
    norm_mel_log = (mel_log - mel_min) / diff if (diff > 0) else np.zeros(shape = (n_filterbanks, Sxx.shape[1]))
    return np.reshape(norm_mel_log, (n_filterbanks, Sxx.shape[1], 1)).astype(np.float32)

def process_wav_to_segments(file_path, target_rate=22000, desired_length=5, overlap=0.0):
    if overlap >= desired_length:
        raise ValueError(f"Nilai overlap ({overlap} detik) harus lebih kecil dari desired_length ({desired_length} detik)")

    rate, data = wf.read(file_path)

    # Menangani stereo/multi-channel dengan konversi ke mono
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    # Normalisasi data audio ke float32 range [-1.0, 1.0]
    if np.issubdtype(data.dtype, np.integer):
        if data.dtype == np.uint8:
            data = (data.astype(np.float32) - 128.0) / 128.0
        elif data.dtype == np.int16:
            data = data.astype(np.float32) / 32768.0
        elif data.dtype == np.int32:
            data = data.astype(np.float32) / 2147483648.0
        else:
            try:
                wav = wave.open(file_path, mode='r')
                sampwidth = wav.getsampwidth()
                wav.close()
                if sampwidth == 1:
                    data = (data.astype(np.float32) - 128.0) / 128.0
                elif sampwidth == 2:
                    data = data.astype(np.float32) / 32768.0
                else:
                    data = data.astype(np.float32) / 2147483648.0
            except Exception:
                max_val = np.max(np.abs(data))
                data = data.astype(np.float32) / max_val if max_val > 0 else data.astype(np.float32)
    else:
        data = data.astype(np.float32)

    # Resample jika rate berbeda
    if rate != target_rate:
        x_original = np.linspace(0, 100, len(data))
        x_resampled = np.linspace(0, 100, int(len(data) * (target_rate / rate)))
        data = np.interp(x_resampled, x_original, data).astype(np.float32)

    chunk_samples = int(desired_length * target_rate)
    step_samples = int((desired_length - overlap) * target_rate)
    total_samples = len(data)
    segments = []

    start_idx = 0
    while start_idx < total_samples:
        end_idx = min(start_idx + chunk_samples, total_samples)
        chunk = data[start_idx:end_idx]
        
        start_time = start_idx / target_rate
        end_time = end_idx / target_rate

        # Padding jika chunk kurang dari 5 detik
        if len(chunk) < chunk_samples:
            padded_chunk = np.zeros(chunk_samples, dtype=np.float32)
            padded_chunk[:len(chunk)] = chunk
            chunk = padded_chunk

        # Ekstraksi Mel-Spectrogram
        n_window = 512
        n_rows = 175
        f, t, Sxx = scipy.signal.spectrogram(chunk, fs=target_rate, nfft=n_window, nperseg=n_window)
        Sxx = Sxx[:n_rows, :]
        mel_spec = FFT2MelSpectrogram(f[:n_rows], Sxx, target_rate)
        
        tensor_x = torch.from_numpy(mel_spec).permute(2, 0, 1).unsqueeze(0).float()
        segments.append((tensor_x, round(start_time, 2), round(end_time, 2)))

        if end_idx == total_samples:
            break

        start_idx += step_samples

    return segments