"""Agregasi riwayat klasifikasi Model A per rentang waktu (FR-SW-053: grafik tren
frekuensi wheeze/crackle di dashboard tenaga medis).

Fungsi murni: input = daftar (segment_end, kelas) hasil klasifikasi, output = hitungan
per bucket waktu. Dipisah dari I/O supaya bisa dites tanpa database.

"Frekuensi" di sini = proporsi segmen berlabel wheeze/crackle/both terhadap seluruh segmen
dalam bucket — sama dengan definisi frekuensi di trend_analysis (SDD_SOFTWARE.md §6), BUKAN
ukuran keparahan klinis. Bucket tanpa segmen tetap dikembalikan dengan total 0 supaya
frontend bisa menggambar jeda, bukan menyambung garis melewati data yang tidak ada.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta

CLASSES = ("none", "crackle", "wheeze", "both")


@dataclass(frozen=True)
class ClassifiedSegment:
    segment_end: datetime
    wheeze_crackle_class: str


def bucket_classifications(
    segments: list[ClassifiedSegment], start: datetime, end: datetime, bucket: timedelta
) -> list[dict]:
    """Hitung jumlah segmen per kelas untuk tiap bucket [start + i*bucket, start + (i+1)*bucket).

    Segmen di luar [start, end) diabaikan. Kelas yang tidak dikenal dihitung ke `total`
    tetapi tidak ke kelas manapun, supaya proporsi tidak diam-diam menggelembung.
    """
    if bucket <= timedelta(0):
        raise ValueError("bucket harus positif")
    if end <= start:
        return []

    n_buckets = -(-(end - start) // bucket)  # pembulatan ke atas
    rows = [
        {"bucket_start": start + i * bucket, "total": 0, **{c: 0 for c in CLASSES}}
        for i in range(n_buckets)
    ]
    for segment in segments:
        if not (start <= segment.segment_end < end):
            continue
        row = rows[(segment.segment_end - start) // bucket]
        row["total"] += 1
        if segment.wheeze_crackle_class in CLASSES:
            row[segment.wheeze_crackle_class] += 1

    return [
        {
            **row,
            "bucket_start": row["bucket_start"].isoformat(),
            "abnormal_ratio": (
                round((row["wheeze"] + row["crackle"] + row["both"]) / row["total"], 4) if row["total"] else None
            ),
        }
        for row in rows
    ]
