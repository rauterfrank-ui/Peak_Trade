"""Contract and integration tests for pairwise spillover v1 execution infrastructure v0."""

from __future__ import annotations

import ast
import sys
import tempfile
from copy import deepcopy
from pathlib import Path

import pytest

from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
    materializer_to_binder_roundtrip_v0 as authorization_materializer_roundtrip_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_evaluation_execution_v0 import (
    AUTHORITY_EFFECT,
    EXECUTION_GO_TOKEN,
    IMPLEMENTATION_GO_TOKEN,
    RATIFIED_BINDING_DIGEST,
    RATIFIED_DATASET_DIGEST,
    RATIFIED_UNIVERSE_DIGEST,
    REASON_BINDING_DIGEST_MISMATCH,
    REASON_DATASET_DIGEST_MISMATCH,
    REASON_ECONOMIC_EXECUTION_FORBIDDEN,
    REASON_GO_TOKEN_INVALID,
    REASON_UNIVERSE_DIGEST_MISMATCH,
    RUNNER_SCRIPT,
    RUNTIME_EFFECT,
    build_owner_inventory,
    build_reuse_decision,
    build_runner_decision,
    load_ops_evaluation_config_v0,
    materialize_execution_contract_v0,
    run_baseline_offline_economic_evaluation_v0,
    run_contract_smoke_evaluation_v0,
    run_full_evaluation_entrypoint_dry_run_v1,
    run_full_offline_economic_evaluation_v0,
    run_pairwise_spillover_score_ranking_pipeline_v0,
    validate_entry_point_go_token_v0,
    validate_execution_go_token_v0,
    validate_implementation_go_token_v0,
    verify_execution_start_state_v0,
    verify_ratified_digests_v0,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_score_v0 import (
    DEFAULT_FORWARD_LAG_BARS,
    DEFAULT_LAG_WINDOW_L,
    DEFAULT_SIGNAL_LAG_BARS,
    SCORE_FORMULA_VERSION,
)
from src.research.cross_sectional_futures_pairwise_lead_lag_spillover_v1_versioned_hypothesis_binding_v0 import (
    materialize_and_validate_versioned_hypothesis_binding_v0,
    materialize_versioned_hypothesis_binding_v0,
    materializer_to_binder_roundtrip_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.fixture_builder import (
    build_synthetic_panel_series_v0,
)
from tests.research.fixtures.cross_sectional_relative_strength_v0.staging_builder import (
    write_bound_period_staging_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
EXECUTION_MODULE = (
    REPO_ROOT / "src/research/"
    "cross_sectional_futures_pairwise_lead_lag_spillover_v1_offline_economic_"
    "evaluation_execution_v0.py"
)
RUNNER_MODULE = REPO_ROOT / RUNNER_SCRIPT
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


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification() -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0()


@pytest.fixture(name="bound_staging")
def fixture_bound_staging() -> Path:
    tmp = Path(tempfile.mkdtemp(prefix="cs_pairwise_spillover_bound_staging_"))
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


class TestCanonicalEntryPointExists:
    def test_harness_module_exists(self) -> None:
        assert EXECUTION_MODULE.is_file()

    def test_runner_module_exists(self) -> None:
        assert RUNNER_MODULE.is_file()

    def test_import_is_side_effect_free(self) -> None:
        tree = ast.parse(EXECUTION_MODULE.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                pytest.fail("module import must not invoke call expressions at top level")


class TestGoTokenEnforcement:
    def test_implementation_go_token_accepted(self) -> None:
        ok, reasons = validate_implementation_go_token_v0(IMPLEMENTATION_GO_TOKEN)
        assert ok, reasons

    def test_execution_go_token_accepted(self) -> None:
        ok, reasons = validate_execution_go_token_v0(EXECUTION_GO_TOKEN)
        assert ok, reasons

    def test_missing_go_token_rejected(self) -> None:
        ok, reasons = validate_implementation_go_token_v0(None)
        assert not ok
        assert REASON_GO_TOKEN_INVALID in reasons or "GO_TOKEN_MISSING" in reasons

    def test_wrong_go_token_rejected(self) -> None:
        ok, reasons = validate_implementation_go_token_v0("GO_WRONG_TOKEN")
        assert not ok
        assert REASON_GO_TOKEN_INVALID in reasons

    def test_entry_point_dispatch(self) -> None:
        ok, branch = validate_entry_point_go_token_v0(IMPLEMENTATION_GO_TOKEN)
        assert ok and branch == "IMPLEMENTATION_V0"
        ok, branch = validate_entry_point_go_token_v0(EXECUTION_GO_TOKEN)
        assert ok and branch == "EXECUTION_V0"


class TestOfflineBoundary:
    def test_no_runtime_authority_effect_constants(self) -> None:
        assert AUTHORITY_EFFECT == "NONE"
        assert RUNTIME_EFFECT == "NONE"

    def test_futures_only_and_bitcoin_excluded(self, complete_binding: dict) -> None:
        assert complete_binding["system_constraints"]["futures_only"] is True
        assert complete_binding["system_constraints"]["bitcoin_direction_allowed"] is False
        pairwise = complete_binding["pairwise_hypothesis_contract"]
        assert pairwise["spot_allowed"] is False
        assert pairwise["synthetic_spot_allowed"] is False


class TestDigestBinding:
    def test_binding_digest_matches_ratified(self, complete_binding: dict) -> None:
        assert complete_binding["binding_digest"] == RATIFIED_BINDING_DIGEST

    def test_dataset_digest_matches_ratified(self, complete_binding: dict) -> None:
        assert complete_binding["dataset_digest"] == RATIFIED_DATASET_DIGEST

    def test_universe_digest_matches_ratified(self, complete_binding: dict) -> None:
        universe_digest = complete_binding["binding"]["pit_universe_binding"]["universe_digest"]
        assert universe_digest == RATIFIED_UNIVERSE_DIGEST

    def test_binding_digest_mismatch_rejected(self, complete_binding: dict) -> None:
        stale = deepcopy(complete_binding)
        stale["binding_digest"] = "f" * 64
        ok, reasons = verify_ratified_digests_v0(
            stale,
            expected_binding_digest=complete_binding["binding_digest"],
        )
        assert ok is False
        assert REASON_BINDING_DIGEST_MISMATCH in reasons

    def test_dataset_digest_mismatch_rejected(self, complete_binding: dict) -> None:
        stale = deepcopy(complete_binding)
        stale["dataset_digest"] = "f" * 64
        ok, reasons = verify_ratified_digests_v0(
            stale,
            expected_dataset_digest=complete_binding["dataset_digest"],
        )
        assert ok is False
        assert REASON_DATASET_DIGEST_MISMATCH in reasons

    def test_universe_digest_mismatch_rejected(self, complete_binding: dict) -> None:
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


class TestAuthorizationAndBindingValidation:
    def test_start_state_verification_accepts_ratified_bindings(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        result = verify_execution_start_state_v0(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=complete_binding,
        )
        assert result.valid is True
        assert result.fail_reasons == ()

    def test_authorization_status_mismatch_rejected(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        stale = deepcopy(authorization_ratification)
        stale["economic_evaluation_executed"] = True
        result = verify_execution_start_state_v0(
            repo_root=REPO_ROOT,
            authorization_ratification=stale,
            versioned_binding=complete_binding,
        )
        assert result.valid is False

    def test_semantic_binding_mutation_rejected(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        stale = deepcopy(complete_binding)
        stale["score_family_policy"] = "panel_median_benchmark_lagged_return_diffusion_v0"
        result = verify_execution_start_state_v0(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            versioned_binding=stale,
        )
        assert result.valid is False


class TestScoreRankingPipeline:
    def test_canonical_score_owner_invoked(self) -> None:
        panel = build_synthetic_panel_series_v0()
        pipeline = run_pairwise_spillover_score_ranking_pipeline_v0(panel)
        assert pipeline["score_owner"].endswith("score_v0")
        assert pipeline["ranked_pairs"] is not None

    def test_score_parameters_bound_from_defaults(self) -> None:
        assert DEFAULT_LAG_WINDOW_L == 8
        assert DEFAULT_SIGNAL_LAG_BARS == 1
        assert DEFAULT_FORWARD_LAG_BARS == 1
        assert SCORE_FORMULA_VERSION == "pairwise_spillover_graph_v1"

    def test_deterministic_pipeline(self) -> None:
        panel = build_synthetic_panel_series_v0()
        first = run_pairwise_spillover_score_ranking_pipeline_v0(panel)
        second = run_pairwise_spillover_score_ranking_pipeline_v0(panel)
        assert first == second

    def test_cost_bindings_preserved(self, complete_binding: dict) -> None:
        cost = complete_binding["cost_execution_binding"]
        assert cost["fee_binding"]["fee_model_version"] == "backtest_fee_taker_symmetric_v0"
        assert (
            cost["slippage_binding"]["slippage_model_version"] == "backtest_slippage_symmetric_v0"
        )
        assert (
            cost["funding_binding"]["funding_model_version"]
            == "backtest_funding_perpetual_interval_v1"
        )


class TestContractSmokeAndDryRun:
    def test_contract_smoke_no_economic_execution(self, complete_binding: dict) -> None:
        panel = build_synthetic_panel_series_v0()
        result = run_contract_smoke_evaluation_v0(
            repo_root=REPO_ROOT,
            panel_series=panel,
            versioned_binding=complete_binding,
            staging_root=Path("."),
        )
        assert result.economic_evaluation_executed is False
        assert result.authority_effect == "NONE"

    def test_precheck_rejects_invalid_go_token(
        self,
        bound_staging: Path,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        panel = build_synthetic_panel_series_v0()
        result = run_full_evaluation_entrypoint_dry_run_v1(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            staging_root=bound_staging,
            panel_series=panel,
            versioned_binding=complete_binding,
            go_token="INVALID_TOKEN",
        )
        assert result.precheck_passed is False
        assert result.economic_evaluation_executed is False

    def test_execution_go_token_rejected_in_implementation_dry_run(
        self,
        bound_staging: Path,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        panel = build_synthetic_panel_series_v0()
        result = run_full_evaluation_entrypoint_dry_run_v1(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            staging_root=bound_staging,
            panel_series=panel,
            versioned_binding=complete_binding,
            go_token=EXECUTION_GO_TOKEN,
        )
        assert result.precheck_passed is False
        assert REASON_ECONOMIC_EXECUTION_FORBIDDEN in result.reason_codes

    @PY310_STAGING
    def test_full_evaluation_entrypoint_dry_run_stops_before_execution(
        self,
        bound_staging: Path,
        authorization_ratification: dict,
        complete_binding: dict,
    ) -> None:
        panel = build_synthetic_panel_series_v0()
        result = run_full_evaluation_entrypoint_dry_run_v1(
            repo_root=REPO_ROOT,
            authorization_ratification=authorization_ratification,
            staging_root=bound_staging,
            panel_series=panel,
            versioned_binding=complete_binding,
            go_token=IMPLEMENTATION_GO_TOKEN,
        )
        assert result.economic_evaluation_executed is False
        assert result.dry_run_stopped_before_execution is True


class TestNoExecutionDuringImplementation:
    def test_baseline_phase_blocked_without_execution_go(self) -> None:
        result = run_baseline_offline_economic_evaluation_v0(go_token=IMPLEMENTATION_GO_TOKEN)
        assert result.executed is False
        assert result.blocked is True

    def test_full_evaluation_blocked_in_implementation_scope(self) -> None:
        result = run_full_offline_economic_evaluation_v0(go_token=EXECUTION_GO_TOKEN)
        assert result.executed is False
        assert REASON_ECONOMIC_EXECUTION_FORBIDDEN in result.reason_codes


class TestMaterializationRoundtrip:
    def test_binding_materialization_complete(self) -> None:
        result = materialize_and_validate_versioned_hypothesis_binding_v0()
        assert result.validation_verdict.value == "ACCEPTED_COMPLETE"

    def test_hypothesis_materializer_to_binder_roundtrip(self, complete_binding: dict) -> None:
        roundtrip = materializer_to_binder_roundtrip_v0(complete_binding)
        assert roundtrip["materializer_to_binder_roundtrip_pass"] is True

    def test_authorization_materializer_to_binder_roundtrip(
        self,
        authorization_ratification: dict,
    ) -> None:
        roundtrip = authorization_materializer_roundtrip_v0(authorization_ratification)
        assert roundtrip["materializer_to_binder_roundtrip_pass"] is True

    def test_deterministic_double_materialization(self) -> None:
        first = materialize_versioned_hypothesis_binding_v0()
        second = materialize_versioned_hypothesis_binding_v0()
        assert first == second

    def test_execution_contract_materialization(self) -> None:
        contract = materialize_execution_contract_v0()
        assert contract["economic_evaluation_executed"] is False
        assert contract["binding_digest"] == RATIFIED_BINDING_DIGEST
        assert contract["entry_point_status"] == "EXECUTION_INFRASTRUCTURE_COMPLETE"


class TestOpsConfigAndGovernanceArtifacts:
    def test_ops_config_loads(self, complete_binding: dict) -> None:
        cfg = load_ops_evaluation_config_v0(REPO_ROOT)
        assert cfg["strategy_id"] == "cross_sectional_futures_pairwise_lead_lag_spillover"
        assert cfg["binding_digest"] == complete_binding["binding_digest"]

    def test_owner_inventory_exports(self) -> None:
        inventory = build_owner_inventory()
        assert inventory["harness_owner"].endswith("execution_v0")
        assert inventory["score_owner"].endswith("score_v0")

    def test_reuse_decision_exports(self) -> None:
        reuse = build_reuse_decision()
        assert any(item["decision"] == "REUSE_AS_IS" for item in reuse["decisions"])

    def test_runner_decision_exports(self) -> None:
        decision = build_runner_decision()
        assert decision["economic_evaluation_executed"] is False
        assert decision["next_operator_go"] == EXECUTION_GO_TOKEN


class TestImportBoundary:
    def test_no_forbidden_runtime_imports(self) -> None:
        source = EXECUTION_MODULE.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source

    def test_runner_has_no_forbidden_runtime_imports(self) -> None:
        source = RUNNER_MODULE.read_text(encoding="utf-8")
        for prefix in FORBIDDEN_RUNTIME_IMPORT_PREFIXES:
            assert prefix not in source


class TestHarnessRunnerContractRoundtrip:
    def test_runner_delegates_to_harness_constants(self) -> None:
        contract = materialize_execution_contract_v0()
        assert contract["runner_binding_ref"] == RUNNER_SCRIPT
        assert contract["implementation_go_token"] == IMPLEMENTATION_GO_TOKEN
