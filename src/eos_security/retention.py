"""Data classification helpers for EOS retention gates."""

from __future__ import annotations

from .redaction import scan_for_sensitive_patterns
from .secret_patterns import CLASS_3_LABELS, CLASS_4_LABELS


CLASS_3_INDICATORS = (
    "gmail raw body",
    "gmail_raw_body",
    "gmail body",
    "raw gmail",
    "drive file content",
    "drive_file_content",
    "google drive file content",
    "maps location history",
    "location_history",
    "location history",
    "google maps timeline",
    "calendar event location",
    "travel-time trace",
    "telegram raw output",
)

CLASS_2_INDICATORS = (
    "personal metadata",
    "mail metadata",
    "gmail metadata",
    "drive metadata",
    "calendar location",
    "route estimate",
)

CLASS_1_INDICATORS = (
    "operational metadata",
    "request_id",
    "trace_id",
    "job_id",
    "timestamp",
    "status",
)

CLASS_0_INDICATORS = (
    "public fixture",
    "test fixture",
    "synthetic only",
    "synthetic fixture",
)


def classify_data_class(value: str) -> str:
    """Classify a text value into the EOS retention data classes."""

    text = "" if value is None else str(value)
    normalized = text.lower()
    scan = scan_for_sensitive_patterns(text)
    labels = set(scan["counts"])

    if labels & CLASS_4_LABELS:
        return "Class 4"
    if labels & CLASS_3_LABELS:
        return "Class 3"
    if any(indicator in normalized for indicator in CLASS_3_INDICATORS):
        return "Class 3"
    if labels:
        return "Class 2"
    if any(indicator in normalized for indicator in CLASS_2_INDICATORS):
        return "Class 2"
    if any(indicator in normalized for indicator in CLASS_1_INDICATORS):
        return "Class 1"
    if any(indicator in normalized for indicator in CLASS_0_INDICATORS):
        return "Class 0"

    return "Class 1"
