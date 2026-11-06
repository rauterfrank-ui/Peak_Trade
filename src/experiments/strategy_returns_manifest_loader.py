from __future__ import annotations

import difflib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
import toml

from src.experiments.equity_loader import equity_to_returns, load_equity_curves_from_run_dir


class StrategyReturnsManifestError(RuntimeError):
    pass


@dataclass(frozen=True)
class StrategyReturnsSource:
    strategy_id: str
    run_dir: Path


def _load_manifest(manifest_path: Path) -> dict[str, Any]:
    if not manifest_path.exists():
        raise StrategyReturnsManifestError(f"manifest_not_found: {manifest_path}")
    try:
        data = toml.loads(manifest_path.read_text(encoding="utf-8"))
    except toml.TomlDecodeError as e:
        raise StrategyReturnsManifestError(f"manifest_invalid: toml_parse_failed: {e}") from e
    if not isinstance(data, dict):
        raise StrategyReturnsManifestError("manifest_invalid: top_level_not_dict")
    return data


def _extract_mapping(data: dict[str, Any]) -> dict[str, str]:
    mapping = data.get("strategy_returns")
    if not isinstance(mapping, dict):
        raise StrategyReturnsManifestError("manifest_invalid: missing [strategy_returns] table")
    out: dict[str, str] = {}
    for key, value in mapping.items():
        if not isinstance(key, str) or not isinstance(value, str):
            raise StrategyReturnsManifestError(
                "manifest_invalid: strategy_returns entries must be str->str"
            )
        out[key] = value
    return out


def _missing_strategy_id_message(strategy_id: str, mapping: dict[str, str]) -> str:
    """Error line for unknown strategy_id; may append close manifest keys (sorted, bounded)."""
    base = f"strategy_id_missing_in_manifest: {strategy_id}"
    keys = sorted(mapping.keys())
    if not keys:
        return base
    close = difflib.get_close_matches(strategy_id, keys, n=3, cutoff=0.55)
    if not close:
        return base
    return base + " candidate_strategy_ids=" + ",".join(close)


def resolve_strategy_run_dir(
    *,
    strategy_id: str,
    manifest_path: str | Path,
    base_dir: str | Path | None = None,
) -> StrategyReturnsSource:
    manifest_path = Path(manifest_path)
    data = _load_manifest(manifest_path)
    mapping = _extract_mapping(data)

    if strategy_id not in mapping:
        raise StrategyReturnsManifestError(_missing_strategy_id_message(strategy_id, mapping))

    raw_path = Path(mapping[strategy_id])
    if raw_path.is_absolute():
        run_dir = raw_path
    else:
        anchor = Path(base_dir) if base_dir is not None else manifest_path.parent
        run_dir = (anchor / raw_path).resolve()

    if not run_dir.exists():
        raise StrategyReturnsManifestError(f"run_dir_not_found: {strategy_id}: {run_dir}")
    if not run_dir.is_dir():
        raise StrategyReturnsManifestError(f"run_dir_not_directory: {strategy_id}: {run_dir}")

    return StrategyReturnsSource(strategy_id=strategy_id, run_dir=run_dir)


def load_returns_for_strategy_from_manifest(
    *,
    strategy_id: str,
    manifest_path: str | Path,
    base_dir: str | Path | None = None,
) -> pd.Series:
    source = resolve_strategy_run_dir(
        strategy_id=strategy_id,
        manifest_path=manifest_path,
        base_dir=base_dir,
    )

    try:
        curves = load_equity_curves_from_run_dir(source.run_dir, max_curves=1)
    except (FileNotFoundError, ValueError) as e:
        raise StrategyReturnsManifestError(
            f"equity_load_failed: {strategy_id}: {source.run_dir}: {e}"
        ) from e

    try:
        return equity_to_returns(curves[0])
    except ValueError as e:
        raise StrategyReturnsManifestError(
            f"returns_derive_failed: {strategy_id}: {source.run_dir}: {e}"
        ) from e
