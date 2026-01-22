from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.execution.determinism import stable_id
from src.execution.replay_pack.builder import build_replay_pack
from src.execution.replay_pack.contract import ContractViolationError
from src.execution.replay_pack.validator import validate_replay_pack


def _mk_event(run_id: str) -> dict:
    fields = {
        "run_id": run_id,
        "session_id": "s",
        "intent_id": "i",
        "symbol": "BTC/EUR",
        "event_type": "INTENT",
        "ts_sim": 0,
        "request_id": None,
        "client_order_id": None,
        "reason_code": None,
        "payload": {},
    }
    event_id = stable_id(kind="execution_event", fields=fields)
    return {
        "schema_version": "BETA_EXEC_V1",
        "event_id": event_id,
        "run_id": run_id,
        "session_id": "s",
        "intent_id": "i",
        "symbol": "BTC/EUR",
        "event_type": "INTENT",
        "ts_sim": 0,
        "ts_utc": "2026-01-01T00:00:00+00:00",
        "request_id": None,
        "client_order_id": None,
        "reason_code": None,
        "reason_detail": None,
        "payload": {},
    }


def test_manifest_crlf_is_rejected(tmp_path: Path) -> None:
    run_id = "run_lf_001"
    run_dir = tmp_path / "run_dir"
    events_path = run_dir / "logs" / "execution" / "execution_events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with open(events_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            json.dumps(_mk_event(run_id), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        )
        f.write("\n")

    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    manifest_path = bundle_root / "manifest.json"
    b = manifest_path.read_bytes()
    manifest_path.write_bytes(b.replace(b"\n", b"\r\n"))

    with pytest.raises(ContractViolationError):
        validate_replay_pack(bundle_root)


def test_sha256sums_crlf_is_rejected(tmp_path: Path) -> None:
    run_id = "run_lf_002"
    run_dir = tmp_path / "run_dir"
    events_path = run_dir / "logs" / "execution" / "execution_events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with open(events_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            json.dumps(_mk_event(run_id), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        )
        f.write("\n")

    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    sums_path = bundle_root / "hashes" / "sha256sums.txt"
    b = sums_path.read_bytes()
    sums_path.write_bytes(b.replace(b"\n", b"\r\n"))

    with pytest.raises(ContractViolationError):
        validate_replay_pack(bundle_root)
