"""Alert engine — evaluasi HR/SpO2/RR terhadap ambang per pasien, eskalasi
berbasis persistence tren, dan Level 1 (informasi) berbasis near-threshold
(FR-SW-040..044, INTEGRATION_CONTRACT.md §5.1 v3, SDD_SOFTWARE.md §7).

Fungsi murni, tanpa I/O — dipisah dari database/network sesuai pola yang sama
sejak Fase 1 (lihat ingestion/audio_segment_buffer.py, trend_analysis/*).
`recent_trend_significant_flags` HARUS sudah di-query dari tabel `trend_events`
oleh caller (layer I/O) — modul ini sendiri tidak menyentuh DB.
"""

from dataclasses import dataclass

from backend.trend_analysis.trend_detector import TrendResult


@dataclass(frozen=True)
class VitalReading:
    hr: float | None
    spo2: float | None
    rr: float | None


@dataclass(frozen=True)
class Thresholds:
    """Subset kolom tabel `thresholds` (SDD_SOFTWARE.md §3) yang relevan untuk evaluasi.

    Semua field `None`-able — parameter dengan threshold `None` (belum dikonfirmasi,
    lihat config.py) DILEWATI saat evaluasi, bukan dianggap 0/gagal. Ini penting supaya
    sistem tidak diam-diam mengaktifkan alert dengan ambang yang belum pernah diisi.
    """

    hr_min: float | None
    hr_max: float | None
    spo2_min: float | None
    rr_min: float | None
    rr_max: float | None


@dataclass(frozen=True)
class Trigger:
    """Satu kondisi pemicu alert — skema field persis INTEGRATION_CONTRACT.md §5.

    `severity` hanya relevan untuk type="vital_threshold" ("breach" | "near") —
    SDD_SOFTWARE.md §7.5. Untuk type="trend_slope", `severity` tetap None; trend_slope
    diperlakukan setara "breach" dalam determine_alert_level (lihat SDD §7.3).
    """

    type: str  # "vital_threshold" | "trend_slope"
    parameter: str  # "hr" | "spo2" | "rr" | "wheeze_frequency" | dst.
    value: float
    threshold: float
    severity: str | None = None  # "breach" | "near" | None (trend_slope)


@dataclass(frozen=True)
class AlertResult:
    level: int  # 1, 2, atau 3
    triggers: list[Trigger]
    trend_persistent: bool


def _classify_two_sided(
    value: float, threshold_min: float | None, threshold_max: float | None, margin_pct: float
) -> tuple[str, float] | None:
    """Klasifikasi near/breach untuk parameter dua-sisi (HR, RR) — SDD_SOFTWARE.md §7.5.

    Return `(severity, reference_threshold)` — `reference_threshold` adalah batas yang
    dilanggar/didekati (hr_min atau hr_max), dipakai untuk field `threshold` di Trigger.
    Return `None` bila nilai aman dan jauh dari kedua batas.

    Kalau hanya salah satu dari min/max yang tersedia (bukan dua-duanya), margin tidak
    bisa dihitung dari rentang (threshold_max - threshold_min) — fallback ke breach-only
    (tanpa near) untuk sisi yang tersedia, karena tidak ada rentang yang bermakna untuk
    menghitung margin persentase.
    """
    if threshold_min is None and threshold_max is None:
        return None

    if threshold_min is not None and threshold_max is not None:
        margin = margin_pct * (threshold_max - threshold_min)
        if value < threshold_min:
            return ("breach", threshold_min)
        if value > threshold_max:
            return ("breach", threshold_max)
        if value < threshold_min + margin:
            return ("near", threshold_min)
        if value > threshold_max - margin:
            return ("near", threshold_max)
        return None

    if threshold_min is not None and value < threshold_min:
        return ("breach", threshold_min)
    if threshold_max is not None and value > threshold_max:
        return ("breach", threshold_max)
    return None


def _classify_one_sided_min(value: float, threshold_min: float | None, margin_abs: float) -> tuple[str, float] | None:
    """Klasifikasi near/breach untuk parameter satu-sisi (SpO2, hanya punya min) — §7.5."""
    if threshold_min is None:
        return None
    if value < threshold_min:
        return ("breach", threshold_min)
    if value < threshold_min + margin_abs:
        return ("near", threshold_min)
    return None


def evaluate_vitals(
    vitals: VitalReading,
    thresholds: Thresholds,
    level1_margin_pct: float,
    level1_margin_spo2_abs: float,
) -> list[Trigger]:
    """Bandingkan HR/SpO2/RR terhadap ambang, hasilkan satu Trigger per parameter yang
    breach ATAU near-threshold (SDD_SOFTWARE.md §7.5). Parameter dilewati sepenuhnya
    (tidak ada trigger, bukan error) bila nilai vital ATAU threshold-nya `None`.
    """
    triggers: list[Trigger] = []

    if vitals.hr is not None:
        result = _classify_two_sided(vitals.hr, thresholds.hr_min, thresholds.hr_max, level1_margin_pct)
        if result is not None:
            severity, reference_threshold = result
            triggers.append(Trigger(type="vital_threshold", parameter="hr", value=vitals.hr, threshold=reference_threshold, severity=severity))

    if vitals.spo2 is not None:
        result = _classify_one_sided_min(vitals.spo2, thresholds.spo2_min, level1_margin_spo2_abs)
        if result is not None:
            severity, reference_threshold = result
            triggers.append(Trigger(type="vital_threshold", parameter="spo2", value=vitals.spo2, threshold=reference_threshold, severity=severity))

    if vitals.rr is not None:
        result = _classify_two_sided(vitals.rr, thresholds.rr_min, thresholds.rr_max, level1_margin_pct)
        if result is not None:
            severity, reference_threshold = result
            triggers.append(Trigger(type="vital_threshold", parameter="rr", value=vitals.rr, threshold=reference_threshold, severity=severity))

    return triggers


def make_trend_trigger(trend_result: TrendResult, significance_threshold: float) -> Trigger:
    return Trigger(
        type="trend_slope",
        parameter="wheeze_frequency",
        value=trend_result.slope,
        threshold=significance_threshold,
        severity=None,
    )


def compute_trend_persistence(recent_significant_flags: list[bool], min_consecutive: int) -> bool:
    """`recent_significant_flags`: nilai `significant` dari N evaluasi trend_event
    TERBARU untuk device ini, urut lama→baru (termasuk evaluasi saat ini bila relevan
    — tanggung jawab caller memastikan urutan ini benar). Fungsi murni, tidak menyentuh DB.

    True hanya bila `min_consecutive` elemen TERAKHIR dalam list semuanya True — satu
    False di tengah (bahkan bila diapit True) mereset streak, sesuai definisi "berturut-turut".
    """
    if len(recent_significant_flags) < min_consecutive:
        return False
    return all(recent_significant_flags[-min_consecutive:])


def determine_alert_level(triggers: list[Trigger], trend_persistent: bool = False) -> int | None:
    """INTEGRATION_CONTRACT.md §5.1 v3 (SDD_SOFTWARE.md §7.2, §7.3):

    0 trigger (breach maupun near)                                -> None (tidak ada alert)
    ada trigger near, TIDAK ada trigger breach                    -> 1
    1 trigger breach, BUKAN trend_slope                           -> 2
    1 trigger breach, trend_slope, belum persistent                -> 2
    1 trigger breach, trend_slope, SUDAH persistent                -> 3 (eskalasi)
    >=2 trigger breach (kombinasi apapun)                          -> 3

    `trend_slope` diperlakukan setara "breach" (bukan "near") — trend_result.significant
    sudah berarti tren melewati ambang signifikansinya sendiri, jadi tidak ada konsep
    "near-threshold" untuk trend_slope di desain ini (SDD_SOFTWARE.md §7.3).

    Trigger "near" TIDAK ikut dihitung dalam aturan >=2-trigger-jadi-level-3 — begitu ada
    satu saja trigger breach sungguhan, sinyal near-threshold jadi tidak relevan untuk
    penentuan level (SDD_SOFTWARE.md §7.2).
    """
    breach_triggers = [t for t in triggers if t.severity == "breach" or t.type == "trend_slope"]
    near_triggers = [t for t in triggers if t.severity == "near"]

    n_breach = len(breach_triggers)
    if n_breach == 0:
        return 1 if near_triggers else None

    if n_breach >= 2:
        return 3

    has_trend_trigger = any(t.type == "trend_slope" for t in breach_triggers)
    if has_trend_trigger and trend_persistent:
        return 3

    return 2


def evaluate_alert(
    vitals: VitalReading,
    trend_result: TrendResult | None,
    recent_trend_significant_flags: list[bool],
    thresholds: Thresholds,
    trend_significance_threshold: float,
    min_consecutive: int,
    level1_margin_pct: float,
    level1_margin_spo2_abs: float,
) -> AlertResult | None:
    """Entry point utama alert engine untuk satu titik evaluasi (satu device, satu waktu).

    `trend_result` boleh `None` bila belum ada cukup data untuk trend_detector.py
    menghasilkan hasil (lihat trend_analysis/trend_detector.py — return None untuk <2 titik).
    """
    triggers = evaluate_vitals(vitals, thresholds, level1_margin_pct, level1_margin_spo2_abs)

    if trend_result is not None and trend_result.significant:
        triggers.append(make_trend_trigger(trend_result, trend_significance_threshold))

    if not triggers:
        return None

    trend_persistent = compute_trend_persistence(recent_trend_significant_flags, min_consecutive)
    level = determine_alert_level(triggers, trend_persistent)

    if level is None:
        return None

    return AlertResult(level=level, triggers=triggers, trend_persistent=trend_persistent)
