"""Mandatory MV2 boundary state-file binding rewire contract for trend_following v2."""

from __future__ import annotations

import json
import time
from collections import defaultdict
from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from copy import deepcopy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pandas as pd
import pytest

from src.backtest.economic_viability_evidence_v1 import (
    ARTIFACT_FILENAME,
    DataAdmissibilityV1,
    DataSourceKind,
    EconomicViabilityEvidenceError,
    build_economic_viability_evidence_v1,
    compute_bars_data_digest,
    load_economic_viability_evidence_bundle_v1,
)
from src.backtest.parameter_sensitivity_v1 import (
    EvaluationStatus,
    MetricValueStatus,
    ParameterSensitivityGridV1,
    ParameterSensitivityPointV1,
    ParameterSensitivityResultV1,
    PipelineStatus,
)
from src.research.cross_sectional_futures_lead_lag_v0_mv2_research_backtest_wiring_boundary_adapter_v0 import (
    MANDATORY_BOUNDARY_STATE_FILE_BINDING_KEYS,
    MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION,
    REASON_MANDATORY_STATE_FILE_BINDING_MISSING,
    REASON_MANDATORY_STATE_FILE_BINDING_SECTION_MISSING,
    REASON_MANDATORY_STATE_FILE_PATH_UNREADABLE,
    REASON_MANDATORY_STATE_FILE_VALIDATION_FAILED,
    mandatory_bindings_to_mv2_wiring_kwargs_v0,
    resolve_mandatory_mv2_backtest_boundary_state_file_bindings_v0,
)
from src.research.panel_sequential_signal_density_research_adapter_v0 import (
    build_sparse_signal_runtime_step31f_config_v0,
    materialize_panel_member_evaluation_dataset_v0,
    resolve_panel_staging_root,
)
from src.research.trend_following_v2_offline_economic_evaluation_authorization_ratification_v0 import (
    materialize_offline_economic_evaluation_authorization_ratification_v0,
)
from src.research.trend_following_v2_offline_economic_evaluation_execution_v0 import (
    BASELINE_EXECUTION_GO_TOKEN,
    load_ops_evaluation_config_v0,
)
from src.research.trend_following_v2_versioned_research_binding_v0 import (
    materialize_versioned_research_binding_v0,
)
from src.research.versioned_final_fleet_bindings_offline_economic_evaluation_v0 import (
    build_runtime_step31f_config_v0,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
STAGING_ROOT = resolve_panel_staging_root()
RVN_PANEL_MEMBER_ID = "okx:linear_perpetual:RVN:USDT:USDT:perp"
REFERENCE_CONFIG_PATH = (
    REPO_ROOT
    / "config/ops/cross_sectional_futures_lead_lag_information_diffusion_v0_economic_evaluation_v1.json"
)
TREND_FOLLOWING_OPS_CONFIG_PATH = (
    REPO_ROOT / "config/ops/trend_following_v2_economic_evaluation_v1.json"
)
BOUNDED_PRIMARY_BACKTEST_BAR_LIMIT = 240
TARGET_SINGLE_TEST_MAX_SECONDS = 15.0
TARGET_FILE_MAX_SECONDS = 30.0

GATE_PATCH_TARGETS: tuple[tuple[str, str], ...] = (
    (
        "src.backtest.mv2_research_wiring_v1",
        "apply_backtest_capital_risk_sizing_exposure_gate_v0",
    ),
    (
        "src.backtest.mv2_research_wiring_v1",
        "apply_backtest_canonical_order_intent_exposure_gate_v0",
    ),
    (
        "src.backtest.mv2_research_wiring_v1",
        "apply_backtest_safety_kernel_exposure_gate_v0",
    ),
    (
        "src.backtest.mv2_research_wiring_v1",
        "apply_backtest_killswitch_exposure_gate_v0",
    ),
    (
        "src.backtest.mv2_research_wiring_v1",
        "apply_backtest_reconciliation_exposure_gate_v0",
    ),
)


def _reference_binding_section() -> dict[str, Any]:
    return json.loads(REFERENCE_CONFIG_PATH.read_text(encoding="utf-8"))[
        MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION
    ]


def _ops_config_without_binding_key(cfg: dict[str, Any], key: str) -> dict[str, Any]:
    mutated = deepcopy(cfg)
    section = dict(mutated[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION])
    section.pop(key, None)
    mutated[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION] = section
    return mutated


def _bounded_parameter_sensitivity_result_v0() -> ParameterSensitivityResultV1:
    grid = ParameterSensitivityGridV1(
        grid_id="bounded_test_grid_v0",
        grid_version="v0",
        strategy_id="trend_following",
        strategy_version="v2",
        canonical_trading_logic_version="bounded_test_v0",
        parameter_names=("fee_bps",),
        parameter_values=((10.0,),),
        combination_count=1,
        search_space_bounds={"fee_bps": {"min": 10.0, "max": 10.0}},
        seed=42,
        train_period="bounded_train",
        validation_period="bounded_validation",
        out_of_sample_period="bounded_oos",
        config_digest="bounded_config_digest",
        implementation_digest="bounded_implementation_digest",
        data_digest_or_explicit_missing="bounded_data_digest",
        grid_digest="bounded_grid_digest",
    )
    point = ParameterSensitivityPointV1(
        parameter_set_id="bounded_point_v0",
        parameter_values={"fee_bps": 10.0},
        evaluation_status=EvaluationStatus.EVALUATED,
        reason_codes=(),
        train_result_ref="bounded_train_ref",
        validation_result_ref="bounded_validation_ref",
        out_of_sample_result_ref="bounded_oos_ref",
        net_return=MetricValueStatus.COMPUTED,
        net_return_value=0.0,
        net_expectancy=MetricValueStatus.COMPUTED,
        net_expectancy_value=0.0,
        profit_factor=MetricValueStatus.COMPUTED,
        profit_factor_value=0.0,
        max_drawdown=MetricValueStatus.COMPUTED,
        max_drawdown_value=0.0,
        trade_count=MetricValueStatus.COMPUTED,
        trade_count_value=0.0,
        walk_forward_status="BOUNDED_NOT_RUN",
        monte_carlo_status="BOUNDED_NOT_RUN",
        stress_status="BOUNDED_NOT_RUN",
        cost_model_ref="bounded_cost_model_ref",
        funding_model_ref="bounded_funding_model_ref",
        config_digest="bounded_config_digest",
        implementation_digest="bounded_implementation_digest",
        data_digest="bounded_data_digest",
        result_digest="bounded_result_digest",
    )
    return ParameterSensitivityResultV1(
        contract_version="parameter_sensitivity.v1",
        owner="backtest.parameter_sensitivity_v1",
        pipeline_status=PipelineStatus.PIPELINE_PASS,
        parameter_robustness_policy_pass=True,
        parameter_robustness_policy_status="PASS",
        grid=grid,
        grid_digest=grid.grid_digest,
        result_digest="bounded_result_digest",
        combination_count=1,
        points=(point,),
        failed_point_count=0,
        blocked_point_count=0,
        seed=42,
        reason_codes=("bounded_test_fixture",),
        parameter_neighbor_degradation=0.0,
    )


@contextmanager
def bounded_economic_robustness_stage_patches_v0() -> Iterator[None]:
    import src.backtest.economic_viability_evidence_v1 as ev_module

    original_build = ev_module.build_economic_viability_evidence_v1
    original_wiring = ev_module.mv2_wiring.run_mv2_research_backtest_wiring_v1

    def _bounded_primary_wiring(*args: Any, **kwargs: Any) -> Any:
        bars = kwargs.get("bars")
        if bars is None and args:
            bars = args[0]
        if isinstance(bars, pd.DataFrame) and len(bars) > BOUNDED_PRIMARY_BACKTEST_BAR_LIMIT:
            bounded_bars = bars.tail(BOUNDED_PRIMARY_BACKTEST_BAR_LIMIT)
            if "bars" in kwargs:
                kwargs = dict(kwargs)
                kwargs["bars"] = bounded_bars
                return original_wiring(*args, **kwargs)
            return original_wiring(bounded_bars, *args[1:], **kwargs)
        return original_wiring(*args, **kwargs)

    def _bounded_build(*, bars: pd.DataFrame, **kwargs: Any) -> Any:
        bounded_kwargs = dict(kwargs)
        bounded_kwargs["monte_carlo_runs"] = 0
        bounded_kwargs["walk_forward_train_bars"] = len(bars) + 1000
        bounded_kwargs["walk_forward_test_bars"] = 1
        bounded_kwargs["walk_forward_step_bars"] = 1
        return original_build(bars=bars, **bounded_kwargs)

    with (
        patch.object(
            ev_module,
            "build_economic_viability_evidence_v1",
            side_effect=_bounded_build,
        ),
        patch.object(
            ev_module.mv2_wiring,
            "run_mv2_research_backtest_wiring_v1",
            side_effect=_bounded_primary_wiring,
        ),
        patch.object(
            ev_module.mv2_wiring,
            "run_mv2_walk_forward_wiring_v1",
            side_effect=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("walk_forward_must_not_run_in_bounded_test")
            ),
        ),
        patch.object(
            ev_module.mv2_wiring,
            "bind_monte_carlo_analysis_v1",
            side_effect=lambda *a, **k: (_ for _ in ()).throw(
                AssertionError("monte_carlo_must_not_run_in_bounded_test")
            ),
        ),
        patch.object(
            ev_module,
            "run_parameter_sensitivity_v1",
            side_effect=lambda **_k: _bounded_parameter_sensitivity_result_v0(),
        ),
    ):
        yield


@pytest.fixture(name="complete_binding")
def fixture_complete_binding() -> dict:
    return materialize_versioned_research_binding_v0(repo_root=REPO_ROOT)


@pytest.fixture(name="authorization_ratification")
def fixture_authorization_ratification(complete_binding: dict) -> dict:
    return materialize_offline_economic_evaluation_authorization_ratification_v0(
        repo_root=REPO_ROOT,
        versioned_binding=complete_binding,
    )


@pytest.fixture(name="ops_config")
def fixture_ops_config() -> dict:
    return load_ops_evaluation_config_v0(REPO_ROOT)


class TestConfigBindingContract:
    def test_ops_template_contains_mandatory_binding_section(self, ops_config: dict) -> None:
        section = ops_config.get(
            MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION
        )
        assert isinstance(section, dict)
        for key in MANDATORY_BOUNDARY_STATE_FILE_BINDING_KEYS:
            assert key in section
            entry = section[key]
            assert isinstance(entry.get("state_file_path"), str)
            assert isinstance(entry.get("expected_state_file_digest_ref"), str)

    def test_binding_section_matches_reference_pattern(self, ops_config: dict) -> None:
        reference = _reference_binding_section()
        actual = ops_config[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION]
        assert actual == reference

    def test_resolve_mandatory_bindings_from_ops_config(self, ops_config: dict) -> None:
        bindings, reasons = resolve_mandatory_mv2_backtest_boundary_state_file_bindings_v0(
            REPO_ROOT,
            ops_config,
        )
        assert reasons == ()
        assert bindings is not None
        kwargs = mandatory_bindings_to_mv2_wiring_kwargs_v0(bindings)
        assert set(kwargs) == {
            "capital_risk_sizing_state_file_binding",
            "canonical_order_intent_state_file_binding",
            "safety_kernel_state_file_binding",
            "killswitch_state_file_binding",
            "reconciliation_state_file_binding",
        }


class TestConfigPropagation:
    @pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="panel staging root unavailable")
    def test_sparse_signal_materializer_preserves_binding_section(
        self,
        tmp_path: Path,
    ) -> None:
        config_path = build_sparse_signal_runtime_step31f_config_v0(
            repo_root=REPO_ROOT,
            strategy_id="trend_following",
            staging_root=STAGING_ROOT,
            instrument_id=RVN_PANEL_MEMBER_ID,
            output_path=tmp_path / "runtime_config.json",
        )
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        assert (
            cfg[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION]
            == _reference_binding_section()
        )

    @pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="panel staging root unavailable")
    def test_runtime_config_materializer_preserves_binding_section(
        self,
        tmp_path: Path,
    ) -> None:
        narrow = materialize_panel_member_evaluation_dataset_v0(
            staging_root=STAGING_ROOT,
            instrument_id=RVN_PANEL_MEMBER_ID,
            output_root=tmp_path / "member",
        )
        config_path = build_runtime_step31f_config_v0(
            repo_root=REPO_ROOT,
            strategy_id="trend_following",
            narrow_dataset=narrow,
            output_path=tmp_path / "runtime_config.json",
        )
        cfg = json.loads(config_path.read_text(encoding="utf-8"))
        assert (
            cfg[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION]
            == _reference_binding_section()
        )


class TestBuilderFailClosed:
    def test_builder_blocks_when_binding_section_missing(self, ops_config: dict) -> None:
        cfg = deepcopy(ops_config)
        cfg.pop(MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION, None)
        bars = pd.DataFrame({"close": [1.0, 1.1]})
        instrument_id = "okx:linear_perpetual:ETH:USDT:USDT:perp"
        with pytest.raises(EconomicViabilityEvidenceError) as exc:
            build_economic_viability_evidence_v1(
                bars=bars,
                data_admissibility=DataAdmissibilityV1(
                    source_kind=DataSourceKind.SYNTHETIC_CONTRACT_FIXTURE,
                    instrument_id=instrument_id,
                    data_digest=compute_bars_data_digest(bars),
                    data_ref="test",
                ),
                strategy_id="trend_following",
                cfg=cfg,
                instrument_id=instrument_id,
                repo_root=REPO_ROOT,
            )
        assert REASON_MANDATORY_STATE_FILE_BINDING_SECTION_MISSING in str(exc.value)


@pytest.mark.parametrize("binding_key", MANDATORY_BOUNDARY_STATE_FILE_BINDING_KEYS)
def test_resolve_fail_closed_on_each_missing_binding_key(
    ops_config: dict,
    binding_key: str,
) -> None:
    cfg = _ops_config_without_binding_key(ops_config, binding_key)
    bindings, reasons = resolve_mandatory_mv2_backtest_boundary_state_file_bindings_v0(
        REPO_ROOT,
        cfg,
    )
    assert bindings is None
    assert any(
        code == f"{REASON_MANDATORY_STATE_FILE_BINDING_MISSING}:{binding_key}" for code in reasons
    )


def test_resolve_fail_closed_on_unreadable_state_file_path(ops_config: dict) -> None:
    cfg = deepcopy(ops_config)
    section = dict(cfg[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION])
    section["capital_risk_sizing"] = {
        "state_file_path": "config/research/does_not_exist/capital_risk_sizing.json",
        "expected_state_file_digest_ref": "0" * 64,
    }
    cfg[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION] = section
    bindings, reasons = resolve_mandatory_mv2_backtest_boundary_state_file_bindings_v0(
        REPO_ROOT,
        cfg,
    )
    assert bindings is None
    assert any(
        code.startswith(f"{REASON_MANDATORY_STATE_FILE_PATH_UNREADABLE}:") for code in reasons
    )


def test_resolve_fail_closed_on_state_file_digest_mismatch(ops_config: dict) -> None:
    cfg = deepcopy(ops_config)
    section = dict(cfg[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION])
    entry = dict(section["killswitch"])
    entry["expected_state_file_digest_ref"] = "f" * 64
    section["killswitch"] = entry
    cfg[MV2_RESEARCH_BACKTEST_MANDATORY_BOUNDARY_STATE_FILE_BINDING_SECTION] = section
    bindings, reasons = resolve_mandatory_mv2_backtest_boundary_state_file_bindings_v0(
        REPO_ROOT,
        cfg,
    )
    assert bindings is None
    assert any(
        code.startswith(f"{REASON_MANDATORY_STATE_FILE_VALIDATION_FAILED}:") for code in reasons
    )


@pytest.mark.skipif(not STAGING_ROOT.is_dir(), reason="panel staging root unavailable")
class TestBoundedSingleMemberMandatoryBoundaryE2E:
    def test_production_baseline_executes_all_mandatory_boundary_gates(
        self,
        authorization_ratification: dict,
        complete_binding: dict,
        tmp_path: Path,
    ) -> None:
        import src.research.trend_following_v2_offline_economic_evaluation_execution_v0 as harness

        gate_counts: dict[str, int] = defaultdict(int)
        patches: list[Any] = []

        for module_path, attr in GATE_PATCH_TARGETS:
            import importlib

            mod = importlib.import_module(module_path)
            original = getattr(mod, attr)
            fq = f"{module_path}.{attr}"

            def _make_wrapper(fn: Any, name: str):
                def _wrapped(*args: Any, **kwargs: Any) -> Any:
                    gate_counts[name] += 1
                    return fn(*args, **kwargs)

                return _wrapped

            patches.append(patch.object(mod, attr, _make_wrapper(original, fq)))

        real_owner = harness._run_candidate_with_runtime_config_v0
        started = time.time()
        with ExitStack() as stack:
            stack.enter_context(bounded_economic_robustness_stage_patches_v0())
            owner_spy = stack.enter_context(
                patch.object(
                    harness,
                    "_run_candidate_with_runtime_config_v0",
                    wraps=real_owner,
                )
            )
            for gate_patch in patches:
                stack.enter_context(gate_patch)
            result = harness.run_baseline_offline_economic_evaluation_v0(
                go_token=BASELINE_EXECUTION_GO_TOKEN,
                repo_root=REPO_ROOT,
                authorization_ratification=authorization_ratification,
                versioned_binding=complete_binding,
                staging_root=STAGING_ROOT,
                scratch_root=tmp_path / "baseline_scratch",
                invoke_baseline_owner=True,
                panel_member_instrument_ids=(RVN_PANEL_MEMBER_ID,),
                skip_member_trade_count_backtest_v0=True,
            )
        elapsed = time.time() - started

        assert elapsed <= TARGET_SINGLE_TEST_MAX_SECONDS, (
            f"bounded_e2e_runtime_exceeded phase=baseline_member={RVN_PANEL_MEMBER_ID} "
            f"elapsed={elapsed:.3f}s limit={TARGET_SINGLE_TEST_MAX_SECONDS}s"
        )
        assert owner_spy.call_count == 1
        assert result.economic_evaluation_executed is True
        assert result.economic_evidence_persisted is True
        assert result.backtest_engine_completed is True

        for module_path, attr in GATE_PATCH_TARGETS:
            fq = f"{module_path}.{attr}"
            assert gate_counts[fq] > 0, f"mandatory_boundary_gate_not_executed:{fq}"

        output_dir = tmp_path / "baseline_scratch" / "baseline_candidate_output"
        loaded = load_economic_viability_evidence_bundle_v1(output_dir)
        assert (output_dir / ARTIFACT_FILENAME).is_file()
        assert loaded.evidence.strategy_signal_binding["mv2_replay_signal_source"] == (
            "mv2_decision_replay_series"
        )


def test_file_runtime_bound_under_target() -> None:
    assert TARGET_FILE_MAX_SECONDS >= TARGET_SINGLE_TEST_MAX_SECONDS


class TestRepairScopeBoundaryGuard:
    def test_governance_boundary_guard_accepts_rewire_scope(self) -> None:
        from src.governance.economic_diagnostic_optimization_boundary_v0 import (
            build_boundary_report,
        )

        changed_files = [
            "config/governance/economic_diagnostic_optimization_boundary_canonical_owner_map_v0.json",
            "config/ops/trend_following_v2_economic_evaluation_v1.json",
            "src/backtest/economic_viability_evidence_v1.py",
            "src/research/versioned_final_fleet_bindings_offline_economic_evaluation_v0.py",
            "scripts/ops/run_economic_viability_evidence_evaluation_v1.py",
            "tests/research/test_trend_following_v2_mandatory_boundary_state_file_binding_rewire_v0.py",
        ]
        report = build_boundary_report(changed_files, repo_root=REPO_ROOT)
        assert report.admissible is True
        assert report.impact_unknown is False
