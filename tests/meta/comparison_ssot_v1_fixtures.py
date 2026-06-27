"""Shared fixtures for comparison_ssot_v1 tests."""

from __future__ import annotations

import shutil
import uuid
from pathlib import Path

import pytest

from src.meta.learning_loop.comparison_metric_input_v1.producer import (
    produce_comparison_metric_input_v1,
)
from src.meta.learning_loop.comparison_ssot_v1.producer import produce_comparison_offline_v1
from tests.meta.comparison_metric_input_v1_fixtures import build_backtest_run_dir

REPO_ROOT = Path(__file__).resolve().parents[2]
_DURABLE_OUTPUT_ROOT = REPO_ROOT / ".comparison_ssot_pytest_outputs"


@pytest.fixture(autouse=True)
def _allow_tmp_output(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_ssot_v1.io.is_under_tmp",
        lambda _path: False,
    )
    monkeypatch.setattr(
        "src.meta.learning_loop.comparison_metric_input_v1.io.is_under_tmp",
        lambda _path: False,
    )


@pytest.fixture
def ssot_durable_output_dir() -> Path:
    _DURABLE_OUTPUT_ROOT.mkdir(exist_ok=True)
    path = _DURABLE_OUTPUT_ROOT / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    yield path
    if path.exists():
        shutil.rmtree(path, ignore_errors=True)
    for staging in _DURABLE_OUTPUT_ROOT.glob(".comparison_ssot_staging_*"):
        shutil.rmtree(staging, ignore_errors=True)


def produce_backtest_metric_input(
    tmp_path: Path,
    durable_root: Path,
    *,
    run_id: str,
    timeframe: str = "1d",
    end_date: str = "2025-01-20",
) -> Path:
    run_dir, ref = build_backtest_run_dir(tmp_path, run_id=run_id)
    if timeframe != "1d" or end_date != "2025-01-20":
        import json

        from src.governance.promotion_loop.backtest_lineage_ref_producer_v1 import (
            build_backtest_lineage_ref_from_run_summary,
        )
        from src.governance.promotion_loop.candidate_lineage_manifest_v1 import (
            lineage_ref_to_mapping,
        )
        from tests.meta.comparison_metric_input_v1_fixtures import (
            comparison_source_ref,
            write_run_summary,
        )

        config = json.loads((run_dir / "config_snapshot.json").read_text(encoding="utf-8"))
        config["params"]["timeframe"] = timeframe
        (run_dir / "config_snapshot.json").write_text(json.dumps(config), encoding="utf-8")
        summary = write_run_summary(run_dir, run_id=run_id)
        summary.params["timeframe"] = timeframe
        summary.finished_at_utc = f"{end_date}T10:00:00+00:00"
        summary.write_json(run_dir / "run_summary.json")
        ref = comparison_source_ref(
            lineage_ref_to_mapping(build_backtest_lineage_ref_from_run_summary(summary))
        )
    result = produce_comparison_metric_input_v1(
        source_domain="BACKTEST",
        output_root=durable_root,
        source_ref=ref,
        run_dir=run_dir,
    )
    return result.manifest_path


def produce_two_compatible_backtest_inputs(
    tmp_path: Path,
    durable_root: Path,
) -> tuple[Path, Path]:
    first = produce_backtest_metric_input(tmp_path, durable_root, run_id="cmp-ssot-run-a")
    second = produce_backtest_metric_input(tmp_path, durable_root, run_id="cmp-ssot-run-b")
    return first, second


def produce_comparison_pair(
    tmp_path: Path,
    durable_root: Path,
    *,
    ranking_rule_version: str = "NONE_V1",
) -> tuple[Path, Path, str]:
    metric_root = durable_root / "metric_inputs"
    metric_root.mkdir(exist_ok=True)
    first, second = produce_two_compatible_backtest_inputs(tmp_path, metric_root)
    comparison_root = durable_root / "comparisons"
    comparison_root.mkdir(exist_ok=True)
    result = produce_comparison_offline_v1(
        input_manifest_paths=[first, second],
        output_root=comparison_root,
        ranking_rule_version=ranking_rule_version,
    )
    return result.definition_path, result.result_path, result.comparison_definition_id
