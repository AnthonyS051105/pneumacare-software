# Audit sebelum merge — feat/ai-integration

Tanggal: 28 Oktober 2026, Asia/Jakarta.

**Keputusan: BELUM MERGE ke main.** Lima temuan backend dapat direproduksi sebagai
kegagalan assertion; ada pula gap tampilan data lama dan batas validasi demo.
AST dua kelas **normal/abnormal diterima sebagai keputusan Tony**, bukan defect.

## Lingkup dan provenance

- Acuan kode yang diuji: `.worktrees/feat-ai-integration-demo`, branch
  `feat/ai-integration`, base `b177a81` + perbaikan lokal sebelumnya dan tes audit baru.
- `git fetch origin main feat/ai-integration` mengonfirmasi remote feature tetap
  `b177a81`, remote main `91271a2` saat audit. Source main tidak dipakai untuk testing.
- Checkpoint perubahan main sebelumnya disimpan lokal sebagai `d1a48df`.
  Tidak push dan tidak merge. Tidak mengubah gain, firmware, jaringan atau server aktif
  pada audit ini; bukti hardware sebelumnya hanya dirujuk, bukan diklaim diulang.
- Dokumen: PRD, SRS, SDD, kontrak, UIUX, task breakdown dan backlog pada root `docs/`.
  Sidik tujuh dokumen dan matriks requirement ada pada
  `AUDIT_REQUIREMENTS_MATRIX_2026-10-28.md`.
- Model/service/preprocessing2kelas/16kHz adalah pengecualian baseline yang disetujui.
  Keputusan tersebut tidak otomatis mengubah aturan kualitas vital atau status alert.

Semua lokasi kode berikut relatif terhadap **checkout feature**, bukan main.
Temuan warisan main tetap relevan untuk keamanan merge, tetapi tidak dituduhkan
sebagai regresi yang dibuat teman pengembang model.

## Temuan yang menghalangi merge aman

### AUDIT-01 — P1: ambang tren per pasien tidak menentukan signifikansi

Bukti: `backend/trend_analysis/trend_service.py:40,58` memakai ambang global.
`backend/alerting/alert_service.py:80` membaca ambang pasien, tetapi
`backend/alerting/alert_engine.py:218` hanya memeriksa `trend_result.significant`
yang sebelumnya sudah dihitung; ambang pasien akhirnya hanya masuk metadata trigger.

Reproduksi: simpan `trend_significance_threshold=999` pada fixture pasien, hasilkan
slope0.171428. Expected `significant=False`, actual **True**. Ini melanggar maksud
FR-SW-023/055: pengaturan yang disimpan clinician harus memengaruhi evaluasi.

Arah perbaikan: satu sumber resolusi ambang pasien/default untuk perhitungan tren,
persistensi dan alert. Uji ambang lebih tinggi, lebih rendah, serta pasien tanpa
ambang. Tidak perlu mengubah nilai klinis default untuk membetulkan alur ini.

### AUDIT-02 — P1: status pasien dapat menyembunyikan alert darurat aktif

Bukti: `backend/api/patient_routes.py:129–140` mengambil **alert terbaru saja**.
Bila sudah acknowledged, status stable meski alert3 sebelumnya belum ditinjau.

Reproduksi: fixture memiliki vital terbaru, alert3 lama unacknowledged dan alert1
baru acknowledged. Endpoint summary mengembalikan **stable**, expected urgent.
Ini bukan masalah pemilihan dua kelas. FR-SW-065 dan UIUX§3.1 meminta ringkasan
status yang tidak menyembunyikan kondisi peringatan aktif.

Arah perbaikan: hitung status dari alert aktif tertinggi, terpisah dari pemilihan
notifikasi terbaru. Uji alert campuran, semua acknowledged, device offline dan
belum ada data. Perlakuan level1 mengikuti keputusan UX, bukan asumsi audit.

### AUDIT-03 — P1: jalur audio membypass kualitas PPG

Bukti: `backend/ingestion/mqtt_subscriber.py:72–83` menyimpan hasil numerik poor
ke ReadingVital tanpa confidence; `:97–105` memfilter kualitas hanya pada evaluasi
langsung PPG. `backend/ingestion/websocket_server.py:247–255` membaca kembali nilai
terbaru tanpa kualitas/umur, lalu mengirimkannya ke alert engine.

Reproduksi: estimator fixture mengembalikan HR25 dengan confidence poor. Evaluasi
langsung PPG menghasilkan0alert; setelah satu segmen audio mock, muncul **alert2**
berdasarkan vital yang sama. Nilai fixture adalah data uji, bukan ambang klinis.

Arah perbaikan: simpan provenance/kualitas dan freshness yang dapat dipakai semua
pemanggil alert; jangan membetulkan hanya jalur PPG. Perubahan skema perlu jalur
migrasi. Penanganan vital terlalu lama juga perlu batas operasional eksplisit.

### AUDIT-04 — P1: jalur startup standar tidak melindungi database lama

Bukti: `backend/app.py:45–46` hanya `create_all()`; skema klasifikasi berubah dari
wheeze_crackle_* ke predicted_class/confidence/probabilities/model_version.
`run_demo.py` sudah mempunyai guard, tetapi README/CLAUDE masih mendokumentasikan
`python -m backend.app`, yang tidak memanggil guard tersebut.

Reproduksi: factory diberi SQLite sementara dengan tabel klasifikasi legacy.
Startup tidak menolak skema tersebut; assertion fail-fast gagal. `create_all`
tidak mengubah kolom existing, sehingga query ORM dua kelas tidak kompatibel.
Snapshot DB demo sebelumnya adalah workaround yang bekerja pada mesin ini,
bukan migrasi/guard yang otomatis berlaku untuk pengguna entrypoint standar.

Arah perbaikan: jadikan pemeriksaan skema bagian startup resmi, berikan pesan
migrasi yang jelas, serta satukan petunjuk peluncuran. Pertahankan backup/data
lama; jangan drop atau relabel data empat kelas seolah prediksi AST.

### AUDIT-05 — P1: JSON MQTT valid dengan tipe salah lolos sebagai exception

Bukti: `backend/ingestion/mqtt_subscriber.py:236–245` menangkap decode JSON saja,
lalu handler menganggap payload dict. Payload valid `[]` menyebabkan `.get`
AttributeError di `:114`. Paho client tidak mengaktifkan suppress_exceptions;
exception callback dapat menghentikan thread jaringan subscriber.

Reproduksi: panggil callback client tanpa broker menggunakan topik ppg/raw dan
payload `[]`. Expected pesan ditolak dengan callback tetap kembali normal;
actual **AttributeError** keluar. Tidak mengirim pesan ke broker pengguna.

Arah perbaikan: validasi object, array numerik, rate, panjang red/IR dan batas
batch; isolasi exception pemrosesan per pesan dengan rollback/cleanup yang benar,
lalu uji pesan baik sesudah pesan buruk. Jangan mencetak payload atau token.

## Temuan frontend dan kesesuaian lain

| Prioritas | Temuan dan bukti | Batas verifikasi / tindakan |
|---|---|---|
| P1/P2 | Poll error diabaikan tanpa batas: `PatientData.tsx:66–67`, `useApi.ts:53–60`. `Connection.tsx:30–39` tetap menggambar online dari cache. | Source-verified; belum diuji shutdown lewat browser. Pertahankan histori, tetapi tampilkan server tak terjangkau/data belum diperbarui dan waktu keberhasilan terakhir. Jangan menyamakan server down dengan bukti device pasti offline. |
| P2 | `clinicianPatients.ts:21–25` mengembalikan stable untuk device online tanpa vital; label daftar menjadi Stabil. | Fungsi aktual dijalankan dengan fixture online+vital null, hasil stable. Halaman pasien sudah punya NO_DATA guard, daftar clinician belum setara. |
| P2 | `usePatientHistory.ts:23–48` tidak memasang polling; PatientHomeView memakainya untuk grafik. | Source-verified: angka summary dapat diperbarui15s, grafik tetap snapshot awal hingga key/range berubah. |
| P2 | Label jumlah/rasio masih segmen, padahal data per siklus atau fallback5s (`PatientDetail.tsx:439,500,524`). | Hitungan valid untuk baris klasifikasi, tetapi bukan rasio segmen5s seragam. Ubah label/unit atau keputusan agregasi secara eksplisit. |
| P2 | API pasien masih mengirim predicted_class/confidence (`patient_routes.py:165–168`). | Tidak ditemukan confidence ditampilkan pada UI pasien utama; ini gap batas kontrak informasi clinician/pasien, bukan kebocoran data pasien lain. |
| Desain terbuka | Enam baris tren kini bisa enam siklus; persistence mengambil histori device tanpa channel_id. | Belum ada dasar menyebutnya window30s atau persistence per channel. Skema lama memang device-level; putuskan semantik sebelum perubahan skema/tuning. |
| Konsistensi | Classification dan metadata siklus di-commit terpisah. | Job gagal pada commit kedua dapat meninggalkan classification tanpa metadata. Belum diuji fault injection DB pada audit ini. |
| Dokumen | Footer README_DATA_FLOW masih menyebut mock otomatis saat503 dan DTW menahan receiver. | Sudah salah terhadap patch worker/fail-closed. Dokumen historis PRD/SRS/SDD masih punya10s/22kHz/4kelas; catatan override baru harus dijadikan baseline konsisten. |

## Yang sesuai dan pengecualian yang sah

- Jalur normal/abnormal konsisten pada API, tipe, UI clinician, probabilitas dan
  service. Tidak ditemukan asumsi empat kelas yang tersisa di `src/`.
- Backend tetap memiliki per-channel segmentation, FIFO bounded, snapshot immutable,
  pembatalan gap/sesi, auth perangkat, MQTT PPG/status, dan penyimpanan hasil.
- Perbaikan sebelumnya (receiver terpisah, gap tidak digabung, sample index v2,
  cancellation takeover, worker recovery, no automatic mock, duplicate-current
  persistence, strict AST response validation, pre-NTP fallback dan ping cleanup)
  sudah ada pada checkout yang diaudit. Tidak dilaporkan ulang sebagai bug aktif.
- Role dan kepemilikan data ditegakkan di backend, password hash, pairing dan guard
  portal tersedia. Ini bukan penetration test atau audit keamanan produksi lengkap.
- Disclaimer skrining/belum tervalidasi klinis dan ModelB belum tersedia ditampilkan;
  perubahan dua kelas tidak berarti severity PPOK atau diagnosis kini tersedia.

## Batas demo / validasi yang terpisah dari bug kode

RR masih selaluNone pada ingestion PPG; sumber/metodenya memang belum diputuskan
pada SDD. Kalibrasi SpO2, ambang klinis dan parameter tren masih placeholder yang
perlu tim/dosen. Tidak diisi angka baru oleh audit. Provenance simulator/mock belum
menjadi badge end-to-end yang konsisten.

AST best.ckpt/environment/cache extractor belum tersedia pada pemeriksaan sebelumnya;
kapasitas, mapping artifact/training dan offline cold-start belum dibuktikan. Pada
host CUDA, main.py memindah model ke CUDA tetapi predict belum memindah tensor input;
ini risiko conditional, bukan crash yang diuji pada GPU di mesin ini.

Hasil fisik sebelumnya menunjukkan drop tetap terjadi bahkan pada receive-only dan
power-save off. Audit ini **tidak mengulang tes hardware** dan tidak mengklaim bahwa
pergantian branch menyelesaikan transport. Detail pada CURRENT_STATUS.md.

## Pengujian pada feat/ai-integration saja

- Suite backend lengkap: **277 passed,4 xfailed**,26.34s; empat xfail adalah reproduksi
  audit pertama yang saat itu sudah ditambahkan. Sesudahnya ditambahkan reproduksi
  MQTT; focused audit normal **5 xfailed**,0.76s.
- Reproduksi tanpa xfail (`--runxfail`): **5 failed**,0.80s, sesuai temuan di atas.
  File `backend/tests/test_audit_known_gaps.py` memakai strict xfail yang eksplisit;
  ini penanda bug terbuka, **bukan alasan menyatakan seluruh tes lulus/aman merge**.
  Output bukti: `audit-reproductions.txt`.
- Backend harness menggunakan app/db sementara dan ML_SERVICE_URL kosong secara
  eksplisit; startup MQTT global distub untuk tidak menduplikasi subscriber pengguna.
  Auth, DB dan transport HTTP/WS lokal tetap diuji. Model AST asli tidak dipakai.
- `npm run lint`: lulus. `npm run build -- --webpack` di host: lulus, TypeScript dan
 18static pages sukses. TypeScript standalone sesudah generation juga lulus.
- `npm run build` default (Turbopack) juga lulus setelah dependency identik lockfile
  tersedia lokal di worktree. Kegagalan awal default berasal dari node_modules yang
  masih berada di luar filesystem root Turbopack; tidak mengubah source/config.
- Build awal sandbox gagal parsing output subprocess TypeScript; build host sukses,
  sehingga kegagalan sandbox itu **tidak dilaporkan sebagai bug kode branch**.
- Checkpoint main tidak diuji ulang pada pekerjaan ini, sesuai instruksi Tony.

## Syarat sebelum merge

Selesaikan lima repro blocker, tambah uji data stale pada portal, satukan startup/
upgrade DB, lalu jalankan ulang semua tes dengan **nol reproduksi audit terbuka**.
Tetapkan unit tren/persistence dan status validasi yang dibutuhkan demo; jangan
mengubah model ke empat kelas untuk mengatasi temuan yang tidak berkaitan model.

Tidak ada merge atau push dilakukan. Laporan ini tidak menyatakan semua aspek
aplikasi aman hanya karena build dan suite regresi lama lulus.
