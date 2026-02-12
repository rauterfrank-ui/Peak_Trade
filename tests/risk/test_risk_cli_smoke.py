import json
import subprocess
import sys
from pathlib import Path


def test_risk_cli_var_smoke(tmp_path):
    returns = Path("tests/fixtures/returns_normal_5k.txt")
    assert returns.exists()
    run_id = "pytest_smoke_c2"
    out = subprocess.check_output(
        [
            sys.executable,
            "scripts/risk_cli.py",
            "--run-id",
            run_id,
            "--artifacts-dir",
            str(tmp_path),
            "var",
            "--returns-file",
            str(returns),
            "--alpha",
            "0.99",
            "--method",
            "historical",
        ],
        text=True,
        cwd=Path(__file__).resolve().parent.parent.parent,
    )
    j = json.loads(out)
    assert "var" in j and j["var"] >= 0.0
    assert (tmp_path / run_id / "meta.json").exists()
    assert (tmp_path / run_id / "results" / "var.json").exists()
