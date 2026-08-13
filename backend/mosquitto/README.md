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

> Jika sistem sudah menjalankan mosquitto sebagai service (systemd `mosquitto.service`) dengan config default, hentikan dulu (`sudo systemctl stop mosquitto`) supaya tidak bentrok port 1883 sebelum menjalankan versi repo ini — atau cukup pakai service default itu langsung, karena config repo ini hanya menambahkan `allow_anonymous true` untuk kemudahan dev (service default biasanya sudah begitu juga di instalasi baru).

## 3. Uji broker jalan

Di terminal terpisah:
```bash
# subscribe ke topik status device (lihat INTEGRATION_CONTRACT.md §3.2)
mosquitto_sub -h localhost -t "pneumacare/+/status" -v

# di terminal lain, publish pesan uji
mosquitto_pub -h localhost -t "pneumacare/pneumacare-a1b2/status" \
  -m '{"device_id":"pneumacare-a1b2","status":"online","timestamp_ms":1723276800123,"battery_pct":87}'
```
Jika pesan uji muncul di terminal subscriber, broker sudah jalan dengan benar.

## 4. Topik yang dipakai (ringkasan dari INTEGRATION_CONTRACT.md §3.2)

| Topik | Arah |
|---|---|
| `pneumacare/{device_id}/ppg/raw` | ESP32 → Backend |
| `pneumacare/{device_id}/alert` | Backend → Dashboard |
| `pneumacare/{device_id}/status` | ESP32 → Backend (retained) |

`mqtt_subscriber.py` (belum diimplementasikan — Fase 1) akan connect ke broker ini menggunakan `MQTT_BROKER_HOST`/`MQTT_BROKER_PORT` dari `backend/config.py`.
