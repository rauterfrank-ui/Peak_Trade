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


def _write_events_file(run_dir: Path, run_id: str) -> None:
    events_path = run_dir / "logs" / "execution" / "execution_events.jsonl"
    events_path.parent.mkdir(parents=True, exist_ok=True)
    fields = {
        "run_id": run_id,
        "session_id": "s",
        "intent_id": "i",
        "symbol": "AAPL/USD",
        "event_type": "FILL",
        "ts_sim": 0,
        "request_id": None,
        "client_order_id": "order_001",
        "reason_code": None,
        "payload": {
            "fill_id": "fill_0",
            "side": "BUY",
            "quantity": "1",
            "price": "1",
            "fee": "0",
            "fee_currency": "USD",
        },
    }
    # Minimal BETA_EXEC_V1 event (same shape + stable_id rules as other replay_pack tests).
    obj = {
        "schema_version": "BETA_EXEC_V1",
        "event_id": stable_id(kind="execution_event", fields=fields),
        "run_id": run_id,
        "session_id": "s",
        "intent_id": "i",
        "symbol": "AAPL/USD",
        "event_type": "FILL",
        "ts_sim": 0,
        "ts_utc": "2026-01-01T00:00:00+00:00",
        "request_id": None,
        "client_order_id": "order_001",
        "reason_code": None,
        "reason_detail": None,
        "payload": fields["payload"],
    }
    with open(events_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
        f.write("\n")


def _run_script(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", "scripts/ops/pt_replay_regression_pack.sh", *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


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
    contents = sorted(contents, key=lambda x: x["path"])
    manifest["contents"] = contents
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


def test_regression_pack_with_existing_bundle_writes_stable_layout(tmp_path: Path) -> None:
    run_id = "run_regpack_existing_bundle"
    run_dir = tmp_path / "run_dir"
    _write_events_file(run_dir, run_id)
    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "built_out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    out_dir = tmp_path / "reg_out"
    cp = _run_script(["--bundle", str(bundle_root), "--out-dir", str(out_dir)], cwd=_repo_root())
    assert cp.returncode == 0, cp.stderr
    assert "STATUS=PASS" in cp.stdout

    assert (out_dir / "reports" / "compare_report.json").exists()
    assert (out_dir / "reports" / "compare_summary.min.json").exists()
    assert (out_dir / "logs" / "regression_pack.log").exists()

    # Determinism invariants: LF-only and trailing LF.
    b = (out_dir / "reports" / "compare_summary.min.json").read_bytes()
    assert b"\r\n" not in b
    assert b.endswith(b"\n")

    # Default bundle-mode is symlink (portable stable layout under OUT_DIR).
    assert (out_dir / "bundle").is_symlink()


def test_regression_pack_existing_bundle_can_copy_bundle_into_out_dir(tmp_path: Path) -> None:
    run_id = "run_regpack_existing_bundle_copy"
    run_dir = tmp_path / "run_dir"
    _write_events_file(run_dir, run_id)
    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "built_out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=False,
    )

    out_dir = tmp_path / "reg_out"
    cp = _run_script(
        ["--bundle", str(bundle_root), "--bundle-mode", "copy", "--out-dir", str(out_dir)],
        cwd=_repo_root(),
    )
    assert cp.returncode == 0, cp.stderr
    assert "STATUS=PASS" in cp.stdout
    assert (out_dir / "bundle").exists()
    assert (out_dir / "bundle").is_dir()


def test_regression_pack_builds_bundle_when_missing_and_links_or_moves(tmp_path: Path) -> None:
    run_id = "run_regpack_build"
    run_dir = tmp_path / "run_dir"
    _write_events_file(run_dir, run_id)

    out_dir = tmp_path / "reg_out"
    cp = _run_script(
        [
            "--run-id-or-dir",
            str(run_dir),
            "--out-dir",
            str(out_dir),
            "--generated-at-utc",
            "2000-01-01T00:00:00Z",
        ],
        cwd=_repo_root(),
    )
    assert cp.returncode == 0, cp.stderr
    assert (out_dir / "bundle").exists()
    assert (out_dir / "reports" / "compare_report.json").exists()
    assert (out_dir / "reports" / "compare_summary.min.json").exists()


def test_regression_pack_preserves_compare_exit_code_4_when_outputs_mismatch(
    tmp_path: Path,
) -> None:
    run_id = "run_regpack_mismatch"
    run_dir = tmp_path / "run_dir"
    _write_events_file(run_dir, run_id)
    bundle_root = build_replay_pack(
        run_dir,
        tmp_path / "built_out",
        created_at_utc_override="2000-01-01T00:00:00+00:00",
        include_outputs=True,
    )

    # Force an expected output mismatch deterministically, but keep bundle hash-valid.
    pos_path = bundle_root / "outputs" / "expected_positions.json"
    expected = json.loads(pos_path.read_text(encoding="utf-8"))
    first_sym = sorted(expected.keys())[0]
    expected[first_sym]["quantity"] = "999"
    write_json_canonical(pos_path, expected)
    _update_manifest_for_file(bundle_root, "outputs/expected_positions.json")

    out_dir = tmp_path / "reg_out"
    cp = _run_script(
        [
            "--bundle",
            str(bundle_root),
            "--out-dir",
            str(out_dir),
            "--check-outputs",
            "--generated-at-utc",
            "2000-01-01T00:00:00Z",
        ],
        cwd=_repo_root(),
    )
    assert cp.returncode == 4, cp.stderr
    assert (out_dir / "reports" / "compare_report.json").exists()
    assert (out_dir / "reports" / "compare_summary.min.json").exists()
