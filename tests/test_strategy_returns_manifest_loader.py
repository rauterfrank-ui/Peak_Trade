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


def test_missing_strategy_id_suggests_close_manifest_keys(tmp_path: Path) -> None:
    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
[strategy_returns]
strategy_a = "runs/strategy_a"
strategy_bb = "runs/strategy_bb"
""".strip()
        + "\n",
    )

    with pytest.raises(StrategyReturnsManifestError) as ei:
        resolve_strategy_run_dir(strategy_id="strategy_b", manifest_path=manifest)
    msg = str(ei.value)
    assert "strategy_id_missing_in_manifest: strategy_b" in msg
    assert "candidate_strategy_ids=" in msg
    assert "strategy_a" in msg


def test_missing_strategy_id_no_candidates_when_no_close_match(tmp_path: Path) -> None:
    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
[strategy_returns]
alpha = "runs/a"
beta = "runs/b"
gamma = "runs/g"
""".strip()
        + "\n",
    )

    with pytest.raises(StrategyReturnsManifestError) as ei:
        resolve_strategy_run_dir(strategy_id="zzzzzzzz", manifest_path=manifest)
    msg = str(ei.value)
    assert msg.startswith("strategy_id_missing_in_manifest: zzzzzzzz")
    assert "candidate_strategy_ids=" not in msg


def test_missing_strategy_id_empty_mapping_no_candidates(tmp_path: Path) -> None:
    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
[strategy_returns]
""".strip()
        + "\n",
    )

    with pytest.raises(StrategyReturnsManifestError) as ei:
        resolve_strategy_run_dir(strategy_id="any", manifest_path=manifest)
    msg = str(ei.value)
    assert "strategy_id_missing_in_manifest: any" in msg
    assert "candidate_strategy_ids=" not in msg


def test_load_returns_for_strategy_from_manifest_missing_manifest(tmp_path: Path) -> None:
    manifest = tmp_path / "missing_strategy_returns_map.toml"

    with pytest.raises(StrategyReturnsManifestError, match="manifest_not_found"):
        load_returns_for_strategy_from_manifest(
            strategy_id="strategy_a",
            manifest_path=manifest,
        )


def test_load_returns_for_strategy_from_manifest_missing_run_dir(tmp_path: Path) -> None:
    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
[strategy_returns]
strategy_a = "runs/strategy_a"
""".strip()
        + "\n",
    )

    with pytest.raises(StrategyReturnsManifestError, match="run_dir_not_found"):
        load_returns_for_strategy_from_manifest(
            strategy_id="strategy_a",
            manifest_path=manifest,
        )


def test_load_returns_for_strategy_from_manifest_missing_equity_file(tmp_path: Path) -> None:
    run_dir = tmp_path / "runs" / "strategy_a"
    run_dir.mkdir(parents=True, exist_ok=True)

    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
[strategy_returns]
strategy_a = "runs/strategy_a"
""".strip()
        + "\n",
    )

    with pytest.raises(StrategyReturnsManifestError, match="equity_load_failed"):
        load_returns_for_strategy_from_manifest(
            strategy_id="strategy_a",
            manifest_path=manifest,
        )


def test_resolve_strategy_run_dir_missing_strategy_returns_table(tmp_path: Path) -> None:
    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
[other]
foo = "bar"
""".strip()
        + "\n",
    )

    with pytest.raises(StrategyReturnsManifestError, match="manifest_invalid: missing"):
        resolve_strategy_run_dir(strategy_id="strategy_a", manifest_path=manifest)


def test_resolve_strategy_run_dir_strategy_returns_not_a_table(tmp_path: Path) -> None:
    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
strategy_returns = "not_a_table"
""".strip()
        + "\n",
    )

    with pytest.raises(StrategyReturnsManifestError, match="manifest_invalid: missing"):
        resolve_strategy_run_dir(strategy_id="strategy_a", manifest_path=manifest)


def test_resolve_strategy_run_dir_non_str_mapping_entries(tmp_path: Path) -> None:
    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
[strategy_returns]
strategy_a = 123
""".strip()
        + "\n",
    )

    with pytest.raises(
        StrategyReturnsManifestError,
        match="manifest_invalid: strategy_returns entries must be str->str",
    ):
        resolve_strategy_run_dir(strategy_id="strategy_a", manifest_path=manifest)


def test_resolve_strategy_run_dir_run_path_is_file(tmp_path: Path) -> None:
    fake_run = tmp_path / "runs" / "strategy_a"
    fake_run.parent.mkdir(parents=True, exist_ok=True)
    fake_run.write_text("not_a_directory", encoding="utf-8")

    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
[strategy_returns]
strategy_a = "runs/strategy_a"
""".strip()
        + "\n",
    )

    with pytest.raises(StrategyReturnsManifestError, match="run_dir_not_directory"):
        resolve_strategy_run_dir(strategy_id="strategy_a", manifest_path=manifest)


def test_resolve_strategy_run_dir_invalid_toml(tmp_path: Path) -> None:
    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(manifest, "[not closed\n")

    with pytest.raises(StrategyReturnsManifestError, match="manifest_invalid: toml_parse_failed"):
        resolve_strategy_run_dir(strategy_id="strategy_a", manifest_path=manifest)


def test_resolve_strategy_run_dir_relative_uses_base_dir_not_manifest_parent(
    tmp_path: Path,
) -> None:
    """Relative paths join to base_dir when given; manifest directory is not the anchor."""
    base_dir = tmp_path / "project_root"
    run_dir = base_dir / "artifacts" / "strategy_a"
    run_dir.mkdir(parents=True)

    manifest = tmp_path / "unrelated" / "nested" / "map.toml"
    manifest.parent.mkdir(parents=True)
    _write_manifest(
        manifest,
        """
[strategy_returns]
strategy_a = "artifacts/strategy_a"
""".strip()
        + "\n",
    )

    source = resolve_strategy_run_dir(
        strategy_id="strategy_a",
        manifest_path=manifest,
        base_dir=base_dir,
    )
    assert source.strategy_id == "strategy_a"
    assert source.run_dir == run_dir.resolve()


def test_resolve_strategy_run_dir_absolute_path_ignores_base_dir(tmp_path: Path) -> None:
    """Absolute manifest entries resolve to that path; base_dir must not affect resolution."""
    run_dir = tmp_path / "storage" / "run_a"
    run_dir.mkdir(parents=True)
    abs_run = run_dir.resolve().as_posix()

    manifest = tmp_path / "configs" / "returns.toml"
    manifest.parent.mkdir(parents=True)
    _write_manifest(
        manifest,
        f"""
[strategy_returns]
strategy_a = "{abs_run}"
""".strip()
        + "\n",
    )

    wrong_base = tmp_path / "wrong_root"
    wrong_base.mkdir(parents=True)

    source = resolve_strategy_run_dir(
        strategy_id="strategy_a",
        manifest_path=manifest,
        base_dir=wrong_base,
    )
    assert source.run_dir == run_dir.resolve()


def test_load_returns_for_strategy_from_manifest_respects_base_dir(tmp_path: Path) -> None:
    base_dir = tmp_path / "data"
    run_dir = base_dir / "runs" / "s1"
    _write_run_equity_csv(run_dir)

    manifest = tmp_path / "meta" / "map.toml"
    manifest.parent.mkdir(parents=True)
    _write_manifest(
        manifest,
        """
[strategy_returns]
s1 = "runs/s1"
""".strip()
        + "\n",
    )

    returns = load_returns_for_strategy_from_manifest(
        strategy_id="s1",
        manifest_path=manifest,
        base_dir=base_dir,
    )
    assert isinstance(returns, pd.Series)
    assert len(returns) == 2
    assert returns.notna().all()


def test_load_returns_for_strategy_from_manifest_returns_derive_failed_when_equity_flat_zero(
    tmp_path: Path,
) -> None:
    """All-zero equity loads (>=3 rows) but pct_change yields no usable returns."""
    run_dir = tmp_path / "runs" / "strategy_a"
    run_dir.mkdir(parents=True)
    df = pd.DataFrame(
        {
            "timestamp": [
                "2026-01-01T00:00:00Z",
                "2026-01-02T00:00:00Z",
                "2026-01-03T00:00:00Z",
            ],
            "equity": [0.0, 0.0, 0.0],
        }
    )
    df.to_csv(run_dir / "phase53_equity.csv", index=False)

    manifest = tmp_path / "strategy_returns_map.toml"
    _write_manifest(
        manifest,
        """
[strategy_returns]
strategy_a = "runs/strategy_a"
""".strip()
        + "\n",
    )

    with pytest.raises(StrategyReturnsManifestError, match="returns_derive_failed"):
        load_returns_for_strategy_from_manifest(
            strategy_id="strategy_a",
            manifest_path=manifest,
        )
