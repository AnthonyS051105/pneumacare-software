"""Transformasi trigger teknis alert -> bahasa awam untuk pasien
(FR-SW-066, SDD_SOFTWARE.md §4.4).

Fungsi murni: input = 1 baris `alerts` (dengan `triggers` JSON teknis dari
INTEGRATION_CONTRACT.md §5), output = pesan bahasa awam.

⚠️ Daftar mapping di bawah adalah DRAF AWAL (SDD_SOFTWARE.md §4.4 sendiri menandai
ini sebagai contoh pola, bukan final) — perlu direview dengan masukan dosen
pembimbing/tenaga medis supaya akurat secara medis tapi tidak menakut-nakuti
berlebihan. Jangan anggap kalimat di sini sudah final.
"""

VITAL_PARAMETER_LABEL = {
    "hr": "detak jantung",
    "spo2": "kadar oksigen",
    "rr": "laju napas",
}


def _vital_threshold_sentence(trigger: dict) -> str:
    parameter_label = VITAL_PARAMETER_LABEL.get(trigger.get("parameter"), "salah satu tanda vital Anda")
    severity = trigger.get("severity")

    if severity == "near":
        return f"{parameter_label.capitalize()} Anda mendekati batas normal, tetap perhatikan kondisi Anda."
    return f"{parameter_label.capitalize()} Anda sempat berada di luar rentang normal."


def _trend_slope_sentence(trigger: dict) -> str:
    return "Pola napas Anda menunjukkan perubahan yang perlu diperhatikan."


_TRIGGER_TYPE_HANDLERS = {
    "vital_threshold": _vital_threshold_sentence,
    "trend_slope": _trend_slope_sentence,
}


def translate_trigger(trigger: dict) -> str:
    """Satu trigger teknis -> satu kalimat bahasa awam."""
    handler = _TRIGGER_TYPE_HANDLERS.get(trigger.get("type"))
    if handler is None:
        return "Ada perubahan pada kondisi Anda yang perlu diperhatikan."
    return handler(trigger)


def translate_alert(level: int, triggers: list[dict]) -> dict:
    """Satu baris `alerts` -> representasi bahasa awam untuk Patient Alerts screen.

    `level` 1 (informasi) dipetakan ke label paling tenang, level 2/3 dipetakan
    sesuai FR-SW-071b (perlu diperhatikan / segera hubungi dokter). Pemetaan
    level->label sengaja tetap sederhana di sini; kebijakan apakah level 1
    ditampilkan sama sekali ke pasien adalah keputusan produk terpisah
    (SRS_SOFTWARE.md FR-SW-071b, belum final).
    """
    level_label = {1: "Informasi", 2: "Perlu Diperhatikan", 3: "Segera Hubungi Dokter"}.get(level, "Informasi")
    messages = [translate_trigger(t) for t in triggers]

    return {"level": level, "level_label": level_label, "messages": messages}
