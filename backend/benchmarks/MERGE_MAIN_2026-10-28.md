# Integrasi feat/ai-integration ke main

Atas permintaan Tony, `feat/ai-integration` pada `4fcd549` digabungkan ke
`main` pada `44fa5b7`. Implementasi AST dua kelas serta lima perbaikan audit
dipertahankan. Konflik pada inference, konfigurasi, WebSocket dan tes diselesaikan
mengikuti feature; preprocessing MobileNet lama dihapus sesuai feature.

Validasi pada source hasil merge:

- `backend/venv/bin/python -m pytest backend/tests -q`: **369 passed, 21.88s**.
- `npm run lint`: lulus setelah folder worktree dan Python venv dikecualikan.
- `npm run build -- --webpack`: lulus, termasuk TypeScript dan 18 halaman statis.
- `npm run build` (Turbopack): gagal karena subprocess CSS tidak diizinkan bind
  port lokal (`Operation not permitted`), termasuk saat dicoba dengan eskalasi.
  Keberhasilan webpack tidak dinyatakan sebagai keberhasilan Turbopack.
- `bash -n run-demo.sh`: lulus.
- `./run-demo.sh --check`: exit 2, `model_loaded:false`, `mock_explicit:false`.
  Ini keluaran readiness yang diharapkan ketika AST belum tersedia.

Launcher sekarang memakai source root yang sudah digabungkan dan DB hasil upgrade
yang sudah tersedia di worktree feature (`demo-ready-two-class-v1.db`). Database
lama root tidak dimodifikasi. Path DB dapat diganti melalui `--database`.
Proses backend yang sebelumnya berjalan tidak direstart oleh merge.

Benchmark MobileNet historis tetap disimpan untuk reproduksi pada revision
`d1a48df`; guard baru memberi pesan jelas jika dijalankan pada source AST.
Hasil benchmark lama tidak menjadi bukti kapasitas AST.

Merge ini tidak menyelesaikan drop transport ESP32 yang masih teramati dan tidak
memvalidasi kapasitas/akurasi AST asli. Checkpoint final dan uji perangkat stabil
10–15 menit tetap diperlukan. Lihat CURRENT_STATUS.md dan FIX_FIVE_AUDIT_2026-10-28.md.
