from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
PAPER_RUNNER = REPO_ROOT / "scripts" / "aiops" / "run_paper_trading_session.py"
PAPER_RUN_MIN_SPEC = REPO_ROOT / "tests" / "fixtures" / "p7" / "paper_run_min_v0.json"
PAPER_RUN_HIGH_VOL_NO_TRADE_SPEC = (
    REPO_ROOT / "tests" / "fixtures" / "p7" / "paper_run_high_vol_no_trade_v0.json"
)

NON_LIVE_MARKERS = (
    "/Users/",
    "api_key",
    "secret",
    "submit_order",
    "real_order",
    "broker_connect",
    "exchange_connect",
)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json_spec(tmp_path: Path, payload: dict, name: str) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def run_paper_session(
    spec: Path,
    outdir: Path,
    *,
    dry_run: bool = False,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    args = [
        sys.executable,
        str(PAPER_RUNNER),
        "--spec",
        str(spec),
        "--outdir",
        str(outdir),
    ]
    if dry_run:
        args.append("--dry-run")
    if extra_args:
        args.extend(extra_args)

    return subprocess.run(
        args,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def assert_json_outputs_do_not_contain_live_markers(outdir: Path) -> None:
    for path in sorted(outdir.rglob("*.json")):
        text = path.read_text(encoding="utf-8")
        lowered = text.lower()
        for marker in NON_LIVE_MARKERS:
            if marker == "/Users/":
                assert marker not in text
            else:
                assert marker not in lowered


def assert_no_json_outputs(outdir: Path) -> None:
    assert outdir.exists()
    assert sorted(path.name for path in outdir.rglob("*.json")) == []
