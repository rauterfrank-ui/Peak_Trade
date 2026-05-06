from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "scripts" / "aiops" / "run_paper_trading_session.py"
BASE_SPEC = REPO_ROOT / "tests" / "fixtures" / "p7" / "paper_run_min_v0.json"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_spec(tmp_path: Path, payload: dict, name: str = "spec.json") -> Path:
    path = tmp_path / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def _run(
    spec: Path,
    outdir: Path,
    *,
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    cmd = [
        sys.executable,
        str(RUNNER),
        "--spec",
        str(spec),
        "--outdir",
        str(outdir),
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def _assert_no_outputs(outdir: Path) -> None:
    assert not outdir.exists() or not any(outdir.iterdir())


def test_paper_runner_fails_closed_when_spec_is_missing(tmp_path: Path) -> None:
    missing_spec = tmp_path / "missing.json"
    outdir = tmp_path / "out"

    result = _run(missing_spec, outdir)

    assert result.returncode != 0
    err = result.stderr
    assert (
        "No such file" in err
        or "cannot find the file" in err.lower()
        or "FileNotFoundError" in err
        or "errno 2" in err.lower()
    )
    _assert_no_outputs(outdir)


def test_paper_runner_fails_closed_when_spec_json_is_invalid(tmp_path: Path) -> None:
    spec = tmp_path / "invalid.json"
    spec.write_text("{not-json\n", encoding="utf-8")
    outdir = tmp_path / "out"

    result = _run(spec, outdir)

    assert result.returncode != 0
    assert (
        "JSON" in result.stderr or "Expecting" in result.stderr or "json.decoder" in result.stderr
    )
    _assert_no_outputs(outdir)


def test_paper_runner_fails_closed_when_initial_cash_missing(tmp_path: Path) -> None:
    """Runner uses spec['initial_cash']; missing key must not silently succeed."""
    payload = _load(BASE_SPEC)
    payload.pop("initial_cash")
    spec = _write_spec(tmp_path, payload)
    outdir = tmp_path / "out"

    result = _run(spec, outdir)

    assert result.returncode != 0
    assert "initial_cash" in result.stderr or "KeyError" in result.stderr
    _assert_no_outputs(outdir)


def test_paper_runner_fails_closed_when_order_side_is_invalid(tmp_path: Path) -> None:
    payload = _load(BASE_SPEC)
    payload["orders"][0]["side"] = "HOLD"
    spec = _write_spec(tmp_path, payload)
    outdir = tmp_path / "out"

    result = _run(spec, outdir)

    assert result.returncode != 0
    err = result.stderr
    assert (
        "INSUFFICIENT_POSITION" in err
        or "RuntimeError" in err
        or "HOLD" in err
        or "side" in err.lower()
    )
    _assert_no_outputs(outdir)


def test_paper_runner_fails_closed_when_mid_price_is_missing(tmp_path: Path) -> None:
    payload = _load(BASE_SPEC)
    payload["mid_prices"] = {}
    spec = _write_spec(tmp_path, payload)
    outdir = tmp_path / "out"

    result = _run(spec, outdir)

    assert result.returncode != 0
    err = result.stderr
    assert "KeyError" in err or "'BTC'" in err or "BTC" in err
    _assert_no_outputs(outdir)


def test_paper_runner_dry_run_fails_closed_when_outdir_is_non_empty(tmp_path: Path) -> None:
    """Non-empty guard exists for --dry-run; exec path would mkdir/write without this check."""
    outdir = tmp_path / "out"
    outdir.mkdir()
    (outdir / "existing.txt").write_text("do not overwrite\n", encoding="utf-8")

    result = _run(BASE_SPEC, outdir, extra_args=["--dry-run"])

    assert result.returncode == 2
    assert "not empty" in result.stderr.lower()
    assert (outdir / "existing.txt").read_text(encoding="utf-8") == "do not overwrite\n"
    assert sorted(path.name for path in outdir.iterdir()) == ["existing.txt"]
