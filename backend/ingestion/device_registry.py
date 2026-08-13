"""Upsert atomik untuk tabel `devices`, dipakai oleh websocket_server dan mqtt_subscriber.

Kedua modul berjalan di thread terpisah (Flask request thread untuk websocket,
paho-mqtt background thread untuk MQTT) dan bisa menerima data dari device yang
sama nyaris bersamaan saat device itu baru pertama kali terlihat. Read-then-insert
biasa (query lalu `db.session.add`) rentan race condition (dua thread sama-sama
tidak menemukan baris lalu sama-sama insert -> UNIQUE constraint error). Insert
`ON CONFLICT DO UPDATE` atomik di level database menghindari ini.
"""

from datetime import datetime, timezone

from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from backend.models import db
from backend.models.device import Device


def upsert_device_seen(device_id: str, **extra_fields) -> None:
    """Pastikan baris `devices` ada dan `last_seen_at`/`status` ter-update, atomik.

    `extra_fields` bisa berisi kolom lain yang perlu diperbarui bersamaan
    (mis. `battery_percent`) — nilai lama dipertahankan bila tidak disertakan.
    """
    now = datetime.now(timezone.utc)
    values = {"device_id": device_id, "status": "online", "last_seen_at": now, **extra_fields}

    stmt = sqlite_insert(Device).values(**values)
    update_fields = {k: v for k, v in values.items() if k != "device_id"}
    stmt = stmt.on_conflict_do_update(index_elements=["device_id"], set_=update_fields)

    db.session.execute(stmt)
    db.session.commit()
