"""Contract tests for cross-sectional offline economic evaluation execution v2."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.research.cross_sectional_panel_staging_source_manifest_v1 import (
    SourceManifestStatus,
    materialize_panel_staging_source_manifests_v1,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v0 import (
    EXECUTION_V2_GO_TOKEN,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_execution_v2 import (
    EconomicClassification,
    ExecutionV2TerminalStatus,
    FIXTURE_DATA_DIGEST,
    GO_TOKEN,
    run_full_offline_economic_evaluation_v2,
)
from src.research.cross_sectional_relative_strength_v0_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_relative_strength_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.staging_builder import (
    write_bound_period_staging_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_research_binding_v0()


@pytest.fixture(name="scope_ratification")
def fixture_scope_ratification(complete_binding: dict) -> dict:
    return materialize_cross_sectional_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


@pytest.fixture(name="bound_staging")
def fixture_bound_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_rs_exec_v2_staging_"))
    staging = write_bound_period_staging_v0(tmp)
    lifecycle = staging / "lifecycle"
    lifecycle.mkdir(parents=True, exist_ok=True)
    (lifecycle / "SOURCE_REGISTRATION.json").write_text(
        json.dumps(
            {
                "source_snapshot_ref": "test:fixture",
                "source_snapshot_digest": "b" * 64,
                "registered": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    manifest_result = materialize_panel_staging_source_manifests_v1(staging)
    assert manifest_result.status is SourceManifestStatus.VERIFIED
    return staging


def test_execution_v2_go_token_constants() -> None:
    assert GO_TOKEN == EXECUTION_V2_GO_TOKEN
    assert GO_TOKEN == (
        "GO_BOUNDED_CROSS_SECTIONAL_RELATIVE_STRENGTH_V0_OFFLINE_ECONOMIC_EVALUATION_EXECUTION_V2"
    )


def test_fixture_digest_constant_present() -> None:
    assert len(FIXTURE_DATA_DIGEST) == 64


def test_execution_v2_runs_with_bound_staging(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    tmp = Path(tempfile.mkdtemp(prefix="cs_rs_exec_v2_non_fixture_"))
    panel = build_synthetic_panel_series_v0(bar_count=31, end="2024-06-01T02:00:00Z")
    staging = write_bound_period_staging_v0(tmp, panel_series=panel)
    lifecycle = staging / "lifecycle"
    lifecycle.mkdir(parents=True, exist_ok=True)
    (lifecycle / "SOURCE_REGISTRATION.json").write_text(
        json.dumps(
            {
                "source_snapshot_ref": "test:non_fixture",
                "source_snapshot_digest": "c" * 64,
                "registered": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    materialize_panel_staging_source_manifests_v1(staging)
    result = run_full_offline_economic_evaluation_v2(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
    )
    assert result.economic_evaluation_executed is True
    assert result.status is ExecutionV2TerminalStatus.ECONOMIC_EVALUATION_COMPLETE
    assert result.economic_classification in {
        EconomicClassification.PASS,
        EconomicClassification.FAIL,
        EconomicClassification.INCONCLUSIVE,
    }
    assert result.authority_effect == "NONE"
    assert result.runtime_effect == "NONE"
    assert result.panel_data_digest != FIXTURE_DATA_DIGEST
    assert "net_return" in result.economic_viability_evidence


def test_execution_v2_fail_closed_on_fixture_digest(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    from src.research.cross_sectional_relative_strength_v0_bound_panel_dataset_materialization_v0 import (
        materialize_bound_panel_dataset_v0,
    )

    materialization = materialize_bound_panel_dataset_v0(
        bound_staging,
        period_binding=complete_binding["period_binding"],
    )
    if materialization.panel_data_digest != FIXTURE_DATA_DIGEST:
        pytest.skip("staging_digest_not_fixture_contract_digest")
    panel = build_synthetic_panel_series_v0()
    result = run_full_offline_economic_evaluation_v2(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
    )
    assert result.status is ExecutionV2TerminalStatus.FAIL_CLOSED_FIXTURE_LEAKAGE
    assert result.economic_evaluation_executed is False


def test_execution_v2_rejects_invalid_go_token(
    bound_staging: Path,
    scope_ratification: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    result = run_full_offline_economic_evaluation_v2(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        go_token="INVALID_GO_TOKEN",
    )
    assert result.status is ExecutionV2TerminalStatus.FAIL_CLOSED_PRECHECK
    assert result.economic_evaluation_executed is False
