# Perbaikan lima masalah audit — 28 Oktober 2026

**Kelima masalah yang disetujui Tony sudah diperbaiki pada feat/ai-integration.**
Lima reproduksi audit sekarang tes biasa dan lulus; tidak ada xfail yang menutupi
hasilnya. Model AST normal/abnormal, preprocessing, gain, jaringan dan firmware
tidak diubah oleh pekerjaan ini. Ini tidak menyatakan drop transport ESP32 atau
kapasitas/akurasi AST asli sudah tervalidasi.

## Perubahan dan bukti

| Audit | Perbaikan | Pengujian penting |
|---|---|---|
| 01: threshold tren | Resolver ambang pasien/default yang sama dipakai tren dan alert. Flag yang disimpan mengikuti pengaturan pasien; alert membandingkan slope dengan ambang aktif dan menuliskan ambang yang sama dalam trigger. Nilai0 tidak keliru menjadi fallback. | Ambang tinggi/rendah, patient berbeda, tanpa patient/threshold/null, kandidat alert yang flag awalnya tidak sesuai ambang aktif. |
| 02: status pasien | Summary mencari alert **belum ditinjau dengan level tertinggi**, baru memakai waktu sebagai pembanding. Alert terbaru yang lebih ringan/sudah ditinjau tidak menutupi alert darurat. | Alert3 aktif +alert1 acknowledged; alert lebih baru/ringan; semua acknowledged; offline tetap tidak menyembunyikan urgensi. Mapping level1/2 attention dipertahankan. |
| 03: kualitas PPG | ReadingVital menyimpan hr_confidence/spo2_confidence/rr_confidence. Jalur PPG dan audio sama-sama memakai vitals_for_alert. Hanya nilai finite dengan kualitas eksplisit good dan umur record0–45s yang diteruskan. | Poor/unknown/null, stale, future timestamp dan nonfinite ditolak; fresh good tetap dapat membuat alert. Ada uji integrasi audio positif dan negatif, bukan sekadar menonaktifkan semua alert. |
| 04: DB lama | Semua factory/startup resmi memeriksa struktur sebelum create_all, ingestion atau MQTT. Import factory tidak membuka DB/subscriber. Ada migrator copy-only, backup konsisten WAL, archive4kelas, tambahan kolom kualitas NULL, integrity/FK/version checks dan publikasi atomik tanpa overwrite. | Startup legacy ditolak sebelum background; bootstrap baru; preservation source/rows; source WAL; target existing; versi tidak dikenal; kegagalan membersihkan temporary dan tidak menerbitkan target. |
| 05: MQTT | Validasi object JSON, topic, ID, timestamp, rate, array ADC, ukuran batch/payload dan panjang red/IR terjadi sebelum mutasi. Callback mengisolasi error handler, rollback/remove session, serta membuang parsial PPG yang tidak kontinu setelah error. | Array/null/string, bool/NaN/Inf/angka terlalu besar/negatif, red mismatch, spoof ID, topic salah, payload oversize, failure sesudah insert pending; pesan baik berikutnya tetap diproses. |

## Kebijakan data dan kompatibilitas

- `VITAL_ALERT_MAX_AGE_SECONDS=45` adalah batas operasional umur **record tersimpan**
  (tiga window PPG15s), bukan ambang fisiologis/klinis. Timestamp yang digunakan
  tetap UTC waktu pemrosesan/penyimpanan server; ini bukan pengukuran latensi akuisisi
  dari perangkat atau pembuktian jam ESP sudah sinkron.
- SQLite timestamp naive dibaca sebagai UTC. Timestamp masa depan tidak dipercaya
  untuk alert. Aturan kualitas diperiksa per metrik, sehingga HR poor tidak otomatis
  menghapus SpO2 yang good.
- Data vital lama diberi kualitas NULL/unknown. Nilai historis tetap ada; tidak
  dianggap good hanya karena angkanya tampak masuk akal. Alert lama tetap dipertahankan,
  bukan dihapus atau dinilai ulang diam-diam.
- Flag persistence historis tetap merekam keputusan pada saat disimpan; perubahan
  ambang tidak menulis ulang sejarah. Window tren dan semantik channel tidak diubah.
- Paket ESP32 tidak memerlukan field baru. Red tetap opsional untuk firmware lama,
  rate hilang tetap memakai default100Hz, dan battery-1 tetap unknown.
- Batas bernama: PPG_MAX_BATCH_SAMPLES2000, PPG_MAX_SAMPLE_RATE_HZ1000,
  PPG_MAX_SAMPLE_VALUE4294967295 dan MQTT_MAX_PAYLOAD_BYTES262144. Nilai tersebut
  merupakan batas transport/ADC, bukan angka klinis. Batch normal100 sample tetap valid.
- Raw history PPG dibatasi60 batch (~60s pada ritme nominal); sebelumnya angka6000
  dipakai sebagai jumlah batch, tidak sesuai komentar60s. Tidak ada persistensi raw
  PPG baru atau perubahan format jaringan.

## Pengujian

Semua pengujian menggunakan source checkout feature, bukan main:

- **369 passed**,32.91s: suite backend lengkap via `python -m pytest backend/tests -q`,
  langsung tanpa harness privat atau xfail. Model HTTP dimock eksplisit oleh fixture;
  database tes terpisah. Transport WebSocket lokal tetap termasuk.
- **77 passed**,4.74s: pengujian fokus audit, kualitas/freshness, audio alert, MQTT,
  dan migrasi. Pengujian threshold/status terkait93pass pada tahap fokus agen.
- Sebelum perbaikan: lima audit gagal; penambahan tes juga menemukan kegagalan
  threshold/status,22kasus MQTT dan beberapa kegagalan schema sebelum implementasi.
- `npm run lint` lulus. `npm run build` default Turbopack lulus, termasuk TypeScript
  dan18static pages. Frontend tidak diubah, ini regresi kompatibilitas.
- `git diff --check` bersih. Model AST asli tidak diuji karena artifact/service
  belum tersedia; tes mock tidak diklaim membuktikan akurasi atau kapasitas AST.

## Database demo aktual dan proses aktif

Backend lama dihentikan sebelum migrasi. Sumber tetap utuh:
`backend/demo-ready-two-class.db`. Target baru yang diverifikasi:
`backend/demo-ready-two-class-v1.db`.

Pada snapshot verifikasi, source/target sama-sama memuat4akun,2pasien,3device,
1pairing,978vital,8alert dan1647klasifikasi4kelas yang sudah diarsipkan sebelumnya.
Tabel klasifikasi2kelas dan tren sama-sama kosong. `integrity_check=ok`, tidak ada
pelanggaran foreign key, versi schema1. Tidak ada vital legacy yang dipaksa good.
Bukti angka: `five-fix-migration-verification.json` (tanpa identitas personal/nilai sensor).

Backend port5000 kini dijalankan dari checkout feature dengan target baru dan
`--allow-unavailable-model` yang sebelumnya dipakai untuk observasi. Health backend
mengembalikan200/statusok dan endpoint pasien tanpa login401. Port8000 AST belum
berjalan; itu tidak disamakan dengan kesiapan demo AI. Tidak ada fallback mock otomatis.

Saat restart setelah AST siap, dari checkout feature gunakan:

```bash
/path/ke/venv/bin/python -m backend.scripts.run_demo \
  --env-file /path/ke/software/backend/.env \
  --database backend/demo-ready-two-class-v1.db
```

Helper root `software/run-demo.sh` yang lama memilih DB lama secara default. Gunakan
`./run-demo.sh --database /path/absolut/ke/demo-ready-two-class-v1.db` untuk memilih
hasil upgrade secara eksplisit; jangan kembali ke file sumber lama. Guard akan
menolak skema lama dengan petunjuk migrasi, bukan mengubahnya otomatis.

Migrasi untuk instalasi lain (hentikan ingestion lebih dulu):

```bash
python -m backend.scripts.migrate_database --source OLD.db --target NEW.db
python -m backend.scripts.run_demo --database NEW.db --check
```

Target harus baru. Jangan menimpa file sumber atau mengganti DB saat server berjalan.

## Batas yang tetap terbuka

Tidak melakukan merge/push pada pekerjaan ini. Audit lain di luar lima perbaikan
(misalnya penanda data stale pada UI, unit tren per siklus/persistence lintas channel,
RR, validasi/kalibrasi dan artifact AST) tetap tercatat. Batch PPG valid yang rate-nya
berubah di tengah window juga belum mendapat lifecycle format baru pada patch ini.
Perbaikan lima bug aplikasi tidak menjadi bukti kehilangan audio fisik sudah hilang.
