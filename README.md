# PNEUMACARE

PNEUMACARE adalah prototipe sistem pemantauan pernapasan yang menghubungkan perangkat wearable berbasis ESP32 dengan layanan analisis dan dashboard web untuk pasien serta tenaga medis.

Perangkat mengumpulkan suara dari empat mikrofon dan sinyal PPG red/IR. Data tersebut digunakan untuk menampilkan hasil klasifikasi suara paru, estimasi denyut jantung dan SpO₂, tren pengukuran, serta peringatan berdasarkan konfigurasi pasien.

## Isi repository

Repository ini memuat sisi software PNEUMACARE:

- **Dashboard web** — Next.js dan TypeScript, dengan portal pasien dan tenaga medis, riwayat pengukuran, notifikasi, serta pengaturan ambang.
- **Backend** — Flask dan SQLAlchemy untuk autentikasi, pengelolaan perangkat, penerimaan audio melalui WebSocket, penerimaan PPG/status melalui MQTT, penyimpanan hasil, analisis tren, dan evaluasi peringatan.
- **ML service** — FastAPI dengan model Audio Spectrogram Transformer (AST) untuk klasifikasi suara paru dua kelas: `normal` dan `abnormal`.
- **Integrasi perangkat** — komunikasi dengan firmware ESP32 yang dikelola pada direktori hardware proyek induk.

Audio diterima pada 16 kHz per channel dan disusun menjadi segmen lima detik. Pemrosesan audio dijalankan melalui antrean terbatas agar penerimaan data dapat berlangsung terpisah dari inferensi. Backend meneruskan potongan siklus pernapasan yang terdeteksi ke ML service dan menyimpan hasilnya untuk dashboard.

## Status produk

PNEUMACARE masih dalam tahap pengembangan dan pengujian integrasi. Kontinuitas audio pada perangkat serta kapasitas model final masih perlu diverifikasi pada pengujian menyeluruh. Hasil klasifikasi dan estimasi vital merupakan informasi prototipe untuk skrining atau pemantauan, bukan diagnosis maupun pengganti penilaian tenaga medis.

Dokumentasi internal, konfigurasi rahasia, database lokal, dan checkpoint model tidak disertakan dalam Git. Kode arsitektur serta layanan inferensi tersedia di `ml-service/`.
