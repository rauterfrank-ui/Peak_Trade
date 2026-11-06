from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.execution.determinism import stable_id
from src.execution.replay_pack.builder import build_replay_pack
from src.execution.replay_pack.canonical import dumps_canonical
from src.execution.replay_pack.contract import ContractViolationError
from src.execution.replay_pack.hashing import (
    collect_files_for_hashing,
    sha256_file,
    write_sha256sums,
)
from src.execution.replay_pack.validator import validate_replay_pack


def _mk_event(run_id: str, ts_sim: int) -> dict:
    fields = {
        "run_id": run_id,
        "session_id": "s",
        "intent_id": "i",
        "symbol": "BTC/EUR",
        "event_type": "INTENT",
        "ts_sim": ts_sim,
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
        "ts_sim": ts_sim,
        "ts_utc": "2026-01-01T00:00:00+00:00",
        "request_id": None,
        "client_order_id": None,
        "reason_code": None,
        "reason_detail": None,
        "payload": {},
    }


def test_validator_rejects_floats_in_events_even_if_hashes_match(
    tmp_path: Path, monkeypatch
) -> None:
    # Make builder deterministic for golden-like hashing.
    import src.execution.replay_pack.builder as builder_mod

    monkeypatch.setattr(builder_mod, "_git_info", lambda _p: {"commit_sha": "TEST", "dirty": False})
    monkeypatch.setattr(
        builder_mod,
        "_env_info",
        lambda: {
            "python_version": "0.0.0",
            "python_implementation": "TEST",
            "platform": "test",
            "platform_release": "0",
        },
    )

    run_id = "run_float_001"
    run_dir = tmp_path / "run_dir"
    events_path = run_dir / "logs" / "execution" / "execution_events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)

    with open(events_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            json.dumps(
                _mk_event(run_id, 0), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        )
        f.write("\n")

    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    # Tamper events file to include a float (but then update hashes so hash checks pass).
    ev_file = bundle_root / "events" / "execution_events.jsonl"
    lines = ev_file.read_text(encoding="utf-8").splitlines()
    obj = json.loads(lines[0])
    obj["ts_sim"] = 0.5  # float
    with open(ev_file, "w", encoding="utf-8", newline="\n") as f:
        # Write JSON with float (must bypass canonical writer which forbids floats).
        f.write(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        f.write("\n")

    # Update manifest entry for the tampered file.
    manifest_path = bundle_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for entry in manifest["contents"]:
        if entry["path"] == "events/execution_events.jsonl":
            entry["sha256"] = sha256_file(ev_file)
            entry["bytes"] = int(ev_file.stat().st_size)
            break
    with open(manifest_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(dumps_canonical(manifest))
        f.write("\n")

    # Regenerate sha256sums to match modified files (includes manifest.json).
    write_sha256sums(bundle_root, collect_files_for_hashing(bundle_root))

    with pytest.raises(ContractViolationError):
        validate_replay_pack(bundle_root)
