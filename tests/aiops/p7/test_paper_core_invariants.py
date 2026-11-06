import json
import subprocess
import sys
from pathlib import Path

SPEC = Path("tests/fixtures/p7/paper_run_min_v0.json")


def _load(p: Path):
    return json.loads(p.read_text(encoding="utf-8"))


def test_p7_min_spec_fixture_is_valid_json():
    data = _load(SPEC)
    assert isinstance(data, dict)
    assert "schema_version" in data


def test_p7_runner_produces_canonical_outputs_and_basic_invariants(tmp_path):
    outdir = tmp_path / "p7_run"
    outdir.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "scripts/aiops/run_paper_trading_session.py",
        "--spec",
        str(SPEC),
        "--run-id",
        "p7_invariants_test",
        "--outdir",
        str(outdir),
        "--evidence",
        "0",
    ]
    subprocess.check_call(cmd)

    fills_p = outdir / "fills.json"
    acct_p = outdir / "account.json"
    assert fills_p.exists(), "fills.json missing"
    assert acct_p.exists(), "account.json missing"

    fills = _load(fills_p)
    acct = _load(acct_p)

    assert isinstance(fills, dict)
    assert isinstance(acct, dict)

    rows = fills.get("fills") or fills.get("rows") or []
    assert isinstance(rows, list)

    for f in rows:
        if not isinstance(f, dict):
            continue
        fee = f.get("fee", None)
        if fee is not None:
            assert float(fee) >= 0.0

    assert any(k in acct for k in ["cash", "balances", "account"]), (
        "account.json missing expected top-level keys"
    )
