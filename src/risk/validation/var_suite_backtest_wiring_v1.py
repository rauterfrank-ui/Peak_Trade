"""
Package H — offline backtest returns to VaR suite report wiring v1.

Deterministic, fail-closed bridge from explicit backtest run artifacts to canonical
VaR suite evidence reports.  No trading, runtime, promotion, or VaR semantics.
"""

from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from src.experiments.equity_loader import equity_to_returns, load_equity_curves_from_run_dir
from src.experiments.strategy_returns_manifest_loader import (
    StrategyReturnsManifestError,
    load_returns_for_strategy_from_manifest,
)
from src.risk.validation.report_formatter import (
    format_suite_result_json,
    format_suite_result_markdown,
)
from src.risk.validation.suite_runner import VaRBacktestSuiteResult
from src.risk.validation.var_suite_adapter import run_rolling_historical_var_backtest_suite

SUITE_REPORT_JSON = "suite_report.json"
SUITE_REPORT_MD = "suite_report.md"
STAGING_DIRNAME_PREFIX = ".var_suite_backtest_wiring_staging_"
DEFAULT_ROLLING_WINDOW = 5


class VarSuiteBacktestWiringError(ValueError):
    """Fail-closed Package H backtest→VaR suite wiring error."""


@dataclass(frozen=True)
class BacktestVarSuiteWiringResult:
    """Published offline VaR suite evidence bundle."""

    output_dir: Path
    suite_result: VaRBacktestSuiteResult


def load_returns_from_run_dir(run_dir: Path | str) -> pd.Series:
    """Load canonical returns from an explicit backtest run directory."""
    path = Path(run_dir)
    if not path.exists():
        raise VarSuiteBacktestWiringError(f"run_dir not found: {path}")
    if not path.is_dir():
        raise VarSuiteBacktestWiringError(f"run_dir is not a directory: {path}")
    try:
        curves = load_equity_curves_from_run_dir(path, max_curves=1)
    except (FileNotFoundError, ValueError) as exc:
        raise VarSuiteBacktestWiringError(f"equity load failed for run_dir={path}: {exc}") from exc
    try:
        return equity_to_returns(curves[0])
    except ValueError as exc:
        raise VarSuiteBacktestWiringError(
            f"returns derivation failed for run_dir={path}: {exc}"
        ) from exc


def resolve_backtest_returns(
    *,
    run_dir: Path | str | None,
    strategy_returns_manifest: Path | str | None,
    strategy_id: str | None,
    manifest_base_dir: Path | str | None = None,
) -> pd.Series:
    """Resolve returns from exactly one explicit offline input source."""
    has_run_dir = run_dir is not None
    has_manifest_path = strategy_returns_manifest is not None
    has_strategy_id = strategy_id is not None

    if has_manifest_path and not has_strategy_id:
        raise VarSuiteBacktestWiringError("strategy_id required with strategy_returns_manifest")
    if has_strategy_id and not has_manifest_path:
        raise VarSuiteBacktestWiringError("strategy_returns_manifest required with strategy_id")
    if has_run_dir and (has_manifest_path or has_strategy_id):
        raise VarSuiteBacktestWiringError(
            "run_dir and strategy_returns_manifest inputs are mutually exclusive"
        )
    if not has_run_dir and not (has_manifest_path and has_strategy_id):
        raise VarSuiteBacktestWiringError(
            "exactly one input required: run_dir or (strategy_returns_manifest, strategy_id)"
        )

    if has_run_dir:
        return load_returns_from_run_dir(run_dir)

    try:
        return load_returns_for_strategy_from_manifest(
            strategy_id=str(strategy_id),
            manifest_path=Path(strategy_returns_manifest),
            base_dir=Path(manifest_base_dir) if manifest_base_dir is not None else None,
        )
    except StrategyReturnsManifestError as exc:
        raise VarSuiteBacktestWiringError(str(exc)) from exc


def _validate_output_target(output_dir: Path) -> None:
    if output_dir.exists():
        raise VarSuiteBacktestWiringError(f"output_dir already exists (fail-closed): {output_dir}")
    parent = output_dir.parent
    if not parent.is_dir():
        raise VarSuiteBacktestWiringError(f"output_dir parent missing: {parent}")


def _staging_dir_for(output_dir: Path) -> Path:
    token = uuid.uuid4().hex
    return output_dir.parent / f"{STAGING_DIRNAME_PREFIX}{token}"


def _cleanup_staging(staging: Path) -> None:
    if staging.exists():
        shutil.rmtree(staging)


def _validate_report_payloads(*, json_text: str, markdown_text: str) -> None:
    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise VarSuiteBacktestWiringError(f"suite_report.json is invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise VarSuiteBacktestWiringError("suite_report.json root must be a JSON object")
    if "overall_result" not in data:
        raise VarSuiteBacktestWiringError("suite_report.json missing overall_result")
    if not markdown_text.strip():
        raise VarSuiteBacktestWiringError("suite_report.md is empty")


def _assert_no_absolute_paths_in_reports(*, json_text: str, markdown_text: str) -> None:
    for label, text in (("suite_report.json", json_text), ("suite_report.md", markdown_text)):
        if "://" in text:
            raise VarSuiteBacktestWiringError(f"{label} must not contain URL-like absolute paths")
        if "/Users/" in text or "C:\\" in text or "\\\\" in text:
            raise VarSuiteBacktestWiringError(f"{label} must not contain host absolute paths")


def _atomic_publish_suite_reports(
    *,
    staging: Path,
    final_dir: Path,
    json_text: str,
    markdown_text: str,
) -> None:
    _validate_report_payloads(json_text=json_text, markdown_text=markdown_text)
    _assert_no_absolute_paths_in_reports(json_text=json_text, markdown_text=markdown_text)

    json_path = staging / SUITE_REPORT_JSON
    md_path = staging / SUITE_REPORT_MD
    json_path.write_text(json_text, encoding="utf-8")
    md_path.write_text(markdown_text, encoding="utf-8")

    reread_json = json_path.read_text(encoding="utf-8")
    reread_md = md_path.read_text(encoding="utf-8")
    if reread_json != json_text or reread_md != markdown_text:
        raise VarSuiteBacktestWiringError("report read-back verification failed before publish")

    staging.replace(final_dir)

    final_json = final_dir / SUITE_REPORT_JSON
    final_md = final_dir / SUITE_REPORT_MD
    if not final_json.is_file() or not final_md.is_file():
        raise VarSuiteBacktestWiringError("published suite reports missing after atomic rename")


def run_backtest_var_suite_wiring_v1(
    *,
    run_dir: Path | str | None = None,
    strategy_returns_manifest: Path | str | None = None,
    strategy_id: str | None = None,
    manifest_base_dir: Path | str | None = None,
    output_dir: Path | str,
    window: int = DEFAULT_ROLLING_WINDOW,
    confidence_level: float = 0.95,
    significance: float = 0.05,
) -> BacktestVarSuiteWiringResult:
    """
      Wire explicit offline backtest returns to canonical VaR suite evidence reports.

    Pure orchestration: loader → existing adapter → existing formatter → atomic publish.
    """
    final_dir = Path(output_dir)
    _validate_output_target(final_dir)

    returns = resolve_backtest_returns(
        run_dir=run_dir,
        strategy_returns_manifest=strategy_returns_manifest,
        strategy_id=strategy_id,
        manifest_base_dir=manifest_base_dir,
    )

    suite_result = run_rolling_historical_var_backtest_suite(
        returns,
        window=window,
        confidence_level=confidence_level,
        significance=significance,
    )

    json_text = format_suite_result_json(suite_result)
    markdown_text = format_suite_result_markdown(suite_result)

    staging = _staging_dir_for(final_dir)
    if staging.exists():
        raise VarSuiteBacktestWiringError(f"staging directory collision: {staging}")

    try:
        staging.mkdir(parents=True, exist_ok=False)
        _atomic_publish_suite_reports(
            staging=staging,
            final_dir=final_dir,
            json_text=json_text,
            markdown_text=markdown_text,
        )
    except Exception:
        _cleanup_staging(staging)
        if final_dir.exists():
            shutil.rmtree(final_dir)
        raise

    return BacktestVarSuiteWiringResult(output_dir=final_dir, suite_result=suite_result)


__all__ = [
    "DEFAULT_ROLLING_WINDOW",
    "BacktestVarSuiteWiringResult",
    "SUITE_REPORT_JSON",
    "SUITE_REPORT_MD",
    "VarSuiteBacktestWiringError",
    "load_returns_from_run_dir",
    "resolve_backtest_returns",
    "run_backtest_var_suite_wiring_v1",
]
