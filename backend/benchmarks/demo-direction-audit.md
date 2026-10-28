# Acuan demo feat/ai-integration — audit 28 Oktober 2026

## Keputusan yang dipakai

Pengguna menetapkan branch `feat/ai-integration` sebagai acuan demo, dengan kelas
**normal/abnormal**. Perubahan dari empat menjadi dua kelas disengaja oleh tim;
audit ini tidak menganggapnya penyimpangan yang perlu dibatalkan. Alasan performa
empat kelas yang lebih buruk adalah informasi dari tim, bukan hasil evaluasi model
yang dilakukan pada sesi audit ini.

Base yang diperiksa: `b177a81`, ditambah perbaikan ingestion/worker di worktree demo
`software/.worktrees/feat-ai-integration-demo`. Model AST HTTP pada 16000 Hz menjadi
acuan; kapasitas MobileNet lama/22000 Hz tidak membuktikan kapasitas AST.

## Bug yang direproduksi dan diperbaiki di worktree demo

1. **Outage ML service menghasilkan klasifikasi palsu.** Sebelumnya
   `backend/ingestion/websocket_server.py::_classify_input` menangkap error HTTP/model
   lalu menghasilkan `mock_v3`; hasilnya disimpan dan dapat memengaruhi tren/alert.
   Sesudah perbaikan, service yang dikonfigurasi namun gagal menyebabkan job gagal
   secara eksplisit. Mock hanya dipakai bila `ML_SERVICE_URL=''` dipilih eksplisit.
   Tes sebelum perbaikan gagal karena baris mock benar-benar ditulis; sesudahnya
   tidak ada classification/cycle sintetis yang dibuat saat service gagal.
2. **Evaluasi tren saat ini dihitung dua kali.** `compute_and_save_trend` menyimpan
   event sebelum alert dievaluasi. Alert service membaca tiga event terbaru lalu
   menambahkan event saat ini sekali lagi. Tes nyata DB dengan flag `[false,true,true]`
   menghasilkan level3 sebelum perbaikan. Kini level2, dan baru event true ketiga
   menghasilkan level3. Parameter tetap tiga evaluasi; tidak ada tuning klinis.
   `trend_already_saved=True` adalah default sesuai ingestion; caller yang secara
   eksplisit mengevaluasi calon event belum tersimpan dapat memilih False.
3. **Respons ML tidak memenuhi kontrak numerik diterima.** Client kini memvalidasi
   integer class 0/1 (bukan bool/float), confidence dan dua probabilitas finite dalam
   0..1, jumlah probabilitas satu, class sesuai argmax, dan confidence sesuai
   probabilitas kelas terpilih. Toleransi serialisasi float32 adalah 1e-5, bukan
   ambang klinis. Nilai tidak dinormalisasi atau diperbaiki diam-diam. Tie mengikuti
   `torch.argmax` (kelas pertama). Lima belas kasus invalid lolos sebelum perbaikan
   dan ditolak sesudahnya; output valid dengan roundoff tetap utuh.

## Hal yang belum dapat dianggap selesai

| Temuan | Bukti kode | Implikasi |
|---|---|---|
| Database main lama tidak kompatibel otomatis | `models/classification.py` memakai predicted_class/confidence/probabilities/model_version; main lama memakai wheeze_crackle_*; app hanya create_all | Gunakan DB demo terpisah atau migrasi eksplisit; create_all tidak mengganti kolom |
| Window tren enam baris kini dapat berisi enam siklus | `trend_analysis/trend_service.py` membaca setiap classification; pipeline dapat membuat beberapa classification per 5 s | Rentang temporal window berubah terhadap desain lama6 segmen = 30 s; validasi parameter temporal masih perlu tim |
| Persistence mencampur empat channel | `models/trend.py` tidak menyimpan channel_id; alert query berdasarkan device_id | Tiga evaluasi berturut belum berarti tiga waktu evaluasi pada satu channel; perlu keputusan desain agregasi sebelum klaim longitudinal tertentu |
| Klasifikasi+metadata siklus bukan satu transaksi atomik | Dua fungsi persist melakukan commit terpisah | Kegagalan commit kedua dapat meninggalkan classification tanpa metadata; belum dimigrasikan dalam perbaikan throughput |
| Service AST dapat memblokir eventloop | `ml-service/main.py` async predict memanggil classifier.predict sinkron | Health/request lain bisa tertunda; ukur pada model asli sebelum menentukan concurrency |
| Identitas artifact model belum berasal dari service | backend/inference/inference_service.py memakai versi config | Nama versi konfigurasi belum membuktikan checksum checkpoint yang sedang dimuat |
| Penggunaan per-cycle/tile terhadap domain training belum divalidasi di sesi ini | service fix_length dan cycle slicing ada; checkpoint/data training belum tersedia | Jangan menafsirkan confidence sebagai ukuran akurasi klinis |

Tampilan clinician latest sudah menggunakan normal/abnormal serta menyatakan model
pengembangan belum tervalidasi klinis. Model B severity tetap ditunda. UI tidak
menampilkan label wheeze/crackle sebagai keluaran model dua kelas.

Dokumen lama PRD/SRS/SDD/kontrak yang masih mengatakan empat kelas dan target model
22000 Hz harus diselaraskan dengan keputusan baru. Itu utang dokumentasi, bukan
alasan mengembalikan model ke empat kelas. Kontrak transport ESP32 tetap PCM 16 kHz.

Satu ketidaksesuaian README_DATA_FLOW §1.4: teks mengatakan input pendek ditile lalu
zero-pad, sementara kode `ml-service/modules/model.py:fix_length` mengulang dengan
ceil lalu center-crop bila lebih panjang dari target. Kode preprocessing model
jangan diubah hanya untuk mengikuti deskripsi dokumentasi yang keliru.

## Pengujian dan lingkungan

Tes dijalankan dengan database SQLite sementara, mode mock eksplisit, dan import-time
MQTT/watchdog distub. Pengujian ini tidak membaca/mengubah DB pengguna atau mematikan
layanan pengguna. Real AST belum dipakai pada tes ini.

- Dua bug awal: 13 tes fokus lulus, lalu **255 tes lengkap lulus, 23.93 s**.
- Setelah validator: **22 tes fokus lulus**; **271 tes lengkap lulus, 23.67 s**.

Pencarian read-only filename checkpoint dan kandidat environment di bawah home
(depth 8, termasuk Downloads/Coding, tanpa membaca secrets/.env) menemukan hanya:

- `Downloads/Respiratory-Detector-main/respiratory_detector/models/respiratory-epoch=05-val_loss=0.9021.ckpt`
- `Coding/pneumacare-gemastik/software/ai_reference/respiratory-epoch=05-val_loss=0.9021.ckpt`

Keduanya sekitar 18.5 MB dan merupakan checkpoint lama, bukan AST final best.ckpt.
Pencarian tambahan di `.cache` sampai depth 8 juga tidak menemukan checkpoint `.ckpt`.
Environment terdokumentasi `~/dev/pneumacare-ml-services/Env` tidak ditemukan.
Metadata env kandidat diperiksa tanpa mengubahnya: env sample-ai-possibilities
memiliki requests/multipart/uvicorn; nexusDao memiliki FastAPI/requests/uvicorn;
backend saat ini memiliki PyTorch CPU/numpy/requests. Tidak ditemukan satu kandidat
lengkap dengan transformers/librosa/PyTorchLightning untuk AST. Tidak mendownload
weights atau paket besar. Tidak menganggap cache pretrained sebagai model final.

Verifikasi hardware sesi sekarang dan kesehatan service dijelaskan terpisah oleh
laporan observasi aktual; hasil unit test ini bukan bukti drop fisik sudah hilang.

## Instrumentasi akhir pada acuan demo

Pipeline demo kini mencatat `audio_stage` dengan monotonic duration, status,
device dan channel untuk registry, deteksi siklus, klasifikasi, gabungan dua commit
classification/metadata, tren dan alert (termasuk query vital terbaru). Durasi juga
tercatat ketika tahap gagal. `classify_http` mencakup serialisasi WAV, request/wait
HTTP serta parsing/validasi respons; timer ini tidak memisahkan preprocessing dan
forward yang berlangsung di proses ML lain.

`LungSoundClassifier.predict` pada ML service mencatat `preprocessing_ms`,
`forward_output_ms`, `total_ms`, status dan input device. Forward/output mencakup
softmax dan konversi hasil ke Python, sehingga pengukuran menunggu materialisasi
output accelerator apabila jalur accelerator berfungsi. Main ML mengaktifkan INFO
logging agar tahap tersebut terlihat. Perhitungan dan preprocessing model tetap.

Tes predict memakai metode actual dari source dengan model CPU kecil dan input
preprocessing terkontrol agar dapat memverifikasi output tetap sama tanpa mengimpor
dependensi AST yang tidak tersedia. Ini bukan pengujian model AST/checkpoint asli.
Tes error HTTP membuktikan tahap gagal tetap mempunyai metrik durasi dan identitas.

Setelah instrumentasi: **28 tes fokus lulus** dan **274 tes lengkap lulus, 13.80 s**.
`py_compile` kedua file service dan `git diff --check` lulus. Tidak ada klaim kapasitas
AST dari hasil ini.

Risiko CUDA yang ditemukan dari kode (belum direproduksi): startup service dapat
memindahkan model ke CUDA, tetapi predict membuat tensor extractor di CPU tanpa
`.to(device)` sebelum forward. Pada host CUDA ini berpotensi gagal karena device
mismatch. Host sesi ini CPU dan checkpoint AST belum tersedia; tidak mengubah
perilaku device/model untuk menutupi ketidakpastian tersebut.
