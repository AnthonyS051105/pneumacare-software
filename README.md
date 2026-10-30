# PNEUMACARE

PNEUMACARE adalah prototipe sistem pemantauan pernapasan yang menghubungkan perangkat wearable berbasis ESP32 dengan layanan analisis dan dashboard web untuk pasien serta tenaga medis.

Perangkat mengumpulkan suara dari empat mikrofon dan sinyal PPG red/IR. Data tersebut digunakan untuk menampilkan hasil klasifikasi suara paru, estimasi denyut jantung dan SpO₂, tren pengukuran, serta peringatan berdasarkan konfigurasi pasien.

## Isi repository

Repository ini memuat sisi software PNEUMACARE:

- **Dashboard web** — Next.js dan TypeScript, dengan portal pasien dan tenaga medis, riwayat pengukuran, notifikasi, serta pengaturan ambang.
- **Backend** — Flask dan SQLAlchemy untuk autentikasi, pengelolaan perangkat, penerimaan audio melalui WebSocket, penerimaan PPG/status melalui MQTT, penyimpanan hasil, analisis tren, dan evaluasi peringatan.
- **ML service** — FastAPI dengan model EfficientNet-B0 untuk klasifikasi suara paru dua kelas: `normal` dan `abnormal`.
- **Integrasi perangkat** — komunikasi dengan firmware ESP32 yang dikelola pada direktori hardware proyek induk.

Audio diterima pada 16 kHz per channel. Sistem mendukung segmen kontinu lima detik dan rekaman berkala dua detik dengan interval awal minimum 20 detik. Chunk dikirim sejak perekaman berlangsung, sedangkan antrean terbatas memisahkan penerimaan dari inferensi. Rekaman berkala diklasifikasikan otomatis oleh model yang tersedia. Hasil abnormal pada mikrofon yang sama memicu **Info** pada rekaman pertama, **Warning** pada dua rekaman berturut-turut, dan **Urgent** berwarna merah pada tiga rekaman berturut-turut. Aturan persistensi ini dapat dikonfigurasi, dengan sumber rekaman tersimpan dan notifikasi berulang dibatasi. Mode notifikasi aktif secara default; kegagalan model tidak diganti prediksi mock.

Hitungan abnormal terpisah per mikrofon dan sesi; channel salinan tidak menambah hitungan. Hasil normal, rekaman yang terlewat, pergantian sesi/model, atau jeda terlalu lama memutus hitungan. Hasil dua detik tetap berlabel eksperimental dan terpisah dari perhitungan tren kontinu lima detik. Level notifikasi menunjukkan prioritas peninjauan, bukan diagnosis atau tingkat keparahan penyakit yang telah tervalidasi; hasil normal tidak membuktikan tidak adanya gangguan selama jeda perekaman.

## Status produk

PNEUMACARE masih dalam tahap pengembangan dan pengujian integrasi. Profil demo dapat memakai tiga mikrofon yang berfungsi dan satu channel salinan berpenanda untuk menguji beban pengiriman empat channel. Dukungan hardware empat mikrofon tetap dipertahankan; salinan tidak mewakili pengukuran posisi mikrofon yang rusak dan tidak memicu notifikasi. Klasifikasi dan notifikasi informasi otomatis dari rekaman pendek tersedia untuk demo prototipe; pengukuran dengan seluruh sensor serta kelayakan klinis masih perlu divalidasi.

Hasil klasifikasi dan estimasi vital merupakan informasi prototipe untuk skrining atau pemantauan, bukan diagnosis maupun pengganti penilaian tenaga medis.

Dokumentasi internal, konfigurasi rahasia, database lokal, dan checkpoint model tidak disertakan dalam Git. Kode arsitektur serta layanan inferensi tersedia di `ml-service/`.
