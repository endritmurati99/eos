from __future__ import annotations

import re
import unicodedata
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime

from src.eos_mail_actions.types import DeadlineExtraction


WEEKDAYS = {
    "monday": 0,
    "montag": 0,
    "tuesday": 1,
    "dienstag": 1,
    "wednesday": 2,
    "mittwoch": 2,
    "thursday": 3,
    "donnerstag": 3,
    "friday": 4,
    "freitag": 4,
    "saturday": 5,
    "samstag": 5,
    "sunday": 6,
    "sonntag": 6,
}


def extract_deadline(
    text: str,
    reference_date: date | str | None = None,
) -> DeadlineExtraction:
    base = _parse_reference_date(reference_date)
    normalized = _normalize_text(text)

    explicit = _extract_explicit_date(normalized)
    if explicit is not None:
        return DeadlineExtraction(due=explicit.isoformat(), confidence=0.96, reason="explicit_date")

    if re.search(r"\b(today|heute)\b", normalized):
        return DeadlineExtraction(due=base.isoformat(), confidence=0.92, reason="today")

    if re.search(r"\b(tomorrow|morgen)\b", normalized):
        return DeadlineExtraction(
            due=(base + timedelta(days=1)).isoformat(),
            confidence=0.92,
            reason="tomorrow",
        )

    within_match = re.search(r"\b(?:within|in)\s+(\d{1,2})\s+days?\b", normalized)
    if within_match:
        days = int(within_match.group(1))
        return DeadlineExtraction(
            due=(base + timedelta(days=days)).isoformat(),
            confidence=0.88,
            reason=f"within_{days}_days",
        )

    weekday = _extract_weekday(normalized, base)
    if weekday is not None:
        due, matched = weekday
        return DeadlineExtraction(due=due.isoformat(), confidence=0.86, reason=f"weekday_{matched}")

    if re.search(r"\b(bis ende der woche|end of (the )?week)\b", normalized):
        return DeadlineExtraction(
            due=_next_weekday(base, 4).isoformat(),
            confidence=0.82,
            reason="end_of_week",
        )

    if _has_uncertain_deadline(normalized):
        return DeadlineExtraction(
            due=None,
            confidence=0.45,
            reason="deadline_uncertain",
            requires_approval=True,
            risk_flags=["deadline_uncertain"],
        )

    return DeadlineExtraction(due=None, confidence=0.0, reason="no_deadline")


def _parse_reference_date(reference_date: date | str | None) -> date:
    if reference_date is None:
        return date.today()
    if isinstance(reference_date, date):
        return reference_date
    raw = reference_date.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(raw).date()
    except ValueError:
        try:
            return parsedate_to_datetime(raw).date()
        except (TypeError, ValueError):
            return date.fromisoformat(raw[:10])


def _normalize_text(text: str) -> str:
    folded = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    lowered = folded.casefold()
    return re.sub(r"\s+", " ", lowered).strip()


def _extract_explicit_date(normalized: str) -> date | None:
    iso_match = re.search(r"\b(20\d{2})-(\d{2})-(\d{2})\b", normalized)
    if iso_match:
        return date(int(iso_match.group(1)), int(iso_match.group(2)), int(iso_match.group(3)))

    eu_match = re.search(r"\b(\d{1,2})\.(\d{1,2})\.(20\d{2})\b", normalized)
    if eu_match:
        return date(int(eu_match.group(3)), int(eu_match.group(2)), int(eu_match.group(1)))

    return None


def _extract_weekday(normalized: str, base: date) -> tuple[date, str] | None:
    for weekday_name, weekday_number in WEEKDAYS.items():
        pattern = rf"\b(by|until|bis|reply by|respond by)\s+{weekday_name}\b"
        if re.search(pattern, normalized):
            return _next_weekday(base, weekday_number), weekday_name
    return None


def _next_weekday(base: date, weekday_number: int) -> date:
    delta = (weekday_number - base.weekday()) % 7
    return base + timedelta(days=delta)


def _has_uncertain_deadline(normalized: str) -> bool:
    return bool(
        re.search(
            r"\b(asap|soon|next week|this week|deadline|zeitnah|bald|so schnell wie moglich|diese woche)\b",
            normalized,
        )
    )
