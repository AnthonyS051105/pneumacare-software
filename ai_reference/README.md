# ai_reference/ — Source Code Asli dari Nathanael

File di folder ini **disalin langsung** dari repo `Respiratory-Detector` milik Nathanael (dikirim Tony 12 Agustus 2026), bukan ditulis ulang oleh Claude — supaya tidak ada risiko salah reproduksi detail numerik (terutama fungsi mel-spectrogram custom yang mudah salah kalau ditulis ulang manual).

## Isi

- **`model.py`** — definisi arsitektur `RespiratoryMobileNet` (MobileNetV3-Small, torchvision) + seluruh fungsi preprocessing (`process_wav_to_segments`, `FFT2MelSpectrogram`, dll). **Modul ini bisa dipakai langsung/di-import di backend**, tidak perlu ditulis ulang.
- **`detector_reference_standalone.py`** — kelas `Detector` asli Nael. **JANGAN dipakai apa adanya di backend** — ini didesain untuk load file `.wav` dari disk (`predict(wav_path)`), sedangkan backend PNEUMACARE menerima audio streaming dari websocket (data di memori, bukan file). Jadikan referensi logika (cara load checkpoint, cara panggil model, format output), lalu adaptasi jadi versi yang menerima tensor/array di memori langsung — lihat `SDD_SOFTWARE.md §5` untuk desain `inference_service.py` yang sudah disesuaikan.

## Fakta Kunci yang Terverifikasi dari File Ini (12 Agustus 2026)

| Item | Nilai |
|---|---|
| Framework | PyTorch (checkpoint disimpan via PyTorch Lightning) |
| Arsitektur | `mobilenet_v3_small` (torchvision), `weights=None`, classifier terakhir diganti `nn.Linear(in_features, 4)` |
| Sample rate | **22000 Hz** |
| Durasi segmen | **5 detik** (bukan 10 detik seperti asumsi awal di dokumen lain — sudah dikoreksi) |
| Overlap default | 0.0 (tapi contoh di `test.py` pakai `overlap=4.75` untuk sliding window tiap 0.25 detik — opsi ini tersedia kalau tim mau granularitas prediksi lebih rapat) |
| Jumlah mel filterbank | 50 |
| Urutan kelas (dari `detector.py`) | `["none", "wheeze", "crackle", "both"]` — index 0,1,2,3 |
| Format confidence/probabilitas | Persentase (0-100), BUKAN fraksi 0-1 |
| Cara load checkpoint | `checkpoint["state_dict"]`, filter key berawalan `"model."`, strip prefix `"model."`, load ke `self.model.model` (bukan `self.model` langsung — perhatikan nested attribute `.model.model`) |

⚠️ **Belum terverifikasi / perlu ditanyakan ke Nathanael:**
- Urutan kelas di atas (`none, wheeze, crackle, both`) **tidak cocok** dengan urutan axis di gambar confusion matrix yang dikirim Tony (`none, crackles, wheezes, both` — posisi wheeze/crackle tertukar). Konfirmasi mana yang benar sebelum dipakai untuk interpretasi hasil ke pengguna.
- Apakah `mobilenet_v3_small` ini pilihan final di antara 3 arsitektur yang dibandingkan di proposal (ResNet50/EfficientNet/MobileNet), atau masih salah satu kandidat yang diuji.
