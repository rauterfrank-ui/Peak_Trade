from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from src.execution.determinism import stable_id
from src.execution.replay_pack.builder import build_replay_pack
from src.execution.replay_pack.canonical import write_json_canonical
from src.execution.replay_pack.hashing import (
    collect_files_for_hashing,
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
    import json

    events_path = run_dir / "logs" / "execution" / "execution_events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    with open(events_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            json.dumps(
                _mk_event(run_id, 0), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        )
        f.write("\n")


def _add_market_data_refs(bundle_root: Path, doc: object) -> None:
    write_json_canonical(bundle_root / "events" / "market_data_refs.json", doc)
    # New file must be covered by sha256sums.txt.
    write_sha256sums(bundle_root, collect_files_for_hashing(bundle_root))


def _run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/execution/pt_replay_pack.py", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def _read_report(bundle_root: Path) -> dict:
    import json

    p = bundle_root / "meta" / "resolution_report.json"
    assert p.exists()
    return json.loads(p.read_text(encoding="utf-8"))


def test_cli_resolve_datarefs_best_effort_missing_optional_ok(tmp_path: Path) -> None:
    run_id = "run_cli_md_best_effort"
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
    # One resolved, one missing optional.
    resolved_rel = "peaktrade_cache/bars_1m/us_equities/AAPL.bars.1m.2026-01-01T00:00:00Z_2026-01-01T06:00:00Z.parquet"
    target = cache_root / resolved_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"hello")

    doc = {
        "market_data_refs": [
            {
                "ref_id": "mdref-0001",
                "kind": "bars",
                "symbol": "AAPL",
                "timeframe": "1m",
                "start_utc": "2026-01-01T00:00:00Z",
                "end_utc": "2026-01-01T06:00:00Z",
                "source": "local_cache",
                "locator": {
                    "namespace": "peaktrade_cache",
                    "dataset": "bars_1m",
                    "partition": "us_equities",
                },
                "required": False,
            },
            {
                "ref_id": "mdref-0002",
                "kind": "bars",
                "symbol": "MISSING",
                "timeframe": "1m",
                "start_utc": "2026-01-01T00:00:00Z",
                "end_utc": "2026-01-01T06:00:00Z",
                "source": "local_cache",
                "locator": {
                    "namespace": "peaktrade_cache",
                    "dataset": "bars_1m",
                    "partition": "us_equities",
                },
                "required": False,
            },
        ]
    }
    _add_market_data_refs(bundle_root, doc)

    cp = _run_cli(
        [
            "resolve-datarefs",
            "--bundle",
            str(bundle_root),
            "--cache-root",
            str(cache_root),
            "--mode",
            "best_effort",
            "--generated-at-utc",
            "2000-01-01T00:00:00Z",
        ],
        cwd=_repo_root(),
    )
    assert cp.returncode == 0, cp.stderr

    report = _read_report(bundle_root)
    assert report["summary"]["total"] == 2
    assert report["summary"]["resolved"] == 1
    assert report["summary"]["missing"] == 1


def test_cli_resolve_datarefs_strict_missing_required_exit_6(tmp_path: Path) -> None:
    run_id = "run_cli_md_strict_missing"
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

    doc = [
        {
            "ref_id": "mdref-req-0001",
            "kind": "bars",
            "symbol": "AAPL",
            "timeframe": "1m",
            "start_utc": "2026-01-01T00:00:00Z",
            "end_utc": "2026-01-01T06:00:00Z",
            "source": "local_cache",
            "locator": {
                "namespace": "peaktrade_cache",
                "dataset": "bars_1m",
                "partition": "us_equities",
            },
            "required": True,
        }
    ]
    _add_market_data_refs(bundle_root, doc)

    cp = _run_cli(
        [
            "resolve-datarefs",
            "--bundle",
            str(bundle_root),
            "--cache-root",
            str(cache_root),
            "--mode",
            "strict",
            "--generated-at-utc",
            "2000-01-01T00:00:00Z",
        ],
        cwd=_repo_root(),
    )
    assert cp.returncode == 6
    report = _read_report(bundle_root)
    assert report["summary"]["missing"] == 1


def test_cli_resolve_datarefs_hash_hint_mismatch_exit_3(tmp_path: Path) -> None:
    run_id = "run_cli_md_hash_mismatch"
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

    resolved_rel = "peaktrade_cache/bars_1m/us_equities/AAPL.bars.1m.2026-01-01T00:00:00Z_2026-01-01T06:00:00Z.parquet"
    target = cache_root / resolved_rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"hello")
    got = sha256_file(target)
    assert got != "0" * 64

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
                "locator": {
                    "namespace": "peaktrade_cache",
                    "dataset": "bars_1m",
                    "partition": "us_equities",
                },
                "sha256_hint": "0" * 64,
                "required": False,
            }
        ],
    }
    _add_market_data_refs(bundle_root, doc)

    cp = _run_cli(
        [
            "resolve-datarefs",
            "--bundle",
            str(bundle_root),
            "--cache-root",
            str(cache_root),
            "--mode",
            "strict",
            "--generated-at-utc",
            "2000-01-01T00:00:00Z",
        ],
        cwd=_repo_root(),
    )
    assert cp.returncode == 3
    report = _read_report(bundle_root)
    assert report["summary"]["hash_mismatch"] == 1


@pytest.mark.parametrize(
    "doc",
    [
        [
            {
                "ref_id": "mdref-0001",
                "kind": "bars",
                "symbol": "AAPL",
                "timeframe": "1m",
                "start_utc": "2026-01-01T00:00:00Z",
                "end_utc": "2026-01-01T06:00:00Z",
                "source": "local_cache",
                "locator": {"namespace": "peaktrade_cache", "dataset": "bars_1m"},
                "required": False,
            }
        ],
        {
            "market_data_refs": [
                {
                    "ref_id": "mdref-0001",
                    "kind": "bars",
                    "symbol": "AAPL",
                    "timeframe": "1m",
                    "start_utc": "2026-01-01T00:00:00Z",
                    "end_utc": "2026-01-01T06:00:00Z",
                    "source": "local_cache",
                    "locator": {"namespace": "peaktrade_cache", "dataset": "bars_1m"},
                    "required": False,
                }
            ]
        },
        {
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
                    "required": False,
                }
            ],
        },
    ],
)
def test_cli_parse_variants_all_accepted(tmp_path: Path, doc: object) -> None:
    run_id = "run_cli_md_variants"
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
    _add_market_data_refs(bundle_root, doc)

    cp = _run_cli(
        [
            "resolve-datarefs",
            "--bundle",
            str(bundle_root),
            "--cache-root",
            str(cache_root),
            "--mode",
            "best_effort",
            "--generated-at-utc",
            "2000-01-01T00:00:00Z",
        ],
        cwd=_repo_root(),
    )
    assert cp.returncode == 0, cp.stderr


def test_cli_replay_with_resolve_datarefs_strict_missing_required_exit_6(tmp_path: Path) -> None:
    run_id = "run_cli_md_replay_strict_missing"
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

    doc = {
        "market_data_refs": [
            {
                "ref_id": "mdref-req-0001",
                "kind": "bars",
                "symbol": "AAPL",
                "timeframe": "1m",
                "start_utc": "2026-01-01T00:00:00Z",
                "end_utc": "2026-01-01T06:00:00Z",
                "source": "local_cache",
                "locator": {
                    "namespace": "peaktrade_cache",
                    "dataset": "bars_1m",
                    "partition": "us_equities",
                },
                "required": True,
            }
        ]
    }
    _add_market_data_refs(bundle_root, doc)

    cp = _run_cli(
        [
            "replay",
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
