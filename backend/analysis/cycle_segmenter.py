"""Deteksi siklus napas + pemotongan PCM tepat pada batas siklus.

Detektor di `resp_cycle.py` bekerja pada sinyal float dan mengembalikan boundary
dalam detik relatif terhadap segmen analisis. Modul ini menjembatani hasil itu ke
pipeline ingestion: menormalkan PCM int16, memotong sampel per siklus, dan
mengembalikan status fallback yang eksplisit saat deteksi tidak bisa dipakai.
"""

import logging
from dataclasses import dataclass, field

import numpy as np

from backend.analysis.resp_cycle import Params, detect_respiratory_cycles

logger = logging.getLogger(__name__)

_PCM_INT16_SCALE = 32768.0
_MIN_SUPPORTED_SAMPLE_RATE_HZ = 2 * Params().f_high


@dataclass
class CycleSlice:
    index: int  # indeks siklus dari detektor, 1-based
    start_s: float  # relatif terhadap awal segmen analisis
    end_s: float
    pcm_samples: list[int]  # potongan int16 tepat batas siklus
    dtw_score: float | None


@dataclass
class CycleDetectionResult:
    # "detected" | "no_cycles" | "unsupported_sample_rate" | "error"
    status: str
    cycles: list[CycleSlice] = field(default_factory=list)
    mean_dtw: float | None = None
    error: str | None = None


def _empty(status: str, error: str | None = None) -> CycleDetectionResult:
    return CycleDetectionResult(status=status, cycles=[], mean_dtw=None, error=error)


def detect_cycle_slices(
    pcm_samples: list[int], sample_rate: int
) -> CycleDetectionResult:
    if sample_rate <= _MIN_SUPPORTED_SAMPLE_RATE_HZ:
        logger.warning(
            "deteksi siklus dilewati: sample_rate=%s Hz (harus > %s Hz)",
            sample_rate,
            _MIN_SUPPORTED_SAMPLE_RATE_HZ,
        )
        return _empty("unsupported_sample_rate")

    if len(pcm_samples) == 0:
        return _empty("no_cycles")

    x = np.asarray(pcm_samples, dtype=np.float64) / _PCM_INT16_SCALE

    try:
        result = detect_respiratory_cycles(x, sample_rate)
    except Exception as exc:  # detektor pihak ketiga; fallback lebih aman daripada crash
        logger.warning("deteksi siklus gagal: %s", exc)
        return _empty("error", error=str(exc))

    raw_cycles = result.get("cycles") or []
    if not raw_cycles:
        return _empty("no_cycles")

    dtw_scores = result.get("cycle_scores") or []
    cycles: list[CycleSlice] = []
    for index, (start_s, end_s) in enumerate(raw_cycles, 1):
        lo = max(0, int(round(start_s * sample_rate)))
        hi = min(len(pcm_samples), int(round(end_s * sample_rate)))
        if hi <= lo:
            continue
        score = dtw_scores[index - 1] if index - 1 < len(dtw_scores) else None
        cycles.append(
            CycleSlice(
                index=index,
                start_s=float(start_s),
                end_s=float(end_s),
                pcm_samples=pcm_samples[lo:hi],
                dtw_score=float(score) if score is not None else None,
            )
        )

    if not cycles:
        return _empty("no_cycles")

    mean_dtw = result.get("mean_dtw")
    return CycleDetectionResult(
        status="detected",
        cycles=cycles,
        mean_dtw=float(mean_dtw) if mean_dtw is not None else None,
    )
