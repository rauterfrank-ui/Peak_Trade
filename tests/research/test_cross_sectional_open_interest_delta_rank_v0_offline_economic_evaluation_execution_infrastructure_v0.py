"""Contract tests for open-interest delta rank execution infrastructure v0."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.research.cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    GO_TOKEN,
    INFRASTRUCTURE_GO_TOKEN,
    RUNTIME_EFFECT,
    entrypoint_result_to_dict,
    load_ops_evaluation_config_v0,
    materialize_execution_contract_v0,
    materialize_infrastructure_summary_v0,
    run_contract_smoke_evaluation_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    verify_execution_start_state_v0,
    verify_full_evaluation_precheck_v1,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_offline_economic_evaluation_scope_ratification_v0 import (
    ValidationVerdictEnum,
    materialize_open_interest_delta_rank_offline_economic_evaluation_scope_ratification_v0,
    validate_open_interest_delta_rank_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (
    materialize_and_validate_versioned_research_binding_v0,
    materialize_versioned_research_binding_v0,
)
from tests.research.fixtures.cross_sectional_open_interest_delta_rank_v0.fixture_builder import (
    build_synthetic_ohlcv_panel_v0,
    write_oi_materialization_root_v0,
)
from src.research.cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0 import (
    RATIFIED_PANEL_DATASET_DIGEST,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_INFRA_GO = INFRASTRUCTURE_GO_TOKEN


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_research_binding_v0()


@pytest.fixture(name="scope_ratification")
def fixture_scope_ratification(complete_binding: dict) -> dict:
    return materialize_open_interest_delta_rank_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


@pytest.fixture(name="bound_materialization")
def fixture_bound_materialization() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_oi_delta_rank_exec_v0_"))
    write_oi_materialization_root_v0(tmp, panel_dataset_digest=RATIFIED_PANEL_DATASET_DIGEST)
    return tmp


def test_go_token_constants() -> None:
    assert GO_TOKEN == (
        "GO_CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_OFFLINE_ECONOMIC_EVALUATION_"
        "EXECUTION_NO_RUNTIME_AUTHORITY_V0"
    )
    assert INFRASTRUCTURE_GO_TOKEN == (
        "GO_CROSS_SECTIONAL_OPEN_INTEREST_DELTA_RANK_V0_OFFLINE_ECONOMIC_EVALUATION_"
        "EXECUTION_INFRASTRUCTURE_IMPLEMENTATION_V0"
    )


def test_no_runtime_authority_effect_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"


def test_binding_materialization_complete_accepted() -> None:
    result = materialize_and_validate_versioned_research_binding_v0()
    assert result.validation_verdict.value == "ACCEPTED_COMPLETE"


def test_futures_only_and_bitcoin_exclusion(complete_binding: dict) -> None:
    constraints = complete_binding["system_constraints"]
    assert constraints["futures_only"] is True
    assert constraints["bitcoin_direction_allowed"] is False


def test_bitcoin_direction_rejected_in_scope_ratification(complete_binding: dict) -> None:
    ratification = (
        materialize_open_interest_delta_rank_offline_economic_evaluation_scope_ratification_v0(
            repo_root=REPO_ROOT,
            versioned_binding=complete_binding,
        )
    )
    ratification["bitcoin_direction_allowed"] = True
    validation = (
        validate_open_interest_delta_rank_offline_economic_evaluation_scope_ratification_v0(
            ratification,
            expected_binding=complete_binding,
        )
    )
    assert validation.verdict is ValidationVerdictEnum.REJECTED
    assert "BITCOIN_DIRECTION_VIOLATION" in validation.fail_reasons


def test_start_state_verification_accepts_ratified_binding(
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    result = verify_execution_start_state_v0(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        versioned_binding=complete_binding,
    )
    assert result.valid is True
    assert result.fail_reasons == ()


def test_precheck_rejects_invalid_go_token(
    bound_materialization: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    ok, reasons, _ = verify_full_evaluation_precheck_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        materialization_root=bound_materialization,
        versioned_binding=complete_binding,
        go_token="INVALID_TOKEN",
    )
    assert ok is False
    assert "GO_TOKEN_INVALID" in reasons


def test_precheck_rejects_data_digest_mismatch(
    bound_materialization: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp)
        (repo / "config/ops").mkdir(parents=True, exist_ok=True)
        cfg = load_ops_evaluation_config_v0(REPO_ROOT)
        cfg["cross_sectional_evaluation_binding_v1"]["data_contract_digest"] = "f" * 64
        (
            repo
            / "config/ops/cross_sectional_open_interest_delta_rank_v0_economic_evaluation_v1.json"
        ).write_text(
            json.dumps(cfg, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        (repo / "config/research").mkdir(parents=True, exist_ok=True)
        (
            repo
            / "config/research/cross_sectional_open_interest_delta_rank_v0_versioned_research_binding_v0.json"
        ).write_text(
            json.dumps(complete_binding, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        ok, reasons, _ = verify_full_evaluation_precheck_v1(
            repo_root=repo,
            ratification=scope_ratification,
            materialization_root=bound_materialization,
            versioned_binding=complete_binding,
            go_token=_INFRA_GO,
        )
        assert ok is False
        assert "DATASET_DIGEST_MISMATCH" in reasons


def test_contract_smoke_evaluation_produces_wiring_outputs(
    bound_materialization: Path,
    complete_binding: dict,
) -> None:
    readiness = run_contract_smoke_evaluation_v0(
        panel_series=build_synthetic_ohlcv_panel_v0(),
        versioned_binding=complete_binding,
        materialization_root=bound_materialization,
    )
    assert readiness.execution_infrastructure_complete is True
    assert readiness.panel_wiring_complete is True
    assert readiness.bound_dataset_materialized is True
    assert readiness.economic_evaluation_executed is False
    assert readiness.smoke_trade_count is not None


def test_dry_run_entrypoint_stops_before_economic_execution(
    bound_materialization: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    result = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        materialization_root=bound_materialization,
        panel_series=build_synthetic_ohlcv_panel_v0(),
        versioned_binding=complete_binding,
        go_token=_INFRA_GO,
    )
    assert result.dry_run_stopped_before_execution is True
    assert result.economic_evaluation_executed is False
    assert len(result.stage_wiring) == 6
    assert all(item.wired for item in result.stage_wiring)


def test_entrypoint_to_dict_carries_no_eval_flag(
    bound_materialization: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    result = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        materialization_root=bound_materialization,
        panel_series=build_synthetic_ohlcv_panel_v0(),
        versioned_binding=complete_binding,
        go_token=_INFRA_GO,
    )
    payload = entrypoint_result_to_dict(result)
    assert payload["economic_evaluation_executed"] is False


def test_infrastructure_summary_flags_no_economic_evaluation(
    scope_ratification: dict,
    complete_binding: dict,
    bound_materialization: Path,
) -> None:
    readiness = run_contract_smoke_evaluation_v0(
        panel_series=build_synthetic_ohlcv_panel_v0(),
        versioned_binding=complete_binding,
        materialization_root=bound_materialization,
    )
    summary = materialize_infrastructure_summary_v0(
        ratification=scope_ratification,
        readiness=readiness,
        origin_main_sha="deadbeef" * 5,
        execution_bundle_dir="/tmp/cs_oi_delta_rank_exec",
    )
    assert summary["economic_evaluation_executed"] is False
    assert summary["economic_classification"] == "NONE"


def test_execution_contract_materialization_flags_no_eval() -> None:
    contract = materialize_execution_contract_v0()
    assert contract["economic_evaluation_executed"] is False
    assert contract["infrastructure_go_token"] == INFRASTRUCTURE_GO_TOKEN
    assert contract["full_eval_callable"] == "run_full_offline_economic_evaluation_v0"


def test_ops_config_loads(complete_binding: dict) -> None:
    cfg = load_ops_evaluation_config_v0(REPO_ROOT)
    assert cfg["strategy_id"] == "cross_sectional_open_interest_delta_rank"
    assert cfg["binding_digest"] == complete_binding["binding_digest"]


def test_execution_path_has_no_runtime_imports() -> None:
    module_name = (
        "src.research.cross_sectional_open_interest_delta_rank_v0_offline_economic_"
        "evaluation_execution_v0"
    )
    module = __import__(module_name, fromlist=["__doc__"])
    source = Path(module.__file__).read_text(encoding="utf-8")
    for token in ("src.execution", "src.governance.live", "src.scheduler"):
        assert token not in source
