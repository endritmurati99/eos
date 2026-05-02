from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass
class EnergyLog:
    local_date: str
    energy_level: int | None = None
    sleep_quality: int | None = None
    physical_fatigue: int | None = None
    mental_load: int | None = None
    stress: int | None = None
    motivation: int | None = None
    soreness: int | None = None
    notes: list[str] | None = None
    source: str = "cli"

    def to_dict(self) -> dict[str, Any]:
        return {
            "local_date": self.local_date,
            "energy_level": self.energy_level,
            "sleep_quality": self.sleep_quality,
            "physical_fatigue": self.physical_fatigue,
            "mental_load": self.mental_load,
            "stress": self.stress,
            "motivation": self.motivation,
            "soreness": self.soreness,
            "notes": self.notes,
            "source": self.source,
        }


_FIELD_KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("schlaf", "sleep", "schlafqualitaet"), "sleep_quality"),
    (("energie", "energy", "energielevel"), "energy_level"),
    (("stress",), "stress"),
    (("koerper", "koerpermued", "fatigue", "physisch", "muede", "mued"), "physical_fatigue"),
    (("mental", "kopf", "konzentration", "geistig"), "mental_load"),
    (("motivation", "motiviert", "lust"), "motivation"),
    (("muskelkater", "kater", "soreness"), "soreness"),
)

_NUM_PATTERN = re.compile(r"\b(\d+)\b(?:\s*(?:/10|von\s*10))?")


def _validate(val: int) -> int:
    if not (1 <= val <= 10):
        raise ValueError(f"Wert {val} liegt außerhalb des erlaubten Bereichs 1–10")
    return val


def parse_energy_text(raw_text: str, *, source: str = "cli") -> "EnergyLog":
    from datetime import datetime, timezone
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Berlin")
    except Exception:
        import pytz
        tz = pytz.timezone("Europe/Berlin")

    local_date = datetime.now(tz).date().isoformat()

    normalized = raw_text.lower()
    normalized = normalized.replace("ä", "ae").replace("ö", "oe").replace("ü", "ue").replace("ß", "ss")

    tokens = re.split(r"[\s,;:]+", normalized)
    fields: dict[str, int] = {}

    for i, token in enumerate(tokens):
        for keywords, field_name in _FIELD_KEYWORDS:
            if any(kw in token for kw in keywords):
                for j in range(i + 1, min(i + 4, len(tokens))):
                    m = re.fullmatch(r"(\d+)(?:/10)?", tokens[j])
                    if m:
                        val = int(m.group(1))
                        _validate(val)
                        fields[field_name] = val
                        break
                break

    return EnergyLog(
        local_date=local_date,
        energy_level=fields.get("energy_level"),
        sleep_quality=fields.get("sleep_quality"),
        physical_fatigue=fields.get("physical_fatigue"),
        mental_load=fields.get("mental_load"),
        stress=fields.get("stress"),
        motivation=fields.get("motivation"),
        soreness=fields.get("soreness"),
        source=source,
    )
