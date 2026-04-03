"""Exit-Codes und Run-Manifest fuer sweep_parameters (NO-LIVE)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))


def test_sweep_parameters_exit_1_missing_config(tmp_path, monkeypatch) -> None:
    import sweep_parameters as sp

    monkeypatch.chdir(tmp_path)
    code = sp.main(["--config-path", str(tmp_path / "missing.toml")])
    assert code == 1
    man = tmp_path / "reports" / "sweeps" / "sweep_parameters_run_manifest.json"
    assert man.is_file()
    payload = json.loads(man.read_text(encoding="utf-8"))
    assert payload["exit_code"] == 1
    assert payload["script_name"] == "sweep_parameters.py"
    assert "run_id" in payload and len(payload["run_id"]) == 64
    assert payload.get("generated_at_utc") and isinstance(payload["generated_at_utc"], str)
    assert payload["generated_at_utc"].endswith("Z")
    assert payload["config_path"] == str(tmp_path / "missing.toml")


def test_sweep_parameters_exit_1_no_successful_runs(tmp_path, monkeypatch) -> None:
    """Grid ok, aber jeder Backtest schlaegt fehl -> keine Zeilen -> Exit 1."""
    import sweep_parameters as sp

    cfg = ROOT / "config" / "config.test.toml"
    if not cfg.is_file():
        pytest.skip(f"fehlt: {cfg}")

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        sp,
        "build_param_grid",
        lambda _cfg, strategy_key: (["fast_window"], [(20,)]),
    )
    monkeypatch.setattr(
        sp,
        "run_backtest_for_params",
        lambda **_kw: (_ for _ in ()).throw(RuntimeError("simulated")),
    )

    code = sp.main(
        [
            "--config-path",
            str(cfg),
            "--strategy",
            "ma_crossover",
            "--symbol",
            "BTC/EUR",
            "--run-name",
            "contract_fail",
            "--top-k-reports",
            "0",
            "--max-runs",
            "2",
        ]
    )
    assert code == 1
    man = tmp_path / "reports" / "sweeps" / "sweep_ma_crossover_contract_fail_run_manifest.json"
    assert man.is_file()
    payload = json.loads(man.read_text(encoding="utf-8"))
    assert payload["exit_code"] == 1
    assert "error" in payload
    assert "run_id" in payload and len(payload["run_id"]) == 64
    assert payload.get("generated_at_utc") and isinstance(payload["generated_at_utc"], str)
    assert payload["generated_at_utc"].endswith("Z")
    assert payload["config_path"] == str(cfg)
    assert payload["strategy"] == "ma_crossover"
    assert payload["symbols"] == ["BTC/EUR"]
