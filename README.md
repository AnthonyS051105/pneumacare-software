# PNEUMACARE

PNEUMACARE adalah prototipe sistem pemantauan pernapasan yang menghubungkan perangkat wearable berbasis ESP32 dengan layanan analisis dan dashboard web untuk pasien serta tenaga medis.

Perangkat mengumpulkan suara dari empat mikrofon dan sinyal PPG red/IR. Data tersebut digunakan untuk menampilkan hasil klasifikasi suara paru, estimasi denyut jantung dan SpO₂, tren pengukuran, serta peringatan berdasarkan konfigurasi pasien.

## Isi repository

Repository ini memuat sisi software PNEUMACARE:

- **Dashboard web** — Next.js dan TypeScript, dengan portal pasien dan tenaga medis, riwayat pengukuran, notifikasi, serta pengaturan ambang.
- **Backend** — Flask dan SQLAlchemy untuk autentikasi, pengelolaan perangkat, penerimaan audio melalui WebSocket, penerimaan PPG/status melalui MQTT, penyimpanan hasil, analisis tren, dan evaluasi peringatan.
- **ML service** — FastAPI dengan model Audio Spectrogram Transformer (AST) untuk klasifikasi suara paru dua kelas: `normal` dan `abnormal`.
- **Integrasi perangkat** — komunikasi dengan firmware ESP32 yang dikelola pada direktori hardware proyek induk.

Audio diterima pada 16 kHz per channel. Sistem mendukung segmen kontinu lima detik dan rekaman berkala dua detik dengan interval awal minimum 20 detik. Chunk dikirim sejak perekaman berlangsung, sedangkan antrean terbatas memisahkan penerimaan dari inferensi. Rekaman berkala dapat diarsipkan dan diklasifikasikan secara eksperimental, dengan hasil terpisah dari riwayat klasifikasi, tren, dan alert pasien.

## Status produk

PNEUMACARE masih dalam tahap pengembangan dan pengujian integrasi. Profil demo dapat memakai tiga mikrofon yang berfungsi dan satu channel salinan berpenanda untuk menguji beban pengiriman empat channel. Dukungan hardware empat mikrofon tetap dipertahankan; salinan tidak mewakili pengukuran posisi mikrofon yang rusak. Alert pasien dari rekaman pendek belum diaktifkan, dan pengukuran dengan seluruh sensor serta kelayakan klinis masih perlu divalidasi.

Hasil klasifikasi dan estimasi vital merupakan informasi prototipe untuk skrining atau pemantauan, bukan diagnosis maupun pengganti penilaian tenaga medis.

Dokumentasi internal, konfigurasi rahasia, database lokal, dan checkpoint model tidak disertakan dalam Git. Kode arsitektur serta layanan inferensi tersedia di `ml-service/`.
