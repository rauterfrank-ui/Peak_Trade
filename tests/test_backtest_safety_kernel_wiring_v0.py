"""Contract: Safety Kernel boundary backtest state-file binding v0 (offline only)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.backtest.mv2_research_wiring_v1 import (
    SafetyKernelBacktestStateFileBindingConfigV1,
    run_mv2_research_backtest_wiring_v1,
)
from src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1 import (
    KILL_SWITCH_CONTRACT_DIGEST,
)
from src.meta.learning_loop.runtime_eligibility_v1 import (
    CONTRACT_NAME as RUNTIME_ELIGIBILITY_CONTRACT_NAME,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    DecisionOutcome,
    PositionState,
    ReconciliationState,
    SafetyMode,
    TradingGate,
)
from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    NEXT_RECOMMENDED_SLICE,
    parity_surface_assessments_v0,
)
from trading.master_v2.safety_kernel_boundary_backtest_state_file_binding_adapter_v0 import (
    SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE,
    SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
    SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    apply_backtest_safety_kernel_exposure_gate_v0,
    backtest_safety_kernel_state_file_binding_non_authority_ok_v0,
    bind_safety_kernel_boundary_backtest_state_file_evidence_v0,
    compute_backtest_state_file_digest_from_payload_v0,
    evaluate_backtest_safety_kernel_state_file_boundary_only_v0,
    parse_safety_kernel_backtest_state_file_v0,
    verify_safety_kernel_backtest_state_file_digest_v0,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    SAFETY_KERNEL_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg

REPO_ROOT = Path(__file__).resolve().parents[1]

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/safety_kernel_boundary_backtest_state_file_binding_adapter_v0.py",
    REPO_ROOT / "scripts/ops/run_backtest_safety_kernel_wiring_v0.py",
    REPO_ROOT / "tests/test_backtest_safety_kernel_wiring_v0.py",
)


def _scan_forbidden_imports(path: Path, forbidden_tokens: frozenset[str]) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if any(token in alias.name for token in forbidden_tokens):
                    hits.append(alias.name)
        if isinstance(node, ast.ImportFrom) and node.module:
            if any(token in node.module for token in forbidden_tokens):
                hits.append(node.module)
    return hits


def _state_file_payload(**kwargs: object) -> dict[str, object]:
    base = {
        "schema_version": SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "safety_mode": SafetyMode.NORMAL.value,
        "safety_exit_signal_triggered": False,
        "safety_exit_signal_reason_code": "",
        "reconciliation_state": ReconciliationState.RECONCILED.value,
        "position_state": PositionState.FLAT_RECONCILED.value,
        "trading_gate": TradingGate.ENTRY_ALLOWED.value,
        "killswitch_blocked": False,
        "safety_decision_allowed": True,
        "safety_kernel_owner_digest_ref": RUNTIME_ELIGIBILITY_CONTRACT_NAME,
        "killswitch_fencing_digest_ref": KILL_SWITCH_CONTRACT_DIGEST,
        **kwargs,
    }
    digest = compute_backtest_state_file_digest_from_payload_v0(base)
    return {**base, "state_file_digest_ref": digest}


def _record(**kwargs: object):
    return parse_safety_kernel_backtest_state_file_v0(payload=_state_file_payload(**kwargs))


def _base_evidence(*, decision_outcome: str = DecisionOutcome.ENTER_LONG.value):
    return build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-safety-kernel-state-file-decision",
        replay_id="backtest-safety-kernel-state-file-replay",
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=1,
        composition_result_id="composition",
        entry_exit_policy_ref="policy",
        selected_side="long",
        decision_outcome=decision_outcome,
        reason_codes=("PASS",),
        decision_precedence_trace=("enter_long",),
        config_digest="config",
        implementation_digest="impl",
    )


def test_owner_constants_reuse_surface_j_adapter_v0() -> None:
    assert SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER.endswith(
        "safety_kernel_boundary_backtest_state_file_binding_adapter_v0"
    )


def test_slice_sources_exclude_runtime_imports_v0() -> None:
    forbidden = frozenset(
        {
            "execution",
            "scheduler",
            "credentials",
            "live_runtime",
            "testnet",
            "shadow",
            "paper_lane",
            "risk_layer.kill_switch.core",
        }
    )
    for path in _FORBIDDEN_IMPORT_SCAN_PATHS:
        assert path.is_file(), f"missing slice source: {path}"
        hits = _scan_forbidden_imports(path, forbidden)
        assert hits == [], f"forbidden imports in {path}: {hits}"


def test_valid_state_file_binds_safety_policy_decision_v0() -> None:
    evidence = evaluate_backtest_safety_kernel_state_file_boundary_only_v0(_record())
    assert evidence.safety_policy_decision_represented is True
    assert evidence.safety_boundary_ref
    assert evidence.safety_boundary_effect == SAFETY_BOUNDARY_EFFECT_BOUND_OFFLINE
    assert evidence.safety_block_reasons_represented is True
    assert evidence.no_order_without_safety_pass_represented is True
    assert evidence.adapter_compatible is False
    assert apply_backtest_safety_kernel_exposure_gate_v0(1, evidence=evidence) == 1


def test_killswitch_blocked_state_file_blocks_exposure_v0() -> None:
    evidence = evaluate_backtest_safety_kernel_state_file_boundary_only_v0(
        _record(
            killswitch_blocked=True,
            safety_decision_allowed=False,
            safety_mode=SafetyMode.BLOCKED.value,
        )
    )
    assert "killswitch_boundary_blocks_new_entry" in evidence.hard_block_reasons
    assert apply_backtest_safety_kernel_exposure_gate_v0(1, evidence=evidence) == 0


def test_reconciliation_required_blocks_exposure_v0() -> None:
    evidence = evaluate_backtest_safety_kernel_state_file_boundary_only_v0(
        _record(reconciliation_state=ReconciliationState.RECONCILIATION_REQUIRED.value)
    )
    assert "reconciliation_required_blocks_new_exposure" in evidence.hard_block_reasons
    assert apply_backtest_safety_kernel_exposure_gate_v0(1, evidence=evidence) == 0


def test_submission_unknown_blocks_exposure_v0() -> None:
    evidence = evaluate_backtest_safety_kernel_state_file_boundary_only_v0(
        _record(position_state=PositionState.SUBMISSION_UNKNOWN.value)
    )
    assert "unknown_outcome_no_auto_resubmit" in evidence.hard_block_reasons
    assert apply_backtest_safety_kernel_exposure_gate_v0(1, evidence=evidence) == 0


def test_missing_owner_digest_fails_closed_v0() -> None:
    payload = _state_file_payload()
    del payload["safety_kernel_owner_digest_ref"]
    with pytest.raises(ValueError, match="safety_kernel_owner_digest_ref_missing"):
        parse_safety_kernel_backtest_state_file_v0(payload=payload)


def test_corrupted_state_file_digest_fails_closed_v0() -> None:
    payload = _state_file_payload()
    payload["state_file_digest_ref"] = "0" * 64
    with pytest.raises(ValueError, match="safety_kernel_backtest_state_file_digest_mismatch"):
        parse_safety_kernel_backtest_state_file_v0(payload=payload)


def test_backtest_binding_uses_surface_j_adapter_not_duplicate_semantics_v0() -> None:
    bound = bind_safety_kernel_boundary_backtest_state_file_evidence_v0(
        _base_evidence(decision_outcome=DecisionOutcome.ENTER_LONG.value),
        state_file=_record(killswitch_blocked=True, safety_decision_allowed=False),
    )
    assert bound.surface_j_adapter_owner_ref == SAFETY_KERNEL_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER


def test_non_authority_invariants_v0() -> None:
    evidence = evaluate_backtest_safety_kernel_state_file_boundary_only_v0(_record())
    assert evidence.runtime_authority is False
    assert evidence.orders_allowed is False
    assert evidence.credentials_used is False
    assert evidence.economic_evaluation is False
    assert evidence.adapter_compatible is False
    assert backtest_safety_kernel_state_file_binding_non_authority_ok_v0(evidence)


def test_parity_gap_assessment_surface_j_backtest_state_file_pass_v0() -> None:
    safety = next(item for item in parity_surface_assessments_v0() if item.surface_id == "J")
    assert safety.parity_status == "PASS"
    assert safety.missing_binding_if_any == ""
    assert "bind_safety_kernel_boundary_backtest_state_file_evidence_v0" in (
        safety.current_backtest_binding
    )
    assert (
        NEXT_RECOMMENDED_SLICE == "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_4_WAY_PARITY_REWIRE_V0"
    )


def test_mv2_research_wiring_binds_state_file_and_represents_safety_kernel_v0(
    tmp_path: Path,
) -> None:
    payload = _state_file_payload()
    state_path = tmp_path / "safety_kernel_backtest_state.json"
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        safety_kernel_state_file_binding=SafetyKernelBacktestStateFileBindingConfigV1(
            state_file_path=state_path,
            expected_state_file_digest_ref=str(payload["state_file_digest_ref"]),
        ),
    )
    assert result.bar_outcomes
    bound = [o for o in result.bar_outcomes if o.safety_kernel_backtest_state_file_evidence]
    assert len(bound) == len(result.bar_outcomes)
    sample = bound[0].safety_kernel_backtest_state_file_evidence
    assert sample is not None
    assert sample.safety_kernel_boundary_backtest_state_file_bound is True
    assert sample.safety_policy_decision_represented is True


def test_mv2_research_wiring_legacy_without_state_file_unchanged_v0() -> None:
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
    )
    assert all(o.safety_kernel_backtest_state_file_evidence is None for o in result.bar_outcomes)


def test_required_state_file_missing_fails_closed_v0() -> None:
    with pytest.raises(ValueError, match="safety_kernel_backtest_state_file_missing"):
        run_mv2_research_backtest_wiring_v1(
            _bars(n=4),
            strategy_id="ma_crossover",
            cfg=_cfg(),
            explicit_zero_cost_non_economic=True,
            safety_kernel_state_file_binding=SafetyKernelBacktestStateFileBindingConfigV1(
                require_state_file=True,
            ),
        )


def test_verify_state_file_digest_ref_v0() -> None:
    record = _record()
    verify_safety_kernel_backtest_state_file_digest_v0(
        record,
        expected_digest_ref=record.state_file_digest_ref,
    )
    with pytest.raises(ValueError, match="safety_kernel_backtest_state_file_digest_mismatch"):
        verify_safety_kernel_backtest_state_file_digest_v0(record, expected_digest_ref="0" * 64)
