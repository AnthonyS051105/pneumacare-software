"""Fixture data simulasi untuk modul trend analysis (FR-SW-024, SRS_SOFTWARE.md §2.3).

Data longitudinal nyata belum tersedia (baru subjek sehat/simulasi, lihat PRD_SOFTWARE.md
§2), jadi modul trend analysis HARUS bisa diuji dan didemokan dengan skenario sintetis
yang jujur dilabeli sebagai simulasi — bukan data pasien sungguhan.

Tiap skenario menghasilkan list ClassificationEvent yang mensimulasikan hasil klasifikasi
per segmen 5 detik (INTEGRATION_CONTRACT.md §4.1) selama beberapa menit, dengan pola
frekuensi abnormal yang berbeda: naik, turun, atau stabil.
"""

from datetime import datetime, timedelta

from backend.trend_analysis.rolling_window import ClassificationEvent

SEGMENT_DURATION = timedelta(seconds=5)
_BASE_TIMESTAMP = datetime(2026, 1, 1, 8, 0, 0)


def _build_events(abnormal_pattern: list[bool]) -> list[ClassificationEvent]:
    return [
        ClassificationEvent(
            timestamp=_BASE_TIMESTAMP + i * SEGMENT_DURATION,
            predicted_class="abnormal" if is_abnormal else "normal",
        )
        for i, is_abnormal in enumerate(abnormal_pattern)
    ]


def rising_abnormal_scenario(n_segments: int = 60) -> list[ClassificationEvent]:
    """Simulasi tren NAIK: abnormal makin sering muncul seiring waktu.

    Paruh pertama jarang abnormal, paruh kedua nyaris selalu abnormal — pola tangga naik,
    bukan acak, supaya slope regresi pasti positif dan jelas signifikan untuk demo.
    """
    pattern = []
    for i in range(n_segments):
        progress = i / max(n_segments - 1, 1)
        abnormal_probability_threshold = 1 - progress  # makin ke akhir, makin sering True
        pattern.append((i % 4) / 4 >= abnormal_probability_threshold)
    return _build_events(pattern)


def falling_abnormal_scenario(n_segments: int = 60) -> list[ClassificationEvent]:
    """Simulasi tren TURUN: abnormal sering di awal, makin jarang seiring waktu (mis. kondisi membaik)."""
    rising = rising_abnormal_scenario(n_segments)
    reversed_pattern = [e.predicted_class == "abnormal" for e in reversed(rising)]
    return _build_events(reversed_pattern)


def stable_abnormal_scenario(n_segments: int = 60, abnormal_every: int = 5) -> list[ClassificationEvent]:
    """Simulasi tren STABIL: abnormal muncul dengan frekuensi konstan (tiap `abnormal_every` segmen)."""
    pattern = [(i % abnormal_every == 0) for i in range(n_segments)]
    return _build_events(pattern)


def no_abnormal_scenario(n_segments: int = 60) -> list[ClassificationEvent]:
    """Simulasi baseline: semua segmen normal (kontrol negatif untuk test)."""
    return _build_events([False] * n_segments)
