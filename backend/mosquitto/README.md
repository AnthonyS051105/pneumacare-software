# Mosquitto — setup development lokal

Broker MQTT ini **tidak diinstall otomatis oleh Claude Code** (di luar akses filesystem sesi ini). Ikuti langkah manual berikut.

## 1. Install Mosquitto

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install mosquitto mosquitto-clients
```

**macOS (Homebrew):**
```bash
brew install mosquitto
```

**Windows:** unduh installer dari https://mosquitto.org/download/

## 2. Jalankan broker dengan config repo ini (bukan service default OS)

Supaya pakai `mosquitto.conf` di folder ini (bukan config sistem), jalankan manual dari folder `backend/mosquitto/`:

```bash
cd backend/mosquitto
mkdir -p data
mosquitto -c mosquitto.conf -v
```

Broker akan listen di `localhost:1883` sesuai `INTEGRATION_CONTRACT.md` §3.1.

> Jika sistem sudah menjalankan mosquitto sebagai service (systemd `mosquitto.service`) dengan config default (biasanya `allow_anonymous true`, tanpa password_file), config repo ini **berbeda** — sekarang mewajibkan auth (lihat §2.1 di bawah). Hentikan service default dulu (`sudo systemctl stop mosquitto`) supaya tidak bentrok port 1883, lalu jalankan versi repo ini secara manual seperti di atas.

### 2.1 Wajib: buat password_file sebelum broker bisa dipakai

Sejak auth diaktifkan (INTEGRATION_CONTRACT.md §6), `mosquitto.conf` di folder ini set `allow_anonymous false` + `password_file ./passwd`. Broker akan **menolak semua koneksi** (termasuk `mqtt_subscriber.py` backend sendiri) sampai file `passwd` ini dibuat, berisi minimal 2 user:

1. **User backend** (dipakai `mqtt_subscriber.py` untuk subscribe) — isi `MQTT_USERNAME`/`MQTT_PASSWORD` di `backend/.env` dengan kredensial yang sama.
2. **User device** (dipakai firmware ESP32 untuk publish) — password-nya **harus sama** dengan `DEVICE_AUTH_TOKEN` di `backend/.env`, supaya satu token dipakai konsisten untuk WS dan MQTT (sesuai INTEGRATION_CONTRACT.md §6).

```bash
cd backend/mosquitto

# buat file baru + user backend (ganti <password> dengan MQTT_PASSWORD kamu)
mosquitto_passwd -c passwd backend

# tambah user device (password HARUS = DEVICE_AUTH_TOKEN di backend/.env)
mosquitto_passwd passwd pneumacare-device
```
`mosquitto_passwd` akan minta password secara interaktif. File `passwd` berisi hash, jangan di-commit (sudah ada di `.gitignore`? cek dulu — kalau belum, tambahkan).

Lalu isi `backend/.env`:
```
MQTT_USERNAME=backend
MQTT_PASSWORD=<password backend di atas>
DEVICE_AUTH_TOKEN=<password user pneumacare-device di atas>
```
Dan di firmware `include/secrets.h`, `DEVICE_API_TOKEN` **harus persis sama** dengan `DEVICE_AUTH_TOKEN` ini — dipakai baik sebagai bearer token WS maupun password MQTT device.

## 3. Uji broker jalan

Di terminal terpisah (pakai kredensial user backend dari §2.1):
```bash
# subscribe ke topik status device (lihat INTEGRATION_CONTRACT.md §3.2)
mosquitto_sub -h localhost -t "pneumacare/+/status" -v -u backend -P <password backend>

# di terminal lain, publish pesan uji sebagai device
mosquitto_pub -h localhost -t "pneumacare/pneumacare-a1b2/status" \
  -m '{"device_id":"pneumacare-a1b2","status":"online","timestamp_ms":1723276800123,"battery_pct":87}' \
  -u pneumacare-device -P <DEVICE_AUTH_TOKEN>
```
Jika pesan uji muncul di terminal subscriber, broker sudah jalan dan auth-nya benar. Kalau koneksi ditolak (`Connection Refused: not authorised`), cek ulang §2.1.

## 4. Topik yang dipakai (ringkasan dari INTEGRATION_CONTRACT.md §3.2)

| Topik | Arah |
|---|---|
| `pneumacare/{device_id}/ppg/raw` | ESP32 → Backend |
| `pneumacare/{device_id}/alert` | Backend → Dashboard |
| `pneumacare/{device_id}/status` | ESP32 → Backend (retained) |

`mqtt_subscriber.py` connect ke broker ini menggunakan `MQTT_BROKER_HOST`/`MQTT_BROKER_PORT`/`MQTT_USERNAME`/`MQTT_PASSWORD` dari `backend/config.py` (env `backend/.env`).
