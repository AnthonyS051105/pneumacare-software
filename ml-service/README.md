# PneumaCare ML Service

Service FastAPI untuk klasifikasi suara paru 2 kelas (`0` = normal,
`1` = abnormal). Service ini dipanggil oleh backend melalui HTTP dan dipisahkan
dari frontend/backend agar proses inference berat tidak membebani proses Flask.

## Struktur

```text
ml-service/
├── main.py                 # FastAPI: /health dan /predict
├── modules/model.py        # arsitektur AST + preprocessing audio
├── modules/weights/        # best.ckpt (982 MB, tidak di-commit)
├── samples/                # contoh WAV untuk uji manual
├── requirements.txt
├── .env.example
└── run.sh
```

## Environment Python

Untuk sementara service memakai environment pengembangan yang sudah ada di
`~/dev/pneumacare-ml-services/Env`. `run.sh` mendeteksinya otomatis, sehingga
dari root repo cukup menjalankan:

```bash
./ml-service/run.sh
```

Override interpreter bila perlu:

```bash
ML_PYTHON=/path/to/python ./ml-service/run.sh
```

Bila nanti ruang disk cukup, environment mandiri bisa dibuat di dalam repo:

```bash
/usr/bin/python3 -m venv ml-service/.venv
ml-service/.venv/bin/pip install --no-cache-dir -r ml-service/requirements.txt
```

`run.sh` akan memakai `ml-service/.venv` lebih dulu sebelum environment lama.
Python yang dipakai saat pengembangan: 3.12.

## Checkpoint

- Lokasi default: `ml-service/modules/weights/best.ckpt` (sekitar 982 MB).
- File ini **tidak boleh di-commit**; root `.gitignore` sudah mengabaikan `*.ckpt`.
- Jika checkpoint tidak ada, service tetap boot, tetapi `/health` melaporkan
  `model_loaded: false` dan `/predict` mengembalikan HTTP 503.
- Override path lewat environment atau `ml-service/.env`:

```bash
CHECKPOINT_PATH=/path/absolut/best.ckpt ./ml-service/run.sh
CHECKPOINT_PATH=modules/weights/best.ckpt ./ml-service/run.sh
```

Path relatif dihitung dari folder `ml-service/`, bukan dari direktori kerja.

## Menjalankan seluruh sistem

Dari root repo:

```bash
# 1. ML service (port 8000)
./ml-service/run.sh

# 2. Backend Flask (port 5000), gunakan environment Python backend yang tersedia
~/dev/pneumacare-ml-services/Env/bin/python -m backend.app

# 3. Frontend Next.js (port 3000)
npm run dev
```

Backend memakai `ML_SERVICE_URL=http://127.0.0.1:8000` secara default. Bila URL
dikosongkan di `backend/.env`, backend memakai mock inference tanpa memanggil
service ini.

## Kontrak API

```bash
curl -s http://127.0.0.1:8000/health
# {"status":"ok","model_loaded":true}

curl -s -F "file=@ml-service/samples/normal.wav" http://127.0.0.1:8000/predict
# {"filename":"normal.wav","class":0,"confidence":0.93,"probabilities":[0.93,0.07]}
```

- `POST /predict` menerima multipart field `file` berisi WAV.
- `class`: `0` normal, `1` abnormal.
- `probabilities`: `[p_normal, p_abnormal]`.
- Service juga menerima raw body, tetapi alur backend selalu memakai multipart.

## Catatan

- Model memakai feature extractor
  `MIT/ast-finetuned-audioset-10-10-0.4593` dari Hugging Face. Di mesin ini
  cache-nya sudah tersedia; mesin baru memerlukan akses internet saat pertama
  kali model asli dimuat.
- Service bind ke `0.0.0.0:8000`; hanya gunakan di jaringan lokal tepercaya.
- Jangan memindahkan/mengganti nama `modules/` atau `modules/model.py` tanpa
  menyesuaikan checkpoint dan `main.py`.
