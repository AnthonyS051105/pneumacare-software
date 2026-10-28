> Audit sebelum merge terbaru: [AUDIT_FEAT_AI_INTEGRATION_2026-10-28.md](AUDIT_FEAT_AI_INTEGRATION_2026-10-28.md). Ditemukan lima blocker yang direproduksi; keputusan saat ini belum merge.

# Status demo PNEUMACARE — 28 Oktober 2026

**Drop audio belum terselesaikan. Ini sekarang terverifikasi pada ESP32 fisik.**
Acuan demo adalah `feat/ai-integration`, dengan AST **normal/abnormal**. Pemilihan dua
kelas disengaja oleh Tony; bukan kesalahan yang perlu dikembalikan ke empat kelas.

## Program yang aktif

- Root `software/` masih checkout `main` untuk mempertahankan pekerjaan sebelumnya.
- Checkout utama demo: `software/.worktrees/feat-ai-integration-demo/`, branch
  `feat/ai-integration`, base `b177a81` + perbaikan lokal.
- Backend **port5000 sekarang berasal dari checkout demo tersebut**, pipeline normal,
  satu proses tanpa debug reloader. Flag receive-only/QUICKACK eksperimen sudah dimatikan.
- DB aktif: `backend/demo-ready-two-class.db` di checkout demo. Empat akun, dua pasien,
  tiga device dan satu pairing dipertahankan dari snapshot DB lama. Sebanyak1647 hasil
  empat kelas, tren dan alert lama diarsipkan pada tabel `*_legacy_four_class` pada
  salinan, bukan diberi label seolah berasal dari AST. DB root asli tidak dimigrasikan.
- Endpoint AST port8000 **belum berjalan**. Kegagalan AST yang dikonfigurasi tidak
  diganti mock; karena itu backend aktif belum berarti demo inferensi siap.
- Tidak ada frontend port3000 yang terlihat pada pemeriksaan akhir. Bila menjalankan
  frontend, gunakan source checkout demo yang sama, bukan frontend root historis.

Launcher dari root software:

```bash
./run-demo.sh --check
```

Saat ini mengembalikan exit2 dan `model_loaded:false` secara benar. Setelah service
AST siap, hentikan backend yang lama lalu jalankan `./run-demo.sh`. Launcher menjaga
path branch dan database sehingga tidak tidak sengaja menjalankan main. Backend yang
sedang aktif diluncurkan dengan `--allow-unavailable-model` untuk observasi; itu bukan
izin membuat hasil palsu dan bukan tanda demo AI sudah siap. Log aktif:
`backend/benchmarks/live-demo-normal-backend.log` pada root software.

## Bukti perangkat fisik

Capture serial berlangsung sekitar10menit, **09:34:36–09:44:33 WIB**; loop dibatasi
600detik. Portserial diambil alih atas izin Tony lalu dilepas setelah selesai.
Board ternyata reboot saat port dibuka meskipun DTR/RTS disetel off; penilaian memakai
fase STREAMING sesudah boot, bukan fase NTP_SYNC. Tidak melakukan flashing ulang,
perubahan gain, sample rate, jumlah channel, SSID/IP, atau buffer firmware.

| Fase stabil | Durasi ukur | Chunk | Chunk/detik | Delta drop/ch1 |
|---|---:|---:|---:|---:|
| Main yang sebelumnya dijalankan pengguna |139.626s|716|**5.13**|1,518,112 sample|
| Latest, penerimaan saja, tanpa inferensi/siklus/DB audio |39.537s|360|**9.11**|272,576 sample|
| Latest receive-only + ACK cepat per raw TCP recv |60.806s|560|**9.21**|412,800 sample|
| Target nominal |—|—|**16**|**0**|

Semua channel tetap drop pada ketiga fase. Fase bukan eksperimen lab kondisi CPU/RF
identik; perbedaan main/latest tidak membuktikan penyebab tunggal atau peningkatan
kapasitas AST. Yang terbukti: **drop tetap terjadi ketika model, siklus, persistensi,
tren dan alert audio tidak berjalan sama sekali**. Jadi inferensi bukan satu-satunya
penyebab masalah aktual. Perbaikan antrean sebelumnya tetap diperlukan untuk
mencegah blocking model saat segmen sudah dapat terbentuk.

Pada fase awal sebelum pergantian server: `dma_ovf=0`, `i2s_err=0`, `ws_fail=0`, PPG
sekitar100Hz, counter FIFO/I2C/queue/MQTT drop nol. Satu send pernah menahan task
sampai1.64s walau belum dinyatakan gagal. Selama eksperimen server sengaja diganti
beberapa kali; counter `ws_fail` menjadi3 dan PPG `queue_drop` menjadi1025, sehingga
kenaikan tersebut tidak boleh disajikan sebagai kegagalan sesi stabil tanpa konteks.
Nilai send maksimum sejak boot setelah gangguan mencapai5.93s.

Backend latest benar-benar mendeteksi loss sebelum send, contohnya sequence tetap
berurutan (`expected_seq=341 received_seq=341`) tetapi `lost_samples=6336`. Parsial
dibatalkan, tidak diklasifikasikan sebagai audio kontinu. Pada eksperimen per-recv
ACK, receiver max3.756ms, decode mean sekitar0.186ms/chunk dan assembly sekitar1.17ms.
Belum ada segmen5s kontinu dalam sesi ini: tidak ada job model yang perlu diproses.
Ini menjelaskan ketiadaan hasil klasifikasi baru dan bukan alasan untuk menonaktifkan
deteksi gap.

Bukti mentah: `live-serial-status.jsonl`, `live-hardware-summary.json`,
`live-demo-backend.log`. Snapshot DB sebelum mengambil serial:
`live-hardware-observation.json` memperlihatkan heartbeat dan vitals terus bertambah
sementara jumlah klasifikasi tidak bertambah.

## Arah diagnosis berikutnya

- Hambatan terukur ada pada send/transport, bukan biaya decode atau antrian inferensi
  pada sesi ini. TCP send buffer ESP32 aktual5760byte, MSS1436byte, frame audio sekitar
 11KB; `WiFiClient::write` dapat menunggu ACK/progres selama beberapa detik.
- `TCP_NODELAY` dan modem-sleep off di firmware sudah aktif. Eksperimen Linux
  QUICKACK tidak menghilangkan drop, sehingga **delayed ACK belum terbukti sebagai
  akar masalah dan eksperimen itu tidak dijadikan default produksi**.
- Wi-Fi komputer: signal sekitar**−73dBm**, bitrate57.8Mb/s, power management **on**,
  excessive retry counter373 saat dibaca. RSSI ESP32 lebih kuat, sekitar−40dBm; itu
  tidak membuktikan link komputer juga baik. Counter retry tersebut kumulatif, bukan
  pengukuran delta selama eksperimen. Belum membuktikan power-save/RF sebagai sebab.
- Tony mengonfirmasi laptop sudah sangat dekat dengan hotspot HP. Karena itu jarak
  fisik tidak dianggap akar masalah. Uji pembeda berikutnya adalah power-save host
  on/off atau jalur access point berbeda; angka RSSI yang lemah tetap pengamatan,
  bukan bukti jarak. Profil jaringan tidak diubah diam-diam.
- Percobaan menonaktifkan power-save sementara tidak dapat berjalan: `sudo` meminta
  password. Tidak meminta/membaca password dan tidak ada setting jaringan yang berubah.
  Jika pengguna memilih uji ini, jalankan sendiri secara lokal; bandingkan kondisi
  on/off dan pulihkan setting sebelumnya.

## Model final belum tersedia

Pencarian filename home dan cache sampai depth8 tidak menemukan `best.ckpt` AST.
Hanya dua salinan checkpoint MobileNet lama sekitar18.5MB ditemukan. Environment
AST yang didokumentasikan (`~/dev/pneumacare-ml-services/Env`) tidak tersedia; kandidat
environment yang diperiksa belum mempunyai kombinasi dependency AST lengkap.
Pencarian ini bukan bukti semua media/direktori di komputer telah diperiksa.

Dependency backend `requests==2.31.0` sudah dipasang ke venv backend yang tersedia.
Tidak mengunduh weights pengganti atau paket ML besar. Demo memerlukan checkpoint
AST dari tim model dan environment sesuai `ml-service/requirements.txt`, lalu
`/health` service harus memberi `model_loaded:true`. Checkpoint empat kelas lama
bukan pengganti artifact ini. Model dua kelas asli **belum diukur kapasitasnya**.

## Perbaikan latest dan kesesuaian arah

- Antrean FIFO satu worker bounded8, cancel usia antre10s, gap/reconnect/session owner,
  snapshot immutable dan validasi frame dari perbaikan sebelumnya sudah diterapkan
  pada checkout demo; jalur siklus dan dua kelas tetap dipertahankan.
- AST down tidak lagi menulis mock otomatis. Mock hanya bila URL sengaja dikosongkan.
- Tren tersimpan tidak lagi dihitung dua kali dalam persistence: dua hasil signifikan
  tidak boleh salah menjadi tiga. Parameter klinis tidak diubah.
- Respons HTTP model divalidasi: angka finite0–1, probabilitas normal, class/argmax
  dan confidence konsisten. Tidak mengubah preprocessing model atau menormalkan output.
- Tes suite latest setelah validator dan instrumentasi tahap: **277lulus,15.76s** dengan mock dan
  DB sementara. Ini bukan validasi akurasi/kapasitas AST asli.
- Persiapan DB diuji pada snapshot aktual: jumlah akun/pasien/device/pairing sama,
  hasil empat kelas diarsipkan dan tabel klasifikasi dua kelas baru kosong.

Batas yang masih perlu perhatian tim: window tren6baris kini dapat berarti6siklus,
bukan30detik; persistence mencampur channel karena TrendEvent belum punya channel_id;
classification dan metadata siklus memakai dua commit terpisah; versi model masih
string konfigurasi, bukan identitas hash artifact. Detail: `demo-direction-audit.md`.
Kedua kontrak hardware/software serta catatan PRD/SRS/SDD diselaraskan ke keputusan
AST dua kelas. Model tetap skrining/indikasi, tidak dinyatakan sebagai diagnosis.

Patch lengkap terhadap baseb177a81: `demo-ready-changes.patch`. Termasuk source baru yang belum di-commit; tidak memuat database, secrets atau weights. Source demo memakai log monotonic untuk registry, siklus, HTTP total, persistensi, tren dan alert. ML service memiliki log preprocessing dan forward tersendiri saat nanti benar-benar berjalan; belum ada pengukuran AST asli. Setelah refresh log terakhir,3tes fokus tambahan lulus0.89s.

## Uji power-save lanjutan

Setelah konfirmasi bahwa laptop sudah dekat hotspot HP, dilakukan capture tambahan
baseline sekitar75detik. Percobaan `nmcli device modify` (runtime, bukan profil
tersimpan) gagal karena NetworkManager tidak dapat reapply properti powersave pada
koneksi aktif. Setting runtime dikembalikan ke default dan pembacaan tetap **on**.
Tidak ada fase off yang berhasil diukur, jadi tidak ada klaim manfaat power-save off.
Bukti: `live-power-save-events.jsonl` dan `live-power-save-status.jsonl`.
Untuk uji langsung dibutuhkan command admin yang pengguna jalankan sendiri di
terminal; password tidak diminta/dibaca oleh agent.

Ditemukan juga socket half-open sesudah reboot ESP: ditambahkan server ping20detik
agar koneksi yang kehilangan client akhirnya dibersihkan. Ini cleanup lifecycle,
bukan klaim perbaikan throughput. Timestamp sebelum NTP pada latest juga kini memakai
perkiraan waktu terima, sesuai kontrak, dengan log sumber yang eksplisit.

## Hasil uji power-save off yang benar-benar terverifikasi

Tony kemudian menonaktifkan power-save sendiri di terminal. Pembacaan awal agent
masih on, tetapi selanjutnya terverifikasi off; timeline120pembacaan berurutan setiap
sekitar1detik semuanya **off**. Jangan mencampur fase awal yang masih on dengan fase ini.

Pada rentang terverifikasi10:01:14–10:03:06WIB (111.761detik), chunks_sent255→791:
**536chunk /111.761s =4.80chunk/s**, target16. Drop tiap channel bertambah sekitar
**1,252,160–1,255,808sample**. `dma_ovf`, `i2s_err`, `ws_fail`, dan PPG queue_drop
semuanya tetap0. Send maksimum sejak boot bertambah hingga1.52s.

Karena itu power-save off **belum menyelesaikan drop**. Kondisi RF/timing antar-run
bervariasi; tidak disimpulkan bahwa off memperburuk throughput atau power-save bukan
faktor pada lingkungan lain. Bukti: `live-power-state-timeline.jsonl`,
`live-power-off-verified-status.jsonl`, `live-power-off-summary.json`.

Power-save saat akhir pengukuran off karena perintah manual Tony; agent tidak punya
sudo untuk memulihkannya. Untuk mengembalikan kondisi awal, pengguna dapat menjalankan
`sudo /usr/sbin/iwconfig wlo1 power on` di terminal. Profil NetworkManager tersimpan
tidak diubah. Portserial telah dilepas setelah capture3menit selesai.

**Kesimpulan saat ini tetap: transport/audio kontinu belum lolos, AST final belum
tersedia, dan demo AI belum siap.** Uji pembeda berikutnya memerlukan jalur hotspot/AP
lain atau instrumentasi paket/ACK lebih lanjut. Tidak mengurangi channel/rate/frekuensi
inferensi, mengganti protokol, atau memperbesar buffer sebagai penutup kekurangan
throughput berkelanjutan tanpa pengukuran dan penjelasan dampak.
