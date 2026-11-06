import json
import subprocess
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "scripts" / "aiops" / "run_paper_trading_session.py"
BASE_SPEC = REPO_ROOT / "tests" / "fixtures" / "p7" / "paper_run_min_v0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_spec(tmp_path: Path, payload: dict, name: str) -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _run(spec: Path, outdir: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--spec",
            str(spec),
            "--outdir",
            str(outdir),
        ],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_insufficient_cash_failure(result: subprocess.CompletedProcess[str]) -> None:
    assert result.returncode != 0
    assert "INSUFFICIENT_CASH" in result.stderr
    assert "Traceback" in result.stderr


def _assert_no_json_outputs(outdir: Path) -> None:
    assert outdir.exists()
    assert sorted(path.name for path in outdir.rglob("*.json")) == []


@pytest.mark.parametrize(
    ("case_name", "patch"),
    [
        ("very_low_initial_cash", {"initial_cash": 1.0}),
        ("zero_initial_cash", {"initial_cash": 0.0}),
        ("negative_initial_cash", {"initial_cash": -1.0}),
    ],
)
def test_paper_runner_fails_closed_when_initial_cash_cannot_cover_buy(
    tmp_path: Path,
    case_name: str,
    patch: dict,
) -> None:
    payload = _load(BASE_SPEC)
    payload.update(patch)
    spec = _write_spec(tmp_path, payload, f"{case_name}.json")
    outdir = tmp_path / f"{case_name}_out"

    result = _run(spec, outdir)

    _assert_insufficient_cash_failure(result)
    _assert_no_json_outputs(outdir)


def test_paper_runner_fails_closed_when_buy_quantity_exceeds_cash(tmp_path: Path) -> None:
    payload = _load(BASE_SPEC)
    payload["orders"] = [{**payload["orders"][0], "qty": 1_000_000.0}]
    spec = _write_spec(tmp_path, payload, "large_buy_qty.json")
    outdir = tmp_path / "large_buy_qty_out"

    result = _run(spec, outdir)

    _assert_insufficient_cash_failure(result)
    _assert_no_json_outputs(outdir)


def test_paper_runner_insufficient_cash_cases_do_not_write_partial_outputs(tmp_path: Path) -> None:
    payload = _load(BASE_SPEC)
    payload["initial_cash"] = 1.0
    spec = _write_spec(tmp_path, payload, "insufficient_cash.json")
    outdir = tmp_path / "insufficient_cash_out"

    result = _run(spec, outdir)

    _assert_insufficient_cash_failure(result)
    assert not (outdir / "fills.json").exists()
    assert not (outdir / "account.json").exists()
    assert not (outdir / "evidence_manifest.json").exists()
    _assert_no_json_outputs(outdir)
