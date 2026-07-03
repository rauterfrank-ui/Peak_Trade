"""Contract tests for funding-rate delta momentum full offline economic evaluation runner v0."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0 import (
    ALLOWED_EVALUATION_STAGES,
    AUTHORITY_EFFECT,
    EconomicClassification,
    ExecutionTerminalStatus,
    FIXTURE_DATA_DIGEST,
    GO_TOKEN,
    RUNTIME_EFFECT,
    execution_result_to_dict,
    run_full_offline_economic_evaluation_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_scope_ratification_v0 import (
    materialize_funding_delta_momentum_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_funding_rate_delta_momentum_v0_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)
from tests.research.fixtures.cross_sectional_funding_rate_delta_momentum_v0.fixture_builder import (
    build_synthetic_ohlcv_panel_v0,
)
from tests.research.test_cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_infrastructure_v0 import (  # noqa: E501
    _write_staging_with_funding,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_research_binding_v0()


@pytest.fixture(name="scope_ratification")
def fixture_scope_ratification(complete_binding: dict) -> dict:
    return materialize_funding_delta_momentum_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


@pytest.fixture(name="bound_staging")
def fixture_bound_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_funding_delta_full_runner_v0_"))
    return _write_staging_with_funding(tmp)


def test_full_runner_go_token_constants() -> None:
    assert GO_TOKEN == (
        "GO_BOUNDED_CROSS_SECTIONAL_FUNDING_RATE_DELTA_MOMENTUM_V0_OFFLINE_ECONOMIC_EVALUATION_SCOPE_V0"
    )


def test_fixture_digest_constant_present() -> None:
    assert len(FIXTURE_DATA_DIGEST) == 64


def test_allowed_evaluation_stage_order() -> None:
    assert ALLOWED_EVALUATION_STAGES == (
        "OFFLINE_BACKTEST",
        "WALK_FORWARD",
        "MONTE_CARLO",
        "STRESS",
        "PARAMETER_SENSITIVITY",
        "ECONOMIC_VIABILITY_EVIDENCE_MATERIALIZATION",
    )


def test_full_runner_executes_six_stages_with_scope_go_token(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    panel = build_synthetic_ohlcv_panel_v0()
    result = run_full_offline_economic_evaluation_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
    )
    assert result.economic_evaluation_executed is True
    assert result.status is ExecutionTerminalStatus.ECONOMIC_EVALUATION_COMPLETE
    assert result.economic_classification in {
        EconomicClassification.PASS,
        EconomicClassification.FAIL,
        EconomicClassification.INCONCLUSIVE,
    }
    assert result.authority_effect == AUTHORITY_EFFECT == "NONE"
    assert result.runtime_effect == RUNTIME_EFFECT == "NONE"
    assert result.panel_data_digest != FIXTURE_DATA_DIGEST
    assert len(result.stage_wiring) == 6
    assert all(item.wired for item in result.stage_wiring)
    stage_names = tuple(item.stage_name for item in result.stage_wiring)
    assert stage_names == ALLOWED_EVALUATION_STAGES
    assert "net_return" in result.economic_viability_evidence


def test_full_runner_fail_closed_on_fixture_digest(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    from src.research.cross_sectional_funding_rate_delta_momentum_v0_bound_panel_dataset_materialization_v0 import (
        materialize_bound_funding_panel_dataset_v0,
    )

    materialization = materialize_bound_funding_panel_dataset_v0(
        bound_staging,
        period_binding=complete_binding["period_binding"],
        expected_data_digest=complete_binding["data_digest"],
    )
    if materialization.panel_data_digest != FIXTURE_DATA_DIGEST:
        pytest.skip("staging_digest_not_fixture_contract_digest")
    panel = build_synthetic_ohlcv_panel_v0()
    result = run_full_offline_economic_evaluation_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
    )
    assert result.status is ExecutionTerminalStatus.FAIL_CLOSED_FIXTURE_LEAKAGE
    assert result.economic_evaluation_executed is False


def test_full_runner_rejects_invalid_go_token(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    panel = build_synthetic_ohlcv_panel_v0()
    result = run_full_offline_economic_evaluation_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token="INVALID_GO_TOKEN",
    )
    assert result.status is ExecutionTerminalStatus.FAIL_CLOSED_PRECHECK
    assert result.economic_evaluation_executed is False


def test_execution_result_to_dict_preserves_stage_wiring_and_no_runtime_effect(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    panel = build_synthetic_ohlcv_panel_v0()
    result = run_full_offline_economic_evaluation_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
    )
    payload = execution_result_to_dict(result)
    assert payload["authority_effect"] == "NONE"
    assert payload["runtime_effect"] == "NONE"
    assert payload["allowed_evaluation_stages"] == list(ALLOWED_EVALUATION_STAGES)
    assert len(payload["stage_wiring"]) == 6
    assert [item["stage_name"] for item in payload["stage_wiring"]] == list(
        ALLOWED_EVALUATION_STAGES
    )


def test_ops_runner_module_has_no_runtime_imports() -> None:
    module_path = (
        REPO_ROOT
        / "scripts/ops/run_cross_sectional_funding_rate_delta_momentum_v0_offline_economic_evaluation_execution_v0.py"
    )
    source = module_path.read_text(encoding="utf-8")
    for token in ("src.execution", "src.governance.live", "src.scheduler"):
        assert token not in source
