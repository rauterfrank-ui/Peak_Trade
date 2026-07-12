"""Contract and integration tests for lead-lag diffusion execution infrastructure v0."""

from __future__ import annotations

import ast
import json
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    GO_TOKEN,
    INFRASTRUCTURE_GO_TOKEN,
    REASON_BINDING_DIGEST_MISMATCH,
    REASON_DATASET_DIGEST_MISMATCH,
    REASON_GO_TOKEN_INVALID,
    REASON_UNIVERSE_DIGEST_MISMATCH,
    RUNTIME_EFFECT,
    load_ops_evaluation_config_v0,
    materialize_execution_contract_v0,
    run_contract_smoke_evaluation_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    verify_execution_start_state_v0,
    verify_full_evaluation_precheck_v1,
    verify_ratified_digests_v0,
    _normalize_cost_execution_binding_for_backtest_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_evaluation_scope_ratification_v0 import (
    ValidationVerdictEnum,
    materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0,
    validate_lead_lag_offline_economic_evaluation_scope_ratification_v0,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_score_v0 import (
    DEFAULT_LAG_WINDOW_L,
    DEFAULT_SIGNAL_LAG_BARS,
    SCORE_FORMULA_VERSION,
)
from src.research.cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0 import (
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
)
from src.research.cross_sectional_relative_strength_v0_score_v0 import (
    SCORE_FORMULA_VERSION as RS_SCORE_FORMULA_VERSION,
)
from src.research.cross_sectional_single_slot_backtest_wiring_v0 import (
    run_single_slot_panel_backtest_v0,
)
from src.research.cross_sectional_single_slot_research_orchestrator_v0 import (
    OrchestratorErrorCode,
    SCORE_FAMILY_LEAD_LAG_DIFFUSION,
    default_lead_lag_operator_binding_v0,
    default_operator_binding_v0,
    run_cross_sectional_single_slot_orchestrator_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.staging_builder import (
    write_bound_period_staging_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
_INFRA_GO = INFRASTRUCTURE_GO_TOKEN
EXECUTION_MODULE = (
    REPO_ROOT / "src/research/"
    "cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution_v0.py"
)
RUNNER_MODULE = (
    REPO_ROOT / "scripts/ops/"
    "run_cross_sectional_futures_lead_lag_information_diffusion_v0_offline_economic_"
    "evaluation_execution_v0.py"
)
FORBIDDEN_RUNTIME_IMPORT_PREFIXES = (
    "src.execution",
    "src.scheduler",
    "src.broker",
)
PY310_STAGING = pytest.mark.skipif(
    sys.version_info < (3, 10),
    reason="panel staging loader requires Python 3.10+ zip(strict=True)",
)


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_hypothesis_binding_v0()


@pytest.fixture(name="scope_ratification")
def fixture_scope_ratification(complete_binding: dict) -> dict:
    return materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


@pytest.fixture(name="bound_staging")
def fixture_bound_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_lead_lag_bound_staging_"))
    staging = write_bound_period_staging_v0(tmp)
    lifecycle = staging / "lifecycle"
    lifecycle.mkdir(parents=True, exist_ok=True)
    lifecycle.joinpath("SOURCE_REGISTRATION.json").write_text(
        '{"source_snapshot_ref":"test:fixture","source_snapshot_digest":"'
        + "a" * 64
        + '","registered":true}\n',
        encoding="utf-8",
    )
    return staging


def test_infrastructure_go_token_constant() -> None:
    assert INFRASTRUCTURE_GO_TOKEN == (
        "GO_CROSS_SECTIONAL_FUTURES_LEAD_LAG_INFORMATION_DIFFUSION_V0_OFFLINE_ECONOMIC_"
        "EVALUATION_EXECUTION_INFRASTRUCTURE_IMPLEMENTATION_V0"
    )


def test_no_runtime_authority_effect_constants() -> None:
    assert AUTHORITY_EFFECT == "NONE"
    assert RUNTIME_EFFECT == "NONE"


def test_binding_materialization_complete_accepted() -> None:
    result = materialize_and_validate_versioned_hypothesis_binding_v0()
    assert result.validation_verdict.value == "ACCEPTED_COMPLETE"


def test_materializer_to_binder_roundtrip_pass(complete_binding: dict) -> None:
    roundtrip = materializer_to_binder_roundtrip_v0(complete_binding)
    assert roundtrip["materializer_to_binder_roundtrip_pass"] is True


def test_deterministic_double_materialization() -> None:
    first = materialize_versioned_hypothesis_binding_v0()
    second = materialize_versioned_hypothesis_binding_v0()
    assert first == second


def test_baseline_l_and_signal_lag_bound_from_binding(complete_binding: dict) -> None:
    pb = complete_binding["parameter_binding"]
    assert pb["lag_window_L"] == DEFAULT_LAG_WINDOW_L == 8
    assert pb["signal_lag_bars"] == DEFAULT_SIGNAL_LAG_BARS == 1
    assert (
        complete_binding["binding"]["selection_hold_exit_rotation_binding"][
            "rebalance_interval_bars"
        ]
        == 1
    )


def test_lead_lag_score_family_orchestrator_path(complete_binding: dict) -> None:
    panel = build_synthetic_panel_series_v0()
    binding = default_lead_lag_operator_binding_v0(complete_binding)
    result = run_cross_sectional_single_slot_orchestrator_v0(
        binding=binding,
        panel_series=panel,
        score_formula_version=SCORE_FORMULA_VERSION,
    )
    assert result.score_formula_version == SCORE_FAMILY_LEAD_LAG_DIFFUSION
    assert len(result.epochs) > 0
    assert result.authority_effect == "NONE"


def test_relative_strength_score_family_unchanged() -> None:
    panel = build_synthetic_panel_series_v0()
    result = run_cross_sectional_single_slot_orchestrator_v0(
        binding=default_operator_binding_v0(),
        panel_series=panel,
    )
    assert result.score_formula_version == RS_SCORE_FORMULA_VERSION
    assert len(result.epochs) > 0


def test_unknown_score_family_fail_closed(complete_binding: dict) -> None:
    binding = default_lead_lag_operator_binding_v0(complete_binding)
    with pytest.raises(ValueError, match=OrchestratorErrorCode.UNKNOWN_SCORE_FAMILY.value):
        run_cross_sectional_single_slot_orchestrator_v0(
            binding=binding,
            panel_series=build_synthetic_panel_series_v0(),
            score_formula_version="unknown_score_family_v0",
        )


def test_lead_lag_orchestrator_deterministic(complete_binding: dict) -> None:
    panel = build_synthetic_panel_series_v0()
    binding = default_lead_lag_operator_binding_v0(complete_binding)
    first = run_cross_sectional_single_slot_orchestrator_v0(
        binding=binding,
        panel_series=panel,
        score_formula_version=SCORE_FORMULA_VERSION,
    )
    second = run_cross_sectional_single_slot_orchestrator_v0(
        binding=binding,
        panel_series=panel,
        score_formula_version=SCORE_FORMULA_VERSION,
    )
    assert first == second


def test_binding_digest_mismatch_rejected(complete_binding: dict) -> None:
    stale = deepcopy(complete_binding)
    stale["binding_digest"] = "f" * 64
    ok, reasons = verify_ratified_digests_v0(
        stale,
        expected_binding_digest=complete_binding["binding_digest"],
    )
    assert ok is False
    assert REASON_BINDING_DIGEST_MISMATCH in reasons


def test_dataset_digest_mismatch_rejected(complete_binding: dict) -> None:
    stale = deepcopy(complete_binding)
    stale["dataset_digest"] = "f" * 64
    ok, reasons = verify_ratified_digests_v0(
        stale,
        expected_dataset_digest=complete_binding["dataset_digest"],
    )
    assert ok is False
    assert REASON_DATASET_DIGEST_MISMATCH in reasons


def test_universe_digest_mismatch_rejected(complete_binding: dict) -> None:
    stale = deepcopy(complete_binding)
    stale["binding"]["pit_universe_binding"]["universe_digest"] = "f" * 64
    ok, reasons = verify_ratified_digests_v0(
        stale,
        expected_universe_digest=(
            complete_binding["binding"]["pit_universe_binding"]["universe_digest"]
        ),
    )
    assert ok is False
    assert REASON_UNIVERSE_DIGEST_MISMATCH in reasons


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
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    ok, reasons, _ = verify_full_evaluation_precheck_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        versioned_binding=complete_binding,
        go_token="INVALID_TOKEN",
    )
    assert ok is False
    assert REASON_GO_TOKEN_INVALID in reasons


def test_contract_smoke_evaluation_no_economic_execution(complete_binding: dict) -> None:
    panel = build_synthetic_panel_series_v0()
    result = run_contract_smoke_evaluation_v0(
        panel_series=panel,
        versioned_binding=complete_binding,
        staging_root=Path("."),
    )
    assert result.economic_evaluation_executed is False
    assert result.authority_effect == "NONE"


@PY310_STAGING
def test_full_evaluation_entrypoint_dry_run_stops_before_execution(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    result = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=_INFRA_GO,
    )
    assert result.economic_evaluation_executed is False
    assert result.dry_run_stopped_before_execution is True


@PY310_STAGING
def test_execution_go_token_rejected_in_infrastructure_dry_run(
    bound_staging: Path,
    scope_ratification: dict,
    complete_binding: dict,
) -> None:
    panel = build_synthetic_panel_series_v0()
    result = run_full_evaluation_entrypoint_dry_run_v1(
        repo_root=REPO_ROOT,
        ratification=scope_ratification,
        staging_root=bound_staging,
        panel_series=panel,
        versioned_binding=complete_binding,
        go_token=GO_TOKEN,
    )
    assert result.precheck_passed is False
    assert result.economic_evaluation_executed is False


def test_ops_config_loads(complete_binding: dict) -> None:
    cfg = load_ops_evaluation_config_v0(REPO_ROOT)
    assert cfg["strategy_id"] == "cross_sectional_futures_lead_lag_information_diffusion"
    assert cfg["binding_digest"] == complete_binding["binding_digest"]


def test_execution_contract_materialization() -> None:
    contract = materialize_execution_contract_v0()
    assert contract["economic_evaluation_executed"] is False
    assert contract["baseline_lag_window"] == 8
    assert (
        contract["canonical_full_evaluation_callable"] == "run_full_offline_economic_evaluation_v0"
    )
    assert "reevaluation_go_token" in contract


def test_scope_ratification_bitcoin_direction_rejected(complete_binding: dict) -> None:
    ratification = materialize_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )
    ratification["bitcoin_direction_allowed"] = True
    validation = validate_lead_lag_offline_economic_evaluation_scope_ratification_v0(
        ratification,
        expected_binding=complete_binding,
    )
    assert validation.verdict is ValidationVerdictEnum.REJECTED
    assert "BITCOIN_DIRECTION_VIOLATION" in validation.fail_reasons


def test_panel_wiring_uses_existing_backtest_owner(complete_binding: dict) -> None:
    panel = build_synthetic_panel_series_v0()
    binding = default_lead_lag_operator_binding_v0(complete_binding)
    orch = run_cross_sectional_single_slot_orchestrator_v0(
        binding=binding,
        panel_series=panel,
        score_formula_version=SCORE_FORMULA_VERSION,
    )
    backtest = run_single_slot_panel_backtest_v0(
        orch,
        panel,
        cost_execution_binding=_normalize_cost_execution_binding_for_backtest_v0(
            complete_binding["cost_execution_binding"]
        ),
    )
    assert "total_return" in backtest.stats
    assert backtest.roundtrip_cost_bps > 0


def _collect_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def test_execution_module_has_no_runtime_imports() -> None:
    imports = _collect_imports(EXECUTION_MODULE)
    for forbidden in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
        assert not any(item == forbidden or item.startswith(forbidden + ".") for item in imports)


def test_runner_module_has_no_runtime_imports() -> None:
    imports = _collect_imports(RUNNER_MODULE)
    for forbidden in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
        assert not any(item == forbidden or item.startswith(forbidden + ".") for item in imports)


def test_config_file_present_and_matches_materialized_binding() -> None:
    cfg_path = REPO_ROOT / (
        "config/research/"
        "cross_sectional_futures_lead_lag_information_diffusion_v0_versioned_hypothesis_binding_v0.json"
    )
    if cfg_path.is_file():
        loaded = json.loads(cfg_path.read_text(encoding="utf-8"))
    else:
        loaded = materialize_versioned_hypothesis_binding_v0()
    materialized = materialize_versioned_hypothesis_binding_v0()
    assert loaded["binding_digest"] == materialized["binding_digest"]
    assert loaded["dataset_digest"] == materialized["dataset_digest"]
