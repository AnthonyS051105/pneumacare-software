> **Status terbaru:** lihat [CURRENT_STATUS.md](CURRENT_STATUS.md). Pengujian fisik berikutnya membuktikan drop masih terjadi; feat/ai-integration kini acuan demo dan sudah dijalankan dari checkout terpisah. Laporan di bawah adalah rekaman tahap sebelumnya.

# Audit kehilangan audio PNEUMACARE — 28 Oktober 2026

## Hasil dan batas kesimpulan

Perbaikan diterapkan pada checkout `main` (base software `91271a2`) dan firmware lokal,
dengan perubahan lokal pengguna dipertahankan. Tidak ada firmware di-flash.

**Terbukti dari kode dan tes:**

1. Receiver lama memanggil inferensi, penyimpanan, tren, dan alert secara langsung sebelum
   `ws.receive()` berikutnya. Seluruh pekerjaan tersebut menahan pembacaan aplikasi.
   Tes baru memblokir model dengan event: receiver baru tetap membaca semua 80 chunk
   empat channel, satu pekerjaan aktif, dua menunggu, dan satu ditolak pada kapasitas dua.
2. Receiver lama mencatat gap tetapi menyambung audio di kedua sisi gap. Tes sebelum
   perbaikan benar-benar menghasilkan segmen `[1, 2]` melintasi chunk hilang; sekarang
   parsial dibuang dan segmen berikutnya hanya berisi audio kontinu sesudah gap.
3. `seq_no` firmware naik saat chunk dibaca/diusahakan kirim, bukan saat sampel di-drop
   dari ring. Karena itu drop-oldest dapat terjadi tanpa gap sequence sama sekali.
   Tes native dan backend sekarang menguji kasus ini dengan indeks sample.
4. Cleanup lama hanya mereset channel terakhir di socket dan buffer global digunakan
   lintas koneksi. Receiver sekarang memiliki buffer semua channel per koneksi,
   kepemilikan per device, dan cancellation token. Penutupan socket lama tidak dapat
   mereset atau merebut sesi baru.
5. Penolakan auth lama memakai `ws.close(message=bytes)`, sedangkan wsproto membutuhkan
   string; tes transport menemukan `AttributeError` dan sekarang memverifikasi code 1008.

**Belum terbukti:** penyebab lengkap penurunan kiriman ESP32 dari sekitar 160 menjadi
32 chunk/10 detik. Loopback dengan checkpoint lama tidak mereproduksi kehilangan itu,
bahkan pada kode sebelum perbaikan. Hipotesis backpressure backend masuk akal dan
jalur blocking-nya nyata, tetapi beban CPU, Wi-Fi/TCP, blocking send/reconnect, MQTT,
logging, dan kondisi runtime pada sesi perangkat asli belum diukur serentak.
Interval antarlog inferensi tidak digunakan sebagai durasi inferensi.

## Desain implementasi

- WebSocket hanya memvalidasi JSON/base64/format, decode int16 little-endian, menyusun
  segmen tepat 5 detik, dan menyerahkan snapshot PCM immutable ke antrean. Decode
  memakai NumPy atas bytes, menggantikan loop Python per sample. Chunk 2 detik juga
  dapat melintasi batas segmen tanpa membuat segmen 6 detik atau membuang remainder.
- Satu worker FIFO per aplikasi/proses memanggil jalur model dan hasil yang sama.
  Tidak menambah worker, process pool, batching atau GPU. Preprocessing tetap sesuai
  referensi lama: 16000 -> **22000 Hz**, satu resampling per segmen.
- Upsert device dipindah dari setiap chunk ke pekerjaan segmen: pada beban nominal,
  16 transaksi/detik menjadi 0,8/detik. Heartbeat/status dan PPG MQTT tetap memakai
  jalur registry masing-masing. `last_seen_at` audio sekarang mengikuti pemrosesan
  segmen; heartbeat MQTT tetap menjadi jalur status langsung.
- Tiap job memiliki Flask app context sendiri; exception memicu rollback dan session
  remove. Kegagalan satu job tidak mematikan consumer. Hasil klasifikasi yang sudah
  di-commit tetap merupakan riwayat bila tahap tren/alert selanjutnya gagal; ini
  mempertahankan semantik commit yang sudah ada, bukan transaksi atomik semua tahap.
- Timer lokal memakai monotonic: receiver/decode/assembly, normalisasi/resampling/mel,
  preprocessing, forward+softmax, registry, persist, tren, alert, queue wait, processing,
  dan total ready-to-complete. Log job memuat status, alasan, device/channel dan counter.
  Log agregat receiver setiap 80 chunk; tidak ada log sample, token atau payload PCM.
- Timestamp perangkat bukan ukuran latensi. Sebelum epoch masuk akal (>= November
  2023), backend memakai perkiraan waktu terima dikurangi durasi chunk dan mencatat
  `source=server_receive_estimate`. Metadata sample v2 tetap menjadi acuan kontinuitas
  ketika SNTP melompat. Ini bukan jaminan waktu akuisisi atau fase antarbus I2S.

## Kapasitas dan overload

`backend/config.py`:

| Pengaturan | Default | Makna |
|---|---:|---|
| AUDIO_QUEUE_CAPACITY | 8 | Jumlah segmen menunggu, di luar satu aktif |
| AUDIO_QUEUE_MAX_WAIT_SECONDS | 10 | Job yang terlalu tua dibatalkan saat diambil worker |
| AUDIO_MAX_DEVICES | 8 | Batas device yang memiliki parsial aktif per proses |
| SOCK_SERVER_OPTIONS.max_message_size | 260000 byte | Batas frame sebelum parsing |

Kapasitas delapan memberi dua burst empat channel. **Reject newest** saat penuh;
receiver tetap membaca, penolakan tercatat. Job tidak diulang diam-diam dan tidak
menggabungkan audio dari segmen yang ditolak. Status `received`, `accepted`,
`completed`, `failed`, `rejected`, `cancelled`, `queued`, `active`, `high_water`,
`wait_max_ms` dan `total_max_ms` dapat dibaca lewat
`app.extensions['audio_worker'].snapshot()` serta log per job. Tidak ada endpoint
monitoring publik baru.

PCM antrean pada 16 kHz: 8 x 80000 x 2 = **1.28 MB**, ditambah aktif 0.16 MB.
Parsial maksimal delapan device x empat channel x 0.16 MB = 5.12 MB. Pada rate
tertinggi yang diterima (48 kHz), batas PCM ini tiga kali lipat. Anggaran ini
mengecualikan model, tensor preprocessing, buffer transport dan overhead object;
bukan klaim pengukuran RSS total. `simple-websocket` juga mempunyai daftar pesan
masuk internal yang tidak menyediakan batas jumlah pesan melalui konfigurasi
Flask-Sock; frame size dibatasi, tetapi banjir pengirim di atas pacing kontrak
belum dijamin bounded secara end-to-end. Uji ini memverifikasi pacing normal dan
antrean/parsial aplikasi yang dibatasi. Snapshot tidak berbagi storage mutable dengan
buffer berikutnya.

Batas 10 detik diperiksa saat dequeue, bukan timer yang menginterupsi inferensi.
Job aktif dapat berjalan melewati batas tersebut. Pada overload uji, antrean
tertua diambil setelah 12.19 detik dan langsung dibatalkan. Ini mencegah pekerjaan
usang terus menumpuk; tidak menciptakan kapasitas komputasi tambahan.

## Gap, reconnect, dan lifecycle

- Gap sequence, indeks sample, perubahan rate/stream, dan frame rusak membatalkan
  parsial yang relevan. Log mencatat alasan, parsial dibuang, serta jumlah sample
  hilang bila indeks memungkinkan. Ukuran sample dihitung dari PCM aktual.
- Pergantian koneksi/boot membersihkan seluruh channel dan membatalkan antrean
  sesi lama. Inferensi yang sudah berjalan diperiksa lagi setelah komputasi sebelum
  penyimpanan. Operasi DB yang sudah di-commit tidak ditarik dari riwayat.
- Pengirim legacy tetap diterima; sequence dan timestamp dengan toleransi jitter
  100 ms dipakai. Deteksi loss ring legacy tetap tidak andal; karena itu log menandai
  `legacy_timestamp_only`. Loss sebelum frame pertama sesi tidak dapat dihitung
  backend tanpa titik pembanding; counter firmware tetap diperlukan.
- Worker mulai **lazy pada segmen pertama**, bukan pada import/factory/reloader
  parent. `start()` idempotent. Tiap app punya worker sendiri, bukan global lintas app.
  Jangan fork setelah worker berjalan; guard PID menolak kondisi tersebut.
- `stop(timeout=2)` membuang antrean, memberi sinyal pembatalan aktif, dan join terbatas.
  Native model call tidak dapat dihentikan paksa oleh thread Python. Jika macet,
  `stop()` mengembalikan False; daemon tidak menahan exit proses. Integrator server
  dapat memanggil `app.extensions['audio_worker'].stop()` pada shutdown; atexit juga
  didaftarkan. SIGKILL/crash tidak menjamin drain atau cleanup.
- **Deployment yang didukung untuk satu vest: satu proses server, threaded requests.**
  Gunakan satu worker proses WSGI, tanpa preload/fork setelah task berjalan. Beberapa
  proses masing-masing memiliki model, queue, registry sesi dan subscriber MQTT;
  dua socket device yang sama di proses berbeda tidak memiliki koordinasi takeover.
  Mode tersebut membutuhkan shared routing/state sebelum diklaim didukung.
- Jalur penerimaan biasa tidak memanggil DB/model/tren. Shutdown dan pergantian sesi
  tidak mengubah model atau state parsial milik koneksi pengganti.

## Pengukuran sebelum/sesudah

Mesin: Intel Core i5-12600H, 16 logical CPU, Python 3.12, PyTorch 2.13.0+cpu,
12 thread intraop dan 12 interop, CUDA tidak tersedia. SQLite file sementara,
Flask/Werkzeug threaded tanpa reloader. Klien WebSocket loopback, empat channel,
16 kHz, PCM int16, tone sintetis 400 Hz, 4000 sample/chunk, interval 250 ms,
empat pesan per burst, segmen 5 detik. MQTT dinonaktifkan hanya pada harness isolasi.
Kode sebelum perbaikan diekstrak dari HEAD ke `/tmp`, tanpa mengubah working tree.
Dua uji real dijalankan berurutan, checkpoint sama:
`respiratory-epoch=05-val_loss=0.9021.ckpt`, SHA256
`46fb066892e65f482510e09a35cc59b96f026b55e0e8740bd20a7b757f4a8e07`.

| Metrik | Sebelum, 60 s | Sesudah, 60 s |
|---|---:|---:|
| Chunk dikirim | 960 | 960 |
| Throughput | 16/s | 16/s |
| Segmen disimpan | 48/48 | 48/48 |
| Waktu handler pekerjaan p50/p95/max | 43.03/67.11/76.14 ms | 55.87/87.52/119.22 ms |
| Receiver max (decode + assembly + submit) | belum diinstrumentasi | 2.85 ms |
| Gap/invalid | tidak diinstrumentasi di harness lama | 0/0 |
| Queue high-water / akhir | tidak ada queue | 3 / 0 |
| Gagal / ditolak / dibatalkan | tidak ada di hasil tersimpan | 0 / 0 / 0 |
| Queue wait p95/max | tidak ada | 184.78/254.94 ms |
| Ready -> complete p95/max | tidak diinstrumentasi | 251.88/354.77 ms |

Tidak ada peningkatan throughput yang dapat diklaim dari dua uji ini: keduanya
mencapai target dan tidak mereproduksi drop. Manfaat yang diuji adalah receiver
terlepas dari waktu pekerjaan lambat, memori terbatas, dan loss eksplisit.
Empat pekerjaan terberat masing-masing <=119.22 ms pada uji ini memberi batas
konservatif sekitar 476.9 ms kerja per burst empat channel, jauh di bawah budget
5 detik pada kondisi uji. Tidak mengukur model final AST atau kondisi ESP32/Wi-Fi.

Tahap sesudah perbaikan, p50/p95/max:

| Tahap | ms |
|---|---:|
| JSON+base64+decode | mean 0.156 per chunk |
| Assembly+submit | mean 1.067 per chunk |
| Preprocessing total | 14.68 / 23.86 / 24.82 |
| Inference+softmax+transfer output | 19.36 / 38.16 / 67.57 |
| Registry | 5.99 / 9.61 / 10.93 |
| Persist classification | 5.01 / 7.60 / 16.26 |
| Trend query/compute/save | 6.42 / 8.83 / 11.26 |
| Vitals lookup+alert | 1.97 / 2.72 / 5.55 |

Rincian preprocessing pada run final yang sama: normalisasi 0.20/2.34/2.80 ms,
resampling 2.52/7.76/10.40 ms, dan mel 11.38/16.49/20.62 ms (p50/p95/max).
Tes preprocessing dan checkpoint asli tetap lulus. Run final diulang setelah
instrumentasi tahap ini selesai dan tanpa suite tes berjalan bersamaan. Waktu
pekerjaan tidak membaik pada pembanding ini; penjadwalan thread, instrumentasi,
frekuensi CPU dan proses latar mesin tidak dikontrol sebagai eksperimen lab. Sweep awal empat segmen langsung
(tanpa transport/DB) pada 12/1/2/4 thread memberi sekitar 0.073/0.078/0.067/0.068 s;
tidak cukup bukti keuntungan stabil untuk mengubah konfigurasi thread global.

Overload mock: 30 detik, 480 chunk, model sengaja menunggu 4 detik/job. Seluruh
480 chunk diterima, receive max 3.30 ms, gap 0. Dari 24 segmen siap: 21 diterima,
9 selesai/disimpan, 3 ditolak penuh, 12 dibatalkan melewati batas usia; high-water
tepat 8, akhir 0. Drain tambahan 10.97 detik, ready-to-complete max 13.16 detik.
Ini pengujian kebijakan overload, bukan kapasitas model asli.

Artefak mentah dan log (tanpa audio/token): `baseline-real-60s.json`,
`worker-real-60s.json`, `worker-overload-30s.json`, file `.log` pendamping, dan
`stage-summary.json`. Harness: `backend/scripts/benchmark_audio_ingestion.py`.
Contoh ulang dari software root:

```bash
backend/venv/bin/python -m backend.scripts.benchmark_audio_ingestion \
  --duration 60 --model real --output /tmp/worker-audio.json
```

## Pengujian dan kontrak

- Backend final: **256 passed**, 24.08 s. Termasuk checkpoint asli, preprocessing,
  auth/API, MQTT/vitals, tren, persistensi, slow model, overload, rollback/recovery,
  FIFO, exact-length split, immutable PCM, gap sample tanpa seq gap, NTP, takeover,
  cleanup seluruh channel, startup idempotent/lazy, bounded shutdown, dan transport
  Flask-Sock sesungguhnya. Tes regresi gap dijalankan dan gagal sebelum perbaikan.
- Setelah checkpoint pembatalan tambahan sebelum DB/tren/alert: **22 focused tests passed**, 1.44 s.
- Firmware native: **38 passed**, 4.616 s. Build `pneumacare`: **SUCCESS**, 8.879 s;
  static RAM 68764/327680 byte (21.0%), flash 976077/1310720 (74.5%). Build bukan
  bukti kondisi fisik atau keandalan Wi-Fi.
- `git diff --check` software/hardware dan kesamaan kedua kontrak lulus.
- Header audio v2 menambah pasangan **opsional** `stream_id` dan `sample_start`.
  Firmware produksi mengirimnya; pengirim lama tetap dapat dipakai. Indeks diambil
  atomik bersama pembacaan ring, mencakup drop/clear/suppression, bukan hanya send.
  Identitas boot tetap saat reconnect. Tidak mengubah gain/rate/channel/network.
- Kedua salinan `docs/INTEGRATION_CONTRACT.md` di software dan hardware diubah identik.
  Patch perubahan firmware saja (terhadap perubahan lokal awal pengguna) juga disimpan
  sebagai `firmware-continuity.patch` untuk review. Folder dokumen ini diabaikan Git pada workspace saat ini; salinan lokal sudah
  diperbarui dan patch kontrak pendamping disertakan agar perubahan tidak terlewat.

## Branch model terbaru

`origin/feat/ai-integration` (`b177a81`) diambil dan diaudit terpisah. Branch itu
mengganti model lokal dengan AST HTTP dua kelas normal/abnormal pada 16 kHz dan
menambah deteksi siklus. Detektor dapat memberi 2–3 siklus per segmen pada contoh
yang diuji, sehingga budget empat channel bisa menjadi 8–12 panggilan model per
5 detik. Kapasitas MobileNet di atas **tidak membuktikan kapasitas AST**.

Checkpoint final `best.ckpt`, environment terdokumentasi, dan beberapa dependency
layanan AST belum tersedia. Tidak mendownload atau mengganti weights. Ada patch
kompatibilitas siap review untuk branch terbaru beserta audit
`feat-ai-integration-audio.md`: **252 tes mock suite latest lulus**, focused final
47 lulus. `git apply --check` patch terhadap base b177a81 lulus. Patch menjaga HTTP,
klasifikasi dua kelas, siklus dan penyimpanan metadata; tidak diterapkan ke main
karena itu akan mencampur migrasi model/DB/UI dengan perbaikan ingestion ini.

## Validasi hardware berikutnya (belum dilakukan)

1. Jalankan backend hasil perubahan satu proses tanpa reloader, model/version dicatat;
   upload firmware baru lewat prosedur normal pengguna. Kumpulkan serial + log backend
   dengan waktu mulai/akhir yang sama selama **10–15 menit**. Untuk pembanding gunakan
   jaringan, device, CPU, model dan beban yang setara. Jangan ubah gain.
2. Saat stabil, hitung delta setiap 5 detik: `chunks_sent` sekitar **80**, `drop` tiap
   channel tetap, `dma_ovf`, `i2s_err`, `ws_fail` tidak bertambah. Log baru
   `build_max_us` dan `send_max_us` menunjukkan operasi kirim yang menahan task
   network. Nilainya maksimum sejak boot, sehingga catat baseline dan kenaikannya.
3. Cocokkan 80 chunk diterima/5 detik dan empat segmen siap/5 detik; queue tidak terus
   naik, failed/rejected/cancelled tetap nol pada kondisi normal, dan total latency
   tidak meningkat seiring waktu. Pantau PPG ~100 Hz, FIFO/I2C/queue/MQTT drops dan
   heartbeat bersamaan. Gunakan counter, bukan interval pesan hasil inferensi.
4. Putus/sambung sekali secara terkendali: periksa semua channel partial direset,
   session lama dibatalkan, tidak ada segmen lintas gap. Ring loss terlapor melalui
   `sample_start`; bedakan lost_samples yang diketahui dari audio parsial yang
   sengaja dibuang. Gangguan ini diharapkan menambah cancellation/gap.
5. Jika drop tetap naik sementara queue rendah, cari korelasi `send_max_us`, Wi-Fi,
   MQTT reconnect/socket timeout, heap dan `dma_ovf`. Jika queue terus penuh,
   kumpulkan stage timing pada model aktual; ukur budget siklus AST secara khusus
   sebelum menambah worker atau mengubah preprocessing.

Belum ada validasi model/klinis, pemasangan vest, gain akhir atau kesamaan fase dua
bus I2S. Tidak ada hasil wheeze, vital atau confidence yang ditafsirkan sebagai diagnosis.
