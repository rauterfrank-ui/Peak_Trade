from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from src.execution.determinism import stable_id
from src.execution.replay_pack.builder import build_replay_pack
from src.execution.replay_pack.canonical import dumps_canonical, write_json_canonical
from src.execution.replay_pack.hashing import (
    collect_files_for_hashing,
    sha256_bytes,
    sha256_file,
    write_sha256sums,
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _mk_event(run_id: str, ts_sim: int = 0) -> dict:
    fields = {
        "run_id": run_id,
        "session_id": "s",
        "intent_id": "i",
        "symbol": "AAPL/USD",
        "event_type": "FILL",
        "ts_sim": ts_sim,
        "request_id": None,
        "client_order_id": "order_001",
        "reason_code": None,
        "payload": {
            "fill_id": f"fill_{ts_sim}",
            "side": "BUY",
            "quantity": "1",
            "price": "1",
            "fee": "0",
            "fee_currency": "USD",
        },
    }
    event_id = stable_id(kind="execution_event", fields=fields)
    return {
        "schema_version": "BETA_EXEC_V1",
        "event_id": event_id,
        "run_id": run_id,
        "session_id": "s",
        "intent_id": "i",
        "symbol": "AAPL/USD",
        "event_type": "FILL",
        "ts_sim": ts_sim,
        "ts_utc": "2026-01-01T00:00:00+00:00",
        "request_id": None,
        "client_order_id": "order_001",
        "reason_code": None,
        "reason_detail": None,
        "payload": fields["payload"],
    }


def _write_events_file(run_dir: Path, run_id: str) -> None:
    events_path = run_dir / "logs" / "execution" / "execution_events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with open(events_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            json.dumps(
                _mk_event(run_id, 0), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        )
        f.write("\n")


def _run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/execution/pt_replay_pack.py", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def _read_compare_report(bundle_root: Path) -> dict:
    p = bundle_root / "meta" / "compare_report.json"
    assert p.exists()
    return json.loads(p.read_text(encoding="utf-8"))


def _update_manifest_for_file(bundle_root: Path, relpath: str) -> None:
    manifest_path = bundle_root / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    contents = manifest["contents"]
    for c in contents:
        if c["path"] == relpath:
            abs_p = bundle_root / relpath
            c["sha256"] = sha256_file(abs_p)
            c["bytes"] = int(abs_p.stat().st_size)
            break
    # Keep sorted by path.
    contents = sorted(contents, key=lambda x: x["path"])
    manifest["contents"] = contents
    # Recompute bundle_id deterministically (same rule as builder).
    material = dumps_canonical(
        {
            "contract_version": str(manifest.get("contract_version") or ""),
            "run_id": str(manifest.get("run_id") or ""),
            "contents": [{"path": c["path"], "sha256": c["sha256"]} for c in contents],
        }
    ).encode("utf-8")
    manifest["bundle_id"] = sha256_bytes(material)
    write_json_canonical(manifest_path, manifest)
    write_sha256sums(bundle_root, collect_files_for_hashing(bundle_root))


def _add_market_data_refs(bundle_root: Path, doc: object) -> None:
    write_json_canonical(bundle_root / "events" / "market_data_refs.json", doc)
    write_sha256sums(bundle_root, collect_files_for_hashing(bundle_root))


def test_compare_minimal_bundle_no_expected_outputs_pass(tmp_path: Path) -> None:
    run_id = "run_cmp_minimal"
    run_dir = tmp_path / "run_dir"
    _write_events_file(run_dir, run_id)
    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    cp = _run_cli(
        ["compare", "--bundle", str(bundle_root), "--generated-at-utc", "2000-01-01T00:00:00Z"],
        cwd=_repo_root(),
    )
    assert cp.returncode == 0, cp.stderr
    rep = _read_compare_report(bundle_root)
    assert rep["summary"]["status"] == "PASS"
    assert rep["replay"]["invariants"]["fills"] == "SKIP"
    assert rep["replay"]["invariants"]["positions"] == "SKIP"
    assert "datarefs" not in rep


def test_compare_with_expected_outputs_pass(tmp_path: Path) -> None:
    run_id = "run_cmp_outputs_pass"
    run_dir = tmp_path / "run_dir"
    _write_events_file(run_dir, run_id)
    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=True,
    )

    cp = _run_cli(
        [
            "compare",
            "--bundle",
            str(bundle_root),
            "--check-outputs",
            "--generated-at-utc",
            "2000-01-01T00:00:00Z",
        ],
        cwd=_repo_root(),
    )
    assert cp.returncode == 0, cp.stderr
    rep = _read_compare_report(bundle_root)
    assert rep["replay"]["invariants"]["fills"] in ("PASS", "SKIP")
    assert rep["replay"]["invariants"]["positions"] in ("PASS", "SKIP")


def test_compare_outputs_mismatch_exit_4_and_diffs(tmp_path: Path) -> None:
    run_id = "run_cmp_outputs_mismatch"
    run_dir = tmp_path / "run_dir"
    _write_events_file(run_dir, run_id)
    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=True,
    )

    # Corrupt expected_positions but keep bundle hashes valid.
    pos_path = bundle_root / "outputs" / "expected_positions.json"
    expected = json.loads(pos_path.read_text(encoding="utf-8"))
    # Force mismatch deterministically.
    first_sym = sorted(expected.keys())[0]
    expected[first_sym]["quantity"] = "999"
    write_json_canonical(pos_path, expected)
    _update_manifest_for_file(bundle_root, "outputs/expected_positions.json")

    cp = _run_cli(
        [
            "compare",
            "--bundle",
            str(bundle_root),
            "--check-outputs",
            "--generated-at-utc",
            "2000-01-01T00:00:00Z",
        ],
        cwd=_repo_root(),
    )
    assert cp.returncode == 4, cp.stderr
    rep = _read_compare_report(bundle_root)
    assert rep["summary"]["exit_code"] == 4
    assert rep["replay"]["invariants"]["positions"] == "FAIL"
    assert rep["replay"]["diffs"]["positions_diff"]["changed"] >= 1


def test_compare_datarefs_best_effort_missing_optional_exit_0(tmp_path: Path) -> None:
    run_id = "run_cmp_datarefs_best_effort"
    run_dir = tmp_path / "run_dir"
    _write_events_file(run_dir, run_id)
    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    doc = {
        "market_data_refs": [
            {
                "ref_id": "mdref-0001",
                "kind": "bars",
                "symbol": "MISSING",
                "timeframe": "1m",
                "start_utc": "2026-01-01T00:00:00Z",
                "end_utc": "2026-01-01T06:00:00Z",
                "source": "local_cache",
                "locator": {"namespace": "peaktrade_cache", "dataset": "bars_1m"},
                "required": False,
            }
        ]
    }
    _add_market_data_refs(bundle_root, doc)

    cache_root = tmp_path / "cache"
    cache_root.mkdir(parents=True, exist_ok=True)

    cp = _run_cli(
        [
            "compare",
            "--bundle",
            str(bundle_root),
            "--resolve-datarefs",
            "best_effort",
            "--cache-root",
            str(cache_root),
            "--generated-at-utc",
            "2000-01-01T00:00:00Z",
        ],
        cwd=_repo_root(),
    )
    assert cp.returncode == 0, cp.stderr
    rep = _read_compare_report(bundle_root)
    assert rep["datarefs"]["summary"]["missing"] == 1


def test_compare_datarefs_strict_missing_required_exit_6(tmp_path: Path) -> None:
    run_id = "run_cmp_datarefs_strict_missing"
    run_dir = tmp_path / "run_dir"
    _write_events_file(run_dir, run_id)
    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    doc = [
        {
            "ref_id": "mdref-req-0001",
            "kind": "bars",
            "symbol": "MISSING",
            "timeframe": "1m",
            "start_utc": "2026-01-01T00:00:00Z",
            "end_utc": "2026-01-01T06:00:00Z",
            "source": "local_cache",
            "locator": {"namespace": "peaktrade_cache", "dataset": "bars_1m"},
            "required": True,
        }
    ]
    _add_market_data_refs(bundle_root, doc)

    cache_root = tmp_path / "cache"
    cache_root.mkdir(parents=True, exist_ok=True)

    cp = _run_cli(
        [
            "compare",
            "--bundle",
            str(bundle_root),
            "--resolve-datarefs",
            "strict",
            "--cache-root",
            str(cache_root),
            "--generated-at-utc",
            "2000-01-01T00:00:00Z",
        ],
        cwd=_repo_root(),
    )
    assert cp.returncode == 6


def test_compare_datarefs_strict_hash_hint_mismatch_exit_3(tmp_path: Path) -> None:
    run_id = "run_cmp_datarefs_hash_mismatch"
    run_dir = tmp_path / "run_dir"
    _write_events_file(run_dir, run_id)
    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    cache_root = tmp_path / "cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    rel = "peaktrade_cache/bars_1m/AAPL.bars.1m.2026-01-01T00:00:00Z_2026-01-01T06:00:00Z.parquet"
    p = cache_root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"hello")

    doc = {
        "schema_version": "MARKET_DATA_REFS_V1",
        "refs": [
            {
                "ref_id": "mdref-0001",
                "kind": "bars",
                "symbol": "AAPL",
                "timeframe": "1m",
                "start_utc": "2026-01-01T00:00:00Z",
                "end_utc": "2026-01-01T06:00:00Z",
                "source": "local_cache",
                "locator": {"namespace": "peaktrade_cache", "dataset": "bars_1m"},
                "sha256_hint": "0" * 64,
                "required": False,
            }
        ],
    }
    _add_market_data_refs(bundle_root, doc)

    cp = _run_cli(
        [
            "compare",
            "--bundle",
            str(bundle_root),
            "--resolve-datarefs",
            "strict",
            "--cache-root",
            str(cache_root),
            "--generated-at-utc",
            "2000-01-01T00:00:00Z",
        ],
        cwd=_repo_root(),
    )
    assert cp.returncode == 3


def test_compare_report_bytes_deterministic_and_lf_only(tmp_path: Path) -> None:
    run_id = "run_cmp_deterministic"
    run_dir = tmp_path / "run_dir"
    _write_events_file(run_dir, run_id)
    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    args = ["compare", "--bundle", str(bundle_root), "--generated-at-utc", "2000-01-01T00:00:00Z"]
    cp1 = _run_cli(args, cwd=_repo_root())
    assert cp1.returncode == 0
    b1 = (bundle_root / "meta" / "compare_report.json").read_bytes()
    assert b"\r\n" not in b1
    assert b1.endswith(b"\n")

    cp2 = _run_cli(args, cwd=_repo_root())
    assert cp2.returncode == 0
    b2 = (bundle_root / "meta" / "compare_report.json").read_bytes()
    assert b1 == b2
