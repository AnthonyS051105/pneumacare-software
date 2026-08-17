"""Fixture data simulasi untuk modul trend analysis (FR-SW-024, SRS_SOFTWARE.md §2.3).

Data longitudinal nyata belum tersedia (baru subjek sehat/simulasi, lihat PRD_SOFTWARE.md
§2), jadi modul trend analysis HARUS bisa diuji dan didemokan dengan skenario sintetis
yang jujur dilabeli sebagai simulasi — bukan data pasien sungguhan.

Tiap skenario menghasilkan list ClassificationEvent yang mensimulasikan hasil klasifikasi
per segmen 5 detik (INTEGRATION_CONTRACT.md §4.1) selama beberapa menit, dengan pola
frekuensi wheeze yang berbeda: naik, turun, atau stabil.
"""

from datetime import datetime, timedelta

from backend.trend_analysis.rolling_window import ClassificationEvent, WheezeCrackleClass

SEGMENT_DURATION = timedelta(seconds=5)
_BASE_TIMESTAMP = datetime(2026, 1, 1, 8, 0, 0)


def _build_events(
    wheeze_pattern: list[bool], crackle_pattern: list[bool] | None = None
) -> list[ClassificationEvent]:
    if crackle_pattern is None:
        crackle_pattern = [False] * len(wheeze_pattern)
    if len(wheeze_pattern) != len(crackle_pattern):
        raise ValueError("wheeze_pattern dan crackle_pattern harus sama panjang")

    events = []
    for i, (wheeze, crackle) in enumerate(zip(wheeze_pattern, crackle_pattern)):
        wheeze_crackle_class: WheezeCrackleClass
        if wheeze and crackle:
            wheeze_crackle_class = "both"
        elif wheeze:
            wheeze_crackle_class = "wheeze"
        elif crackle:
            wheeze_crackle_class = "crackle"
        else:
            wheeze_crackle_class = "none"

        events.append(
            ClassificationEvent(
                timestamp=_BASE_TIMESTAMP + i * SEGMENT_DURATION,
                wheeze_crackle_class=wheeze_crackle_class,
            )
        )
    return events


def rising_wheeze_scenario(n_segments: int = 60) -> list[ClassificationEvent]:
    """Simulasi tren NAIK: wheeze makin sering muncul seiring waktu.

    Paruh pertama jarang wheeze, paruh kedua nyaris selalu wheeze — pola tangga naik,
    bukan acak, supaya slope regresi pasti positif dan jelas signifikan untuk demo.
    """
    pattern = []
    for i in range(n_segments):
        progress = i / max(n_segments - 1, 1)
        wheeze_probability_threshold = 1 - progress  # makin ke akhir, makin sering True
        pattern.append((i % 4) / 4 >= wheeze_probability_threshold)
    return _build_events(pattern)


def falling_wheeze_scenario(n_segments: int = 60) -> list[ClassificationEvent]:
    """Simulasi tren TURUN: wheeze sering di awal, makin jarang seiring waktu (mis. kondisi membaik)."""
    rising = rising_wheeze_scenario(n_segments)
    reversed_pattern = [e.wheeze_present for e in reversed(rising)]
    return _build_events(reversed_pattern)


def stable_wheeze_scenario(n_segments: int = 60, wheeze_every: int = 5) -> list[ClassificationEvent]:
    """Simulasi tren STABIL: wheeze muncul dengan frekuensi konstan (tiap `wheeze_every` segmen)."""
    pattern = [(i % wheeze_every == 0) for i in range(n_segments)]
    return _build_events(pattern)


def no_wheeze_scenario(n_segments: int = 60) -> list[ClassificationEvent]:
    """Simulasi baseline: tidak ada wheeze sama sekali (kontrol negatif untuk test)."""
    return _build_events([False] * n_segments)
