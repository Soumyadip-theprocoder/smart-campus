"""
Break helpers shared by the serializers and the generation task.

A break is a time range ``{"start": "HH:MM", "end": "HH:MM", "label": str}``.
  * Continuous break: one range spanning several hours (e.g. 12:00-15:00).
  * Discrete breaks: several independent ranges (e.g. 10:00-11:00 and 15:00-16:00).

Legacy values (a plain ``"HH:MM"`` string) mean a one-hour break starting at that time.
"""

from datetime import time as dtime

MINUTES_PER_DAY = 24 * 60


def _to_minutes(value):
    """Parse 'HH:MM' / 'HH:MM:SS' / datetime.time into minutes since midnight, or None."""
    if isinstance(value, dtime):
        return value.hour * 60 + value.minute
    if not isinstance(value, str):
        return None
    parts = value.strip().split(":")
    try:
        hours = int(parts[0])
        minutes = int(parts[1]) if len(parts) > 1 else 0
    except (ValueError, IndexError):
        return None
    if not (0 <= hours <= 24 and 0 <= minutes < 60):
        return None
    return hours * 60 + minutes


def _to_hhmm(total):
    total = max(0, min(MINUTES_PER_DAY, total))
    return f"{total // 60:02d}:{total % 60:02d}"


def _to_range(entry):
    if isinstance(entry, (str, dtime)):
        start = _to_minutes(entry)
        if start is None:
            return None
        return start, min(start + 60, MINUTES_PER_DAY), ""
    if isinstance(entry, dict):
        start = _to_minutes(entry.get("start"))
        end = _to_minutes(entry.get("end"))
        if start is None or end is None or end <= start:
            return None
        return start, end, str(entry.get("label") or "")[:30]
    return None


def normalize_breaks(raw):
    """Return a sorted list of non-overlapping ``{start, end, label}`` dicts.

    Overlapping or touching ranges are merged (first non-empty label wins).
    Invalid entries are ignored.
    """
    if not isinstance(raw, (list, tuple)):
        return []
    ranges = sorted(filter(None, (_to_range(e) for e in raw)), key=lambda r: (r[0], r[1]))
    merged = []
    for start, end, label in ranges:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
            if not merged[-1][2] and label:
                merged[-1][2] = label
        else:
            merged.append([start, end, label])
    return [{"start": _to_hhmm(s), "end": _to_hhmm(e), "label": lbl} for s, e, lbl in merged]


def validate_breaks(raw):
    """Strict validation for API input. Returns normalized breaks or raises ValueError."""
    if raw in (None, ""):
        return []
    if not isinstance(raw, (list, tuple)):
        raise ValueError("Breaks must be a list.")
    for entry in raw:
        if _to_range(entry) is None:
            raise ValueError(
                f"Invalid break {entry!r}. Use 'HH:MM' or {{start, end, label}} with end after start."
            )
    return normalize_breaks(raw)


def slot_overlaps_break(start_time, end_time, breaks):
    """True when the slot [start_time, end_time) overlaps any break range."""
    s = _to_minutes(start_time)
    e = _to_minutes(end_time)
    if s is None or e is None:
        return False
    for b in normalize_breaks(breaks):
        if s < _to_minutes(b["end"]) and e > _to_minutes(b["start"]):
            return True
    return False
