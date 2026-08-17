"""Catatan pola otomatis sederhana dari riwayat vital (UIUX_FLOW.md §3.2,
PatternInsightCard) — bandingkan rata-rata HR per rentang jam, laporkan rentang
paling stabil (deviasi dari rata-rata keseluruhan paling kecil).

⚠️ Ini heuristik sederhana untuk demo, BUKAN analisis statistik yang divalidasi
klinis — "paling stabil" didefinisikan sebagai rentang jam dengan variansi HR
terendah dibanding rata-rata keseluruhan. Kalimat yang dihasilkan HARUS tetap
netral/tidak menyiratkan interpretasi medis (SDD_SOFTWARE.md §8, prinsip
"skrining bukan diagnosis").

Fungsi murni: input = list (timestamp, hr) dari readings_vital, output = teks
insight bahasa awam. Dipisah dari I/O sesuai pola sejak Fase 1.
"""

from dataclasses import dataclass
from datetime import datetime
from statistics import mean, pstdev

# Rentang jam yang dibandingkan — pembagian umum siang/sore/malam/dini hari,
# bukan hasil kalibrasi klinis apapun, sekadar pengelompokan yang mudah dipahami.
_TIME_BUCKETS = [
    ("pagi", 5, 11),
    ("siang", 11, 15),
    ("sore", 15, 18),
    ("malam", 18, 23),
    ("dini hari", 23, 5),  # wrap-around
]


@dataclass(frozen=True)
class VitalPoint:
    timestamp: datetime
    hr: float | None


def _bucket_for_hour(hour: int) -> str:
    for label, start, end in _TIME_BUCKETS:
        if start < end:
            if start <= hour < end:
                return label
        else:  # wrap-around (dini hari: 23-24 dan 0-5)
            if hour >= start or hour < end:
                return label
    return "dini hari"


def compute_most_stable_period(points: list[VitalPoint]) -> str | None:
    """Cari rentang waktu (pagi/siang/sore/malam/dini hari) dengan HR paling stabil.

    Return None bila data terlalu sedikit untuk kesimpulan bermakna (< 2 bucket
    yang masing-masing punya >= 2 titik data) — lebih baik tidak menampilkan
    insight daripada menampilkan kesimpulan dari data terlalu sedikit.
    """
    buckets: dict[str, list[float]] = {}
    for point in points:
        if point.hr is None:
            continue
        label = _bucket_for_hour(point.timestamp.hour)
        buckets.setdefault(label, []).append(point.hr)

    eligible_buckets = {label: values for label, values in buckets.items() if len(values) >= 2}
    if len(eligible_buckets) < 2:
        return None

    most_stable_label = min(eligible_buckets, key=lambda label: pstdev(eligible_buckets[label]))
    return most_stable_label


def generate_pattern_insight(points: list[VitalPoint]) -> str | None:
    """Hasilkan satu kalimat bahasa awam untuk PatternInsightCard.

    Return None bila tidak ada insight yang bisa disimpulkan (data terlalu
    sedikit) — caller (endpoint) bertanggung jawab menyembunyikan card bila None,
    BUKAN menampilkan kalimat kosong atau mengarang kesimpulan.
    """
    most_stable = compute_most_stable_period(points)
    if most_stable is None:
        return None
    return f"Detak jantung Anda paling stabil di {most_stable} hari."
