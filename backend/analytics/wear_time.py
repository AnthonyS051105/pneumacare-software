"""Hitung durasi pemakaian vest (wear-time) dari riwayat transisi status device
(UIUX_FLOW.md §3.1/§3.2, tabel `device_status_log` — SDD_SOFTWARE.md §3).

Fungsi murni: input = list StatusChange terurut waktu + batas rentang yang mau
dihitung, output = total durasi "online" dalam rentang tersebut. Dipisah dari
I/O (query DB) sesuai pola yang sama sejak Fase 1.

⚠️ "Wear-time" di sini adalah proksi dari status koneksi device (online/offline),
BUKAN sensor pemakaian fisik sungguhan (mis. tidak ada deteksi vest dilepas tapi
device tetap menyala) — device online diasumsikan sedang dipakai. Ini keterbatasan
yang perlu disebutkan jujur, bukan diklaim sebagai pengukuran wear-time presisi.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class StatusChange:
    status: str  # "online" | "offline"
    changed_at: datetime


def compute_online_duration_seconds(
    changes: list[StatusChange],
    range_start: datetime,
    range_end: datetime,
    status_before_range: str = "offline",
) -> float:
    """Total durasi status="online" dalam [range_start, range_end).

    `changes` HARUS sudah terurut menaik berdasarkan `changed_at` (tanggung jawab
    caller). `status_before_range` adalah status device tepat sebelum range_start
    dimulai (dari baris terakhir sebelum range, atau "offline" bila tidak ada
    riwayat sama sekali sebelum range — asumsi aman: device baru dianggap belum
    pernah online).
    """
    if range_end <= range_start:
        raise ValueError("range_end harus > range_start")

    total_seconds = 0.0
    current_status = status_before_range
    segment_start = range_start

    for change in changes:
        if change.changed_at <= range_start:
            current_status = change.status
            continue
        if change.changed_at >= range_end:
            break

        if current_status == "online":
            total_seconds += (change.changed_at - segment_start).total_seconds()

        segment_start = change.changed_at
        current_status = change.status

    if current_status == "online":
        total_seconds += (range_end - segment_start).total_seconds()

    return total_seconds


def compute_daily_online_hours(
    changes: list[StatusChange],
    day_start: datetime,
    day_end: datetime,
    status_before_range: str = "offline",
) -> float:
    """Wrapper `compute_online_duration_seconds` yang mengembalikan hasil dalam jam,
    dibulatkan 1 desimal — satuan yang dipakai UI (WearComplianceCard dkk.)."""
    seconds = compute_online_duration_seconds(changes, day_start, day_end, status_before_range)
    return round(seconds / 3600, 1)
