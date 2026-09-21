"""Stable fingerprints for side effects. Hashing, used for exactly-once."""
import hashlib
import json
import re
import uuid
from datetime import date


def _normalize_value(val):
    """Recursively convert whole floats (e.g. 12.0) to int, traversing dicts and lists."""
    if isinstance(val, float) and val.is_integer():
        return int(val)
    if isinstance(val, dict):
        return {k: _normalize_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_normalize_value(v) for v in val]
    return val


def canonical_json(value) -> str:
    """One spelling per meaning.
    Sorted keys, no spaces, and whole floats as integers (12.0 and 12 are the same drive id),
    including inside nested dicts and lists.
    """
    normalized = _normalize_value(value)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def idempotency_key(run_id: str, step_seq: int, tool_name: str, args: dict) -> str:
    """The same tool call at the same step of the same run must always get the same key.
    SHA-256 hex digest of canonical_json([run_id, step_seq, tool_name, args]).
    """
    serialized = canonical_json([run_id, step_seq, tool_name, args])
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def notification_dedupe_key(roll_no: str, message: str, day: date) -> str:
    """The same message to the same student on the same day is one notification.
    SHA-256 hex of canonical_json([roll_no, message with runs of whitespace collapsed and trimmed, day.isoformat()]).
    """
    clean_message = re.sub(r"\s+", " ", message.strip())
    serialized = canonical_json([roll_no, clean_message, day.isoformat()])
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()