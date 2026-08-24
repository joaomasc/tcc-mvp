from __future__ import annotations

import json

import pytest

from vs_epl_krls.audit import _record_hash, append_audit_record, verify_audit_ledger


def test_audit_ledger_is_hash_chained_and_deterministically_verified(tmp_path):
    ledger = tmp_path / "audit.jsonl"
    first = append_audit_record(
        ledger,
        event="forecast",
        payload={"point": 6.9},
        recorded_at_utc="2026-08-23T00:00:00+00:00",
    )
    second = append_audit_record(
        ledger,
        event="outcome",
        payload={"actual": 6.89},
        recorded_at_utc="2026-08-24T00:00:00+00:00",
    )
    records = verify_audit_ledger(ledger)
    assert [record["sequence"] for record in records] == [1, 2]
    assert second["previous_hash"] == first["record_hash"]


def test_audit_ledger_rejects_tampering_and_bad_events(tmp_path):
    ledger = tmp_path / "audit.jsonl"
    append_audit_record(ledger, event="release", payload={"status": "candidate"})
    record = json.loads(ledger.read_text(encoding="utf-8"))
    record["payload"]["status"] = "production"
    ledger.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match="hash mismatch"):
        verify_audit_ledger(ledger)
    with pytest.raises(ValueError, match="event"):
        append_audit_record(tmp_path / "other.jsonl", event="bad event", payload={})


def test_missing_audit_ledger_is_empty(tmp_path):
    assert verify_audit_ledger(tmp_path / "missing.jsonl") == []


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("not-json\n", "invalid audit JSON"),
        ("[]\n", "invalid audit record"),
    ],
)
def test_audit_ledger_rejects_malformed_records(tmp_path, content, message):
    ledger = tmp_path / "malformed.jsonl"
    ledger.write_text(content, encoding="utf-8")
    with pytest.raises(RuntimeError, match=message):
        verify_audit_ledger(ledger)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("sequence", 2, "sequence mismatch"),
        ("previous_hash", "0" * 64, "chain mismatch"),
    ],
)
def test_audit_ledger_rejects_broken_sequence_or_chain(
    tmp_path, field, value, message
):
    ledger = tmp_path / f"broken-{field}.jsonl"
    record = append_audit_record(ledger, event="release", payload={})
    record[field] = value
    unsigned = {key: value for key, value in record.items() if key != "record_hash"}
    record["record_hash"] = _record_hash(unsigned)
    ledger.write_text(json.dumps(record) + "\n", encoding="utf-8")
    with pytest.raises(RuntimeError, match=message):
        verify_audit_ledger(ledger)
