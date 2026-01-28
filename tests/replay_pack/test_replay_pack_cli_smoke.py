from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from src.execution.determinism import stable_id


def _repo_root() -> Path:
    # tests/replay_pack/test_replay_pack_cli_smoke.py -> repo root
    return Path(__file__).resolve().parents[2]


def _script_path() -> Path:
    return _repo_root() / "scripts" / "execution" / "pt_replay_pack.py"


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


def _write_events(path: Path, run_id: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(
            json.dumps(
                _mk_event(run_id, 0), sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        )
        f.write("\n")


def _run_cli(args: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_script_path()), *args],
        cwd=str(cwd),
        text=True,
        capture_output=True,
        check=False,
    )


def test_cli_build_validate_inspect_v1_and_v2(tmp_path: Path) -> None:
    repo = _repo_root()
    events = tmp_path / "execution_events.jsonl"
    _write_events(events, "run_cli_001")

    out1 = tmp_path / "out_v1"
    out2 = tmp_path / "out_v2"

    # v1 build from explicit events path
    r = _run_cli(
        [
            "build",
            "--events",
            str(events),
            "--out",
            str(out1),
            "--version",
            "1",
            "--created-at-utc",
            "2000-01-01T00:00:00+00:00",
        ],
        cwd=repo,
    )
    assert r.returncode == 0, f"build v1 failed: {r.stdout}\n{r.stderr}"

    bundle1 = out1 / "replay_pack"
    r = _run_cli(["validate", "--bundle", str(bundle1)], cwd=repo)
    assert r.returncode == 0, f"validate v1 failed: {r.stdout}\n{r.stderr}"

    r = _run_cli(["inspect", "--bundle", str(bundle1), "--json"], cwd=repo)
    assert r.returncode == 0, f"inspect v1 failed: {r.stdout}\n{r.stderr}"
    doc = json.loads(r.stdout.strip())
    assert doc["contract_version"] == "1"

    # v2 build from explicit events path
    r = _run_cli(
        [
            "build",
            "--events",
            str(events),
            "--out",
            str(out2),
            "--version",
            "2",
            "--include-fifo-entries",
            "--created-at-utc",
            "2000-01-01T00:00:00+00:00",
        ],
        cwd=repo,
    )
    assert r.returncode == 0, f"build v2 failed: {r.stdout}\n{r.stderr}"

    bundle2 = out2 / "replay_pack"
    r = _run_cli(["validate", "--bundle", str(bundle2)], cwd=repo)
    assert r.returncode == 0, f"validate v2 failed: {r.stdout}\n{r.stderr}"

    r = _run_cli(["inspect", "--bundle", str(bundle2), "--json"], cwd=repo)
    assert r.returncode == 0, f"inspect v2 failed: {r.stdout}\n{r.stderr}"
    doc = json.loads(r.stdout.strip())
    assert doc["contract_version"] == "2"
    assert doc["has_fifo_ledger"] is True
