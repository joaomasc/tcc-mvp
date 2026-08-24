"""Tamper-evident append-only ledgers for production evidence.

The ledger is deliberately small and dependency-free.  It does not replace a
managed audit-log service, but it makes local releases and forecasts
independently verifiable before they are exported to one.
"""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _record_hash(record_without_hash: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical_json(record_without_hash).encode("utf-8")).hexdigest()


def verify_audit_ledger(path: str | Path) -> list[dict[str, Any]]:
    """Return verified records or raise when any link/content was modified."""

    source = Path(path)
    if not source.exists():
        return []
    records: list[dict[str, Any]] = []
    previous_hash: str | None = None
    with source.open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"invalid audit JSON at line {line_number}") from exc
            if not isinstance(record, dict):
                raise RuntimeError(f"invalid audit record at line {line_number}")
            observed_hash = record.get("record_hash")
            unsigned = {key: value for key, value in record.items() if key != "record_hash"}
            if observed_hash != _record_hash(unsigned):
                raise RuntimeError(f"audit record hash mismatch at line {line_number}")
            if unsigned.get("sequence") != len(records) + 1:
                raise RuntimeError(f"audit sequence mismatch at line {line_number}")
            if unsigned.get("previous_hash") != previous_hash:
                raise RuntimeError(f"audit chain mismatch at line {line_number}")
            records.append(record)
            previous_hash = str(observed_hash)
    return records


def append_audit_record(
    path: str | Path,
    *,
    event: str,
    payload: dict[str, Any],
    recorded_at_utc: str | None = None,
) -> dict[str, Any]:
    """Append one canonical, hash-chained event after verifying existing data."""

    if not event or any(character.isspace() for character in event):
        raise ValueError("event must be a non-empty token without whitespace")
    destination = Path(path)
    records = verify_audit_ledger(destination)
    unsigned: dict[str, Any] = {
        "sequence": len(records) + 1,
        "recorded_at_utc": recorded_at_utc
        or datetime.now(timezone.utc).isoformat(),
        "event": event,
        "payload": payload,
        "previous_hash": records[-1]["record_hash"] if records else None,
    }
    record = {**unsigned, "record_hash": _record_hash(unsigned)}
    encoded = _canonical_json(record) + "\n"
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(encoded)
        stream.flush()
    verify_audit_ledger(destination)
    return record

