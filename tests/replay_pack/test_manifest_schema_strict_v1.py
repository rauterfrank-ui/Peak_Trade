from __future__ import annotations

import pytest

from src.execution.replay_pack.contract import SchemaValidationError, validate_manifest_v1_dict


def test_manifest_schema_strict_missing_required_key_fails() -> None:
    with pytest.raises(SchemaValidationError):
        validate_manifest_v1_dict(
            {
                # missing contract_version
                "bundle_id": "b",
                "run_id": "r",
                "created_at_utc": "2000-01-01T00:00:00+00:00",
                "peak_trade_git_sha": "UNKNOWN",
                "producer": {"tool": "pt_replay_pack", "version": "1.0"},
                "contents": [
                    {
                        "path": "events/execution_events.jsonl",
                        "sha256": "0" * 64,
                        "bytes": 0,
                        "media_type": "application/jsonl",
                    }
                ],
                "canonicalization": {
                    "json": "sort_keys_utf8_no_ws",
                    "jsonl": "one_object_per_line_sorted_keys_lf",
                },
                "invariants": {"has_execution_events": True, "ordering": "event_time_utc_then_seq"},
            }
        )


def test_manifest_schema_strict_rejects_bad_canonicalization_enum() -> None:
    with pytest.raises(SchemaValidationError):
        validate_manifest_v1_dict(
            {
                "contract_version": "1",
                "bundle_id": "b",
                "run_id": "r",
                "created_at_utc": "2000-01-01T00:00:00+00:00",
                "peak_trade_git_sha": "UNKNOWN",
                "producer": {"tool": "pt_replay_pack", "version": "1.0"},
                "contents": [
                    {
                        "path": "events/execution_events.jsonl",
                        "sha256": "0" * 64,
                        "bytes": 0,
                        "media_type": "application/jsonl",
                    }
                ],
                "canonicalization": {"json": "nope", "jsonl": "one_object_per_line_sorted_keys_lf"},
                "invariants": {"has_execution_events": True, "ordering": "event_time_utc_then_seq"},
            }
        )
