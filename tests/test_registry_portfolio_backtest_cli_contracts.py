import os
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pytest
from typing import Dict, Optional, List


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = REPO_ROOT / "scripts" / "run_registry_portfolio_backtest.py"


def _run_cli(args: List[str], env: Optional[Dict[str, str]] = None) -> subprocess.CompletedProcess:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)

    return subprocess.run(
        [sys.executable, str(SCRIPT_PATH), *args],
        cwd=str(REPO_ROOT),
        env=merged_env,
        text=True,
        capture_output=True,
    )


def _write_toml(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _parse_strategy_list(output: str) -> list[str]:
    # Matches:
    #   1. ma_crossover
    #   2. momentum_1h
    return re.findall(r"^\s+\d+\.\s+([A-Za-z0-9_]+)\s*$", output, flags=re.MULTILINE)


def test_cli_rejects_limit_gt_720(tmp_path: Path) -> None:
    # Config only needed so the script can import/load cleanly, but argparse rejects before use.
    cfg = tmp_path / "config.toml"
    _write_toml(
        cfg,
        """
[backtest]
initial_cash = 10000.0
results_dir = "results"

[portfolio]
enabled = true
allocation_method = "equal"
total_capital = 10000.0

[strategies]
active = []
available = []
""".lstrip(),
    )

    p = _run_cli(["--limit", "721", "--dry-run"], env={"PEAK_TRADE_CONFIG": str(cfg)})
    assert p.returncode != 0
    combined = (p.stdout + "\n" + p.stderr).lower()
    assert "720" in combined
    assert "max" in combined or "darf" in combined


def test_cli_rejects_invalid_timeframe(tmp_path: Path) -> None:
    cfg = tmp_path / "config.toml"
    _write_toml(
        cfg,
        """
[backtest]
initial_cash = 10000.0
results_dir = "results"

[portfolio]
enabled = true
allocation_method = "equal"
total_capital = 10000.0

[strategies]
active = []
available = []
""".lstrip(),
    )

    p = _run_cli(["--timeframe", "2h", "--dry-run"], env={"PEAK_TRADE_CONFIG": str(cfg)})
    assert p.returncode != 0
    combined = (p.stdout + "\n" + p.stderr).lower()
    # argparse wording is stable enough for contract intent ("invalid choice")
    assert "invalid choice" in combined or "ungültig" in combined


def test_regime_any_means_no_filter(tmp_path: Path) -> None:
    cfg = tmp_path / "config.toml"
    _write_toml(
        cfg,
        """
[backtest]
initial_cash = 10000.0
results_dir = "results"

[portfolio]
enabled = true
allocation_method = "equal"
total_capital = 10000.0
max_strategies_active = 10

[strategies]
active = ["s1"]
available = ["s1", "s2"]

[strategy.s1]
foo = 1

[strategy.s2]
foo = 2

[strategies.metadata.s1]
best_market_regime = "trending"

[strategies.metadata.s2]
best_market_regime = "ranging"
""".lstrip(),
    )

    env = {"PEAK_TRADE_CONFIG": str(cfg)}

    p_default = _run_cli(["--dry-run"], env=env)
    assert p_default.returncode == 0
    default_list = _parse_strategy_list(p_default.stdout)
    assert default_list == ["s1"]

    p_any = _run_cli(["--dry-run", "--regime", "any"], env=env)
    assert p_any.returncode == 0
    any_list = _parse_strategy_list(p_any.stdout)

    # Contract: "any" means no regime filter -> all *available* strategies.
    assert any_list == ["s1", "s2"]


def test_portfolio_profile_overrides_applied(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cfg_path = tmp_path / "config.toml"
    _write_toml(
        cfg_path,
        """
[backtest]
initial_cash = 10000.0
results_dir = "results"

[portfolio]
enabled = true
allocation_method = "equal"
total_capital = 10000.0
max_strategies_active = 10

[portfolio.weights]
s1 = 0.5
s2 = 0.5

[portfolio.aggressive]
allocation_method = "manual"
total_capital = 20000.0

[portfolio.aggressive.weights]
s1 = 0.8
s2 = 0.2

[strategies]
active = ["s1", "s2"]
available = ["s1", "s2"]

[strategy.s1]
foo = 1

[strategy.s2]
foo = 2
""".lstrip(),
    )

    monkeypatch.setenv("PEAK_TRADE_CONFIG", str(cfg_path))
    from src.core import config_registry as cr

    cr.reset_config()
    cfg = cr.get_config()

    from src.backtest import engine as bt_engine

    # Avoid strategy loading/backtesting: return deterministic dummy results.
    seen_initial_capital: dict[str, float] = {}

    def _dummy_run_single(*, df: pd.DataFrame, strategy_name: str, **_kwargs):
        # run_portfolio_from_config temporarily overwrites cfg["backtest"]["initial_cash"] per strategy.
        initial_capital = float(cfg["backtest"]["initial_cash"])
        seen_initial_capital[strategy_name] = initial_capital
        return bt_engine._create_dummy_result(strategy_name, df, initial_capital=initial_capital)

    monkeypatch.setattr(
        bt_engine, "run_single_strategy_from_registry", _dummy_run_single, raising=True
    )

    idx = pd.date_range("2025-01-01", periods=5, freq="h")
    df = pd.DataFrame(
        {
            "open": [1, 1, 1, 1, 1],
            "high": [1, 1, 1, 1, 1],
            "low": [1, 1, 1, 1, 1],
            "close": [1, 1, 1, 1, 1],
            "volume": [1, 1, 1, 1, 1],
        },
        index=idx,
    )

    result = bt_engine.run_portfolio_from_config(
        df=df,
        cfg=cfg,
        portfolio_name="aggressive",
        strategy_filter=["s1", "s2"],
    )

    assert result.portfolio_stats["allocation_method"] == "manual"
    assert result.allocation["s1"] == pytest.approx(0.8)
    assert result.allocation["s2"] == pytest.approx(0.2)
    # total_capital override should drive per-strategy allocated initial cash
    assert seen_initial_capital["s1"] == pytest.approx(16000.0)
    assert seen_initial_capital["s2"] == pytest.approx(4000.0)


def test_config_path_default_and_fallback(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Contract:
    - Default config is <repo>/config/config.toml
    - Fallback is <repo>/config.toml
    - Robust against different CWD (path resolution anchored at project root)

    This test monkeypatches the module-level project root constants so it does not
    depend on the developer machine's repo files.
    """
    fake_root = tmp_path / "fake_repo_root"
    (fake_root / "config").mkdir(parents=True, exist_ok=True)

    from src.core import config_registry as cr

    monkeypatch.delenv("PEAK_TRADE_CONFIG", raising=False)
    monkeypatch.setattr(cr, "_PROJECT_ROOT", fake_root, raising=False)
    monkeypatch.setattr(
        cr, "DEFAULT_CONFIG_PATH", fake_root / "config" / "config.toml", raising=False
    )
    monkeypatch.setattr(cr, "FALLBACK_CONFIG_PATH", fake_root / "config.toml", raising=False)

    # Default path wins
    _write_toml(
        fake_root / "config" / "config.toml",
        """
[sentinel]
value = 1

[strategies]
active = []
available = []
""".lstrip(),
    )
    cr.reset_config()
    cfg = cr.get_config()
    assert cfg["sentinel"]["value"] == 1

    # Fallback used when default missing
    (fake_root / "config" / "config.toml").unlink()
    _write_toml(
        fake_root / "config.toml",
        """
[sentinel]
value = 2

[strategies]
active = []
available = []
""".lstrip(),
    )
    cr.reset_config()
    cfg2 = cr.get_config()
    assert cfg2["sentinel"]["value"] == 2


def test_config_resolution_logs_choice(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Contract: config_registry logs which resolution path was used.
    """
    fake_root = tmp_path / "fake_repo_root"
    (fake_root / "config").mkdir(parents=True, exist_ok=True)

    from src.core import config_registry as cr

    monkeypatch.delenv("PEAK_TRADE_CONFIG", raising=False)
    monkeypatch.setattr(cr, "_PROJECT_ROOT", fake_root, raising=False)
    monkeypatch.setattr(
        cr, "DEFAULT_CONFIG_PATH", fake_root / "config" / "config.toml", raising=False
    )
    monkeypatch.setattr(cr, "FALLBACK_CONFIG_PATH", fake_root / "config.toml", raising=False)

    # Exercise fallback logging
    _write_toml(
        fake_root / "config.toml",
        """
[sentinel]
value = "fallback"

[strategies]
active = []
available = []
""".lstrip(),
    )

    caplog.set_level("INFO")
    cr.reset_config()
    _ = cr.get_config()

    assert any(
        "ConfigRegistry: default missing, using fallback config path" in r.message
        for r in caplog.records
    )


def test_strategies_available_sanity_warnings(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """
    Contract: sanity warnings are emitted, but no hard errors.
    """
    cfg_path = tmp_path / "config.toml"
    _write_toml(
        cfg_path,
        """
[backtest]
initial_cash = 10000.0
results_dir = "results"

[strategies]
active = []
available = ["known", "unknown"]

[strategy.known]
foo = 1
""".lstrip(),
    )

    from src.core.config_registry import ConfigRegistry

    caplog.set_level("WARNING")
    reg = ConfigRegistry(config_path=cfg_path)
    _ = reg.config

    assert any(
        "strategies.available contains ids without [strategy.<id>] blocks" in r.message
        for r in caplog.records
    )
