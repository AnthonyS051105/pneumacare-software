"""
Deteksi boundary siklus napas dari suara paru single-channel.
Implementasi dari: Aras, Ozturk, Gangal (2018), Turk J Elec Eng & Comp Sci 26:11-22.
"""
from dataclasses import dataclass
import numpy as np
from scipy import signal
from scipy.fft import dct, idct

try:  # opsional, hanya untuk mempercepat DTW
    from numba import njit
except ImportError:  # pragma: no cover
    njit = None


# --------------------------------------------------------------------------
# Parameter. Yang bertanda [PAPER] disebut di paper; [ASUMSI] tidak disebut.
# --------------------------------------------------------------------------
@dataclass
class Params:
    f_low: float = 80.0          # [PAPER] fL = 80 Hz (Sec. 2.2)
    f_high: float = 1000.0       # [PAPER] fH = 1000 Hz (Sec. 2.2)
    l_min: float = 1.25          # [PAPER] Lmin = 1.25 s (Sec. 2.3)
    l_max: float = 5.5           # [PAPER] Lmax = 5.5 s (Sec. 2.3)
    win_s: float = 0.05          # [ASUMSI] panjang jendela Hamming Nw
    hop_s: float = 0.01          # [ASUMSI] hop L
    smooth_cutoff_hz: float = 2.0  # [ASUMSI] kekuatan smoothing (Garcia 2010)
    n_s: int = 48                # [ASUMSI] jumlah sampel decimation Ns
    min_tests: int = 2           # [ASUMSI] min. test pattern per model
    log_energy: bool = False     # [ASUMSI] False = Eq.(3) apa adanya (linear)
    extend_backward: bool = True  # [EKSTENSI, bukan paper] cari siklus sebelum model


# --------------------------------------------------------------------------
# DTW (Eq. 10-11)
# --------------------------------------------------------------------------
def _dtw(m, t):
    n = m.shape[0]
    D = np.full((n + 1, n + 1), np.inf)
    D[0, 0] = 0.0
    for i in range(1, n + 1):
        for j in range(1, n + 1):
            c = abs(m[i - 1] - t[j - 1])
            D[i, j] = c + min(D[i, j - 1], D[i - 1, j], D[i - 1, j - 1])
    return D[n, n]


dtw = njit(cache=True)(_dtw) if njit is not None else _dtw


# --------------------------------------------------------------------------
# Preprocessing (Sec. 2.2)
# --------------------------------------------------------------------------
def garcia_smooth(y, s):
    """Penalized least squares berbasis DCT (Garcia 2010, ref [17]), tanpa robust-iteration."""
    n = len(y)
    lam = (2.0 - 2.0 * np.cos(np.pi * np.arange(n) / n)) ** 2
    return idct(dct(y, norm="ortho") / (1.0 + s * lam), norm="ortho")


def preprocess(x, fs, p):
    nw = int(round(p.win_s * fs))
    hop = int(round(p.hop_s * fs))
    f, t, S = signal.spectrogram(            # Eq.(1)-(2): STFT + jendela Hamming
        x, fs=fs, window="hamming", nperseg=nw, noverlap=nw - hop,
        mode="psd", scaling="density")
    band = (f >= p.f_low) & (f <= p.f_high)
    pn = S[band].mean(axis=0)                # Eq.(3): rata-rata energi 80-1000 Hz
    if p.log_energy:
        pn = 10 * np.log10(pn + 1e-20)
        pn = pn - pn.min()
    frame_rate = 1.0 / (t[1] - t[0])
    s = (frame_rate / (2 * np.pi * p.smooth_cutoff_hz)) ** 4
    xs = garcia_smooth(pn, s)                # Eq.(4): Xs = smooth(p)
    return t, xs, frame_rate


def local_minima(xs):
    """Eq.(5): titik dengan turunan pertama = 0 dan turunan kedua > 0."""
    return signal.find_peaks(-xs)[0]


def sample_pattern(xs, lo, hi, ns):
    """Eq.(7)/(9): ambil Ns sampel merata lalu bagi dengan maks amplitudo di [lo, hi]."""
    idx = np.round(np.linspace(lo, hi, ns)).astype(int)
    peak = xs[lo:hi + 1].max()
    return xs[idx] / max(peak, 1e-12)


# --------------------------------------------------------------------------
# Pencarian model & test pattern (Sec. 2.3, Fig. 3)
# --------------------------------------------------------------------------
def _align_cycle_scores(bounds, scores, model_lo):
    """Sejajarkan skor test pattern ke daftar siklus.

    Siklus model (yang menjadi acuan DTW) tidak diuji terhadap dirinya sendiri,
    sehingga posisinya diisi None.
    """
    model_cycle_index = bounds.index(model_lo)
    cycle_scores: list[float | None] = [None] * (len(bounds) - 1)
    score_iter = iter(scores)
    for i in range(len(cycle_scores)):
        if i == model_cycle_index:
            continue
        score = next(score_iter, None)
        cycle_scores[i] = float(score) if score is not None else None
    return cycle_scores


def detect_respiratory_cycles(x, fs, params=None):
    p = params or Params()
    x = np.asarray(x, dtype=float)
    if fs <= 2 * p.f_high:
        raise ValueError(f"fs harus > {2 * p.f_high:.0f} Hz agar band 80-1000 Hz valid.")
    t, xs, fr = preprocess(x, fs, p)
    mins = local_minima(xs)
    lmin, lmax = int(round(p.l_min * fr)), int(round(p.l_max * fr))

    cache = {}
    def pat(a, b):
        if (a, b) not in cache:
            cache[(a, b)] = sample_pattern(xs, a, b, p.n_s)
        return cache[(a, b)]

    def search(min_tests):
        best = None
        zone = mins[mins <= 2 * lmax]                   # 1 <= bML <= bMU <= 2*Lmax
        for lo in zone:
            for hi in zone[zone > lo]:
                if not (lmin <= hi - lo <= lmax):       # Lmin <= bMU - bML <= Lmax
                    continue
                model = pat(lo, hi)                     # Eq.(7)
                bounds, scores, cur = [lo, hi], [], hi
                while True:                             # Eq.(8): lower bound = upper bound sebelumnya
                    cands = mins[(mins - cur >= lmin) & (mins - cur <= lmax)]
                    if len(cands) == 0:
                        break
                    d = [dtw(model, pat(cur, c)) for c in cands]   # Eq.(9)-(10)
                    k = int(np.argmin(d))               # subtest dengan DTW terkecil
                    scores.append(d[k])
                    cur = cands[k]
                    bounds.append(cur)
                if len(scores) < min_tests:
                    continue
                m = float(np.mean(scores))              # rata-rata DTW semua test pattern
                if best is None or m < best[0]:         # model dengan mean DTW terendah
                    best = (m, bounds, scores, model)
        return best

    best = search(p.min_tests) or search(1)
    if best is None:
        return {
            "boundaries": [],
            "cycles": [],
            "mean_dtw": None,
            "cycle_scores": [],
            "t": t,
            "xs": xs,
        }
    mean_dtw, bounds, scores, model = best
    model_lo = bounds[0]  # frame awal siklus model (lo, hi); tidak punya test score
    if p.extend_backward:                                # EKSTENSI: simetris dengan arah maju
        cur = bounds[0]
        while True:
            cands = mins[(cur - mins >= lmin) & (cur - mins <= lmax)]
            if len(cands) == 0:
                break
            d = [dtw(model, pat(c, cur)) for c in cands]
            k = int(np.argmin(d))
            scores.insert(0, d[k])
            cur = cands[k]
            bounds.insert(0, cur)
    b_sec = [float(t[i]) for i in bounds]

    # Skor test pattern mengikuti urutan siklus, kecuali siklus model yang tidak
    # diuji terhadap dirinya sendiri. Isi None pada posisi siklus model.
    cycle_scores = _align_cycle_scores(bounds, scores, model_lo)

    return {
        "boundaries": b_sec,                             # titik batas berurutan
        "cycles": list(zip(b_sec[:-1], b_sec[1:])),      # (start, end) tiap siklus
        "mean_dtw": mean_dtw,
        "dtw_per_cycle": scores,                         # skor DTW tiap test pattern (tanpa model)
        "cycle_scores": cycle_scores,                    # skor sejajar dengan `cycles`
        "t": t, "xs": xs,
    }


# def cycle_windows(x, fs, cycles, win_s=5.0, edge="shift"):
#     """
#     Buat satu window berdurasi `win_s` untuk tiap siklus, berpusat di titik tengah
#     siklus: c = a + (b - a) / 2.

#     edge="shift": jika window keluar dari rekaman, digeser masuk ke dalam rekaman
#                   (titik tengah siklus tetap tercakup selama rekaman >= win_s).
#     edge="zero" : window tetap berpusat di c, bagian di luar rekaman diisi nol.
#     Rekaman yang lebih pendek dari win_s selalu di-zero-pad di ujung.

#     Return: list of dict {cycle, a, b, center, win_start, win_end, covers_cycle, padded, segment}
#     """
#     x = np.asarray(x, dtype=float)
#     n_win, N = int(round(win_s * fs)), len(x)
#     out = []
#     for i, (a, b) in enumerate(cycles, 1):
#         c = a + (b - a) / 2.0
#         start = int(round((c - win_s / 2.0) * fs))
#         if edge == "shift" and N >= n_win:
#             start = min(max(start, 0), N - n_win)
#         seg = np.zeros(n_win)
#         lo, hi = max(start, 0), min(start + n_win, N)
#         seg[lo - start:hi - start] = x[lo:hi]
#         w0, w1 = start / fs, (start + n_win) / fs
#         out.append({
#             "cycle": i, "a": a, "b": b, "center": c,
#             "win_start": w0, "win_end": w1,
#             "covers_cycle": (w0 <= a and w1 >= b),   # False jika siklus > win_s (boleh)
#             "padded": (start < 0 or start + n_win > N),
#             "segment": seg,
#         })
#     return out


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------
# if __name__ == "__main__":
#     import argparse
#     from scipy.io import wavfile

#     ap = argparse.ArgumentParser()
#     ap.add_argument("wav")
#     ap.add_argument("--plot", action="store_true")
#     ap.add_argument("--windows", metavar="DIR", help="simpan window per siklus (WAV) ke folder DIR")
#     ap.add_argument("--win", type=float, default=5.0, help="durasi window (s), default 5")
#     ap.add_argument("--edge", choices=["shift", "zero"], default="shift")
#     a = ap.parse_args()

#     fs, x = wavfile.read(a.wav)
#     if x.ndim > 1:
#         x = x.mean(axis=1)
#     if np.issubdtype(x.dtype, np.integer):
#         x = x / np.iinfo(x.dtype).max
#     res = detect_respiratory_cycles(x, fs)
#     for i, (s, e) in enumerate(res["cycles"], 1):
#         print(f"Siklus {i}: {s:.3f} - {e:.3f} s  (durasi {e - s:.3f} s)")

#     if a.windows:
#         import os
#         os.makedirs(a.windows, exist_ok=True)
#         wins = cycle_windows(x, fs, res["cycles"], a.win, a.edge)
#         with open(os.path.join(a.windows, "windows.csv"), "w") as f:
#             f.write("cycle,cycle_start,cycle_end,center,win_start,win_end,padded\n")
#             for w in wins:
#                 f.write(f"{w['cycle']},{w['a']:.3f},{w['b']:.3f},{w['center']:.3f},"
#                         f"{w['win_start']:.3f},{w['win_end']:.3f},{int(w['padded'])}\n")
#                 wavfile.write(os.path.join(a.windows, f"window_{w['cycle']:02d}.wav"),
#                               fs, (np.clip(w["segment"], -1, 1) * 32767).astype(np.int16))
#         print(f"{len(wins)} window disimpan di {a.windows}/")

#     if a.plot:
#         import matplotlib.pyplot as plt
#         tt = np.arange(len(x)) / fs
#         fig, ax = plt.subplots(2, 1, sharex=True, figsize=(11, 5))
#         ax[0].plot(tt, x, lw=0.4)
#         ax[1].plot(res["t"], res["xs"])
#         for b in res["boundaries"]:
#             for a_ in ax:
#                 a_.axvline(b, color="r", ls="--")
#         ax[1].set_xlabel("Waktu (s)")
#         plt.tight_layout()
#         plt.show()