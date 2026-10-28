This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Dokumentasi aliran data

Lihat [README_DATA_FLOW.md](./README_DATA_FLOW.md) untuk diagram dan penjelasan
aliran data dari perangkat ESP32, backend, ML service, hingga website.

## Backend demo dan upgrade database

Acuan demo adalah branch `feat/ai-integration`, dengan AST dua kelas
`normal`/`abnormal`. Dari root software, gunakan environment Python backend:

```bash
python -m backend.scripts.run_demo --database backend/demo-ready-two-class.db --check
python -m backend.scripts.run_demo --database backend/demo-ready-two-class.db
```

ML service harus memuat checkpoint asli sebelum demo inferensi. Opsi
`--allow-unavailable-model` hanya untuk diagnostik transport dan tidak membuktikan
kapasitas/akurasi model. Wrapper menjalankan satu proses tanpa debug reloader.
`python -m backend.app` tetap tersedia untuk pengembangan; factory `create_app`
dan WSGI `backend.app:app` memakai pemeriksaan skema yang sama sebelum ingestion.
Mengimpor `create_app` saja tidak membuka database atau memulai subscriber.

Jika startup melaporkan **incompatible database schema**, hentikan backend dan
migrasikan ke **file baru**, menggunakan database yang benar-benar dipilih oleh
`DATABASE_URL` atau `--database`:

```bash
python -m backend.scripts.migrate_database --source backend/old.db --target backend/upgraded.db
python -m backend.scripts.run_demo --database backend/upgraded.db --check
```

Migrator mengambil snapshot konsisten SQLite (termasuk WAL), memeriksa integritas
dan foreign key, lalu mempublikasikan hasil secara atomik. File sumber tidak
berubah; target yang sudah ada ditolak. Kegagalan tidak meninggalkan target
setengah jadi sehingga perintah dapat diulang dengan target yang sama. Jika
berhasil, pilih target secara eksplisit saat startup dan simpan sumber sebagai
cadangan. Jangan menimpa sumber atau mengganti file database saat server berjalan.

Akun, pairing, ambang pasien, serta vital dipertahankan. Hasil empat kelas,
tren, dan alert lama disimpan pada tabel `*_legacy_four_class`; hasil tersebut
tidak dikonversi menjadi prediksi AST. Kolom kualitas vital lama diisi `NULL`
(unknown), sehingga angka lama tidak otomatis dipercaya untuk membuat alert.
Database baru yang kosong dapat dibuat saat startup; database lama yang kolomnya
tidak cocok ditolak dengan petunjuk migrasi. Migrator mencatat versi skema dan
menolak versi yang tidak dikenali; ini bukan migrator umum untuk semua perubahan
skema masa depan. Perintah lama `prepare_demo_database` memakai migrator yang sama.

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.
