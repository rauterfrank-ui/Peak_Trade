from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.execution.determinism import stable_id
from src.execution.replay_pack.builder import build_replay_pack
from src.execution.replay_pack.hashing import sha256_file
from src.execution.replay_pack.validator import validate_replay_pack
from src.execution.replay_pack.contract import MissingRequiredFileError


def _mk_event(run_id: str, ts_sim: int) -> dict:
    fields = {
        "run_id": run_id,
        "session_id": "s",
        "intent_id": "i",
        "symbol": "BTC/EUR",
        "event_type": "FILL",
        "ts_sim": ts_sim,
        "request_id": None,
        "client_order_id": "order_001",
        "reason_code": None,
        "payload": {
            "fill_id": f"fill_{ts_sim}",
            "side": "BUY",
            "quantity": "0.01000000",
            "price": "50000.00000000",
            "fee": "0.50000000",
            "fee_currency": "EUR",
        },
    }
    event_id = stable_id(kind="execution_event", fields=fields)
    return {
        "schema_version": "BETA_EXEC_V1",
        "event_id": event_id,
        "run_id": run_id,
        "session_id": "s",
        "intent_id": "i",
        "symbol": "BTC/EUR",
        "event_type": "FILL",
        "ts_sim": ts_sim,
        "ts_utc": "2026-01-01T00:00:00+00:00",
        "request_id": None,
        "client_order_id": "order_001",
        "reason_code": None,
        "reason_detail": None,
        "payload": fields["payload"],
    }


def _write_events(events_path: Path, run_id: str) -> None:
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with open(events_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            json.dumps(
                _mk_event(run_id, 0), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        )
        f.write("\n")


def _read_all_files(root: Path) -> dict[str, bytes]:
    out: dict[str, bytes] = {}
    for p in root.rglob("*"):
        if p.is_file():
            rel = p.relative_to(root).as_posix()
            out[rel] = p.read_bytes()
    return out


def test_v2_build_is_deterministic_bytes_and_manifest_hash(tmp_path: Path, monkeypatch) -> None:
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

    run_id = "run_v2_det_001"
    run_dir = tmp_path / "run_dir"
    events_path = run_dir / "logs" / "execution" / "execution_events.jsonl"
    _write_events(events_path, run_id)

    b1 = build_replay_pack(
        run_dir,
        tmp_path / "out1",
        bundle_version="2",
        include_fifo=True,
        include_fifo_entries=True,
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )
    b2 = build_replay_pack(
        run_dir,
        tmp_path / "out2",
        bundle_version="2",
        include_fifo=True,
        include_fifo_entries=True,
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    validate_replay_pack(b1)
    validate_replay_pack(b2)

    files1 = _read_all_files(b1)
    files2 = _read_all_files(b2)
    assert files1.keys() == files2.keys()
    for k in sorted(files1.keys()):
        assert files1[k] == files2[k], f"bundle bytes differ for {k}"

    assert sha256_file(b1 / "manifest.json") == sha256_file(b2 / "manifest.json")


def test_v2_does_not_change_legacy_files_vs_v1(tmp_path: Path, monkeypatch) -> None:
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

    run_id = "run_v2_legacy_001"
    run_dir = tmp_path / "run_dir"
    events_path = run_dir / "logs" / "execution" / "execution_events.jsonl"
    _write_events(events_path, run_id)

    b1 = build_replay_pack(
        run_dir,
        tmp_path / "out_v1",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )
    b2 = build_replay_pack(
        run_dir,
        tmp_path / "out_v2",
        bundle_version="2",
        include_fifo=True,
        include_fifo_entries=True,
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    # Shared legacy files must be byte-identical.
    shared = [
        "events/execution_events.jsonl",
        "inputs/config_snapshot.json",
        "meta/git.json",
        "meta/env.json",
    ]
    for rel in shared:
        assert (b1 / rel).read_bytes() == (b2 / rel).read_bytes(), f"changed legacy file: {rel}"


def test_v2_missing_fifo_snapshot_is_rejected(tmp_path: Path, monkeypatch) -> None:
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

    run_id = "run_v2_missing_001"
    run_dir = tmp_path / "run_dir"
    events_path = run_dir / "logs" / "execution" / "execution_events.jsonl"
    _write_events(events_path, run_id)

    b2 = build_replay_pack(
        run_dir,
        tmp_path / "out_v2",
        bundle_version="2",
        include_fifo=True,
        include_fifo_entries=False,
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    # Tamper: remove required v2 FIFO snapshot file.
    (b2 / "ledger" / "ledger_fifo_snapshot.json").unlink()

    with pytest.raises(MissingRequiredFileError):
        validate_replay_pack(b2)
