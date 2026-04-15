from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest

from src.experiments.strategy_returns_manifest_loader import (
    StrategyReturnsManifestError,
    load_returns_for_strategy_from_manifest,
    resolve_strategy_run_dir,
)


def _write_manifest(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _write_run_equity_csv(run_dir: Path) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(
        {
            "timestamp": [
                "2026-01-01T00:00:00Z",
                "2026-01-02T00:00:00Z",
                "2026-01-03T00:00:00Z",
            ],
            "equity": [100.0, 101.0, 103.0],
        }
    )
    # equity_loader accepts *equity.csv
    df.to_csv(run_dir / "phase53_equity.csv", index=False)


def test_resolve_strategy_run_dir_success(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "strategy_a"
    run_dir.mkdir(parents=True)

    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
[strategy_returns]
strategy_a = "runs/strategy_a"
""".strip()
        + "\n",
    )

    source = resolve_strategy_run_dir(strategy_id="strategy_a", manifest_path=manifest)
    assert source.strategy_id == "strategy_a"
    assert source.run_dir == run_dir.resolve()


def test_load_returns_for_strategy_from_manifest_success(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "strategy_a"
    _write_run_equity_csv(run_dir)

    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
[strategy_returns]
strategy_a = "runs/strategy_a"
""".strip()
        + "\n",
    )

    returns = load_returns_for_strategy_from_manifest(
        strategy_id="strategy_a",
        manifest_path=manifest,
    )

    assert isinstance(returns, pd.Series)
    assert len(returns) == 2
    assert returns.notna().all()


def test_load_returns_for_strategy_from_manifest_missing_strategy_id(tmp_path: Path) -> None:
    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
[strategy_returns]
strategy_a = "runs/strategy_a"
""".strip()
        + "\n",
    )

    with pytest.raises(StrategyReturnsManifestError, match="strategy_id_missing_in_manifest"):
        load_returns_for_strategy_from_manifest(
            strategy_id="strategy_b",
            manifest_path=manifest,
        )
