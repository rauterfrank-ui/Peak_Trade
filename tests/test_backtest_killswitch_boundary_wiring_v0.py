"""Contract: KillSwitch boundary backtest wiring v0 after Safety Kernel wiring (offline only)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.backtest.mv2_research_wiring_v1 import (
    KillSwitchBacktestStateFileBindingConfigV1,
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
from trading.master_v2.killswitch_boundary_backtest_state_file_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
    KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    apply_backtest_combined_safety_and_killswitch_exposure_gate_v0,
    apply_backtest_killswitch_exposure_gate_v0,
    backtest_state_file_binding_non_authority_ok_v0,
    bind_killswitch_boundary_backtest_state_file_evidence_v0,
    compute_backtest_state_file_digest_from_payload_v0,
    evaluate_backtest_state_file_boundary_only_v0,
    killswitch_boundary_semantics_represented_in_backtest_v0,
    parse_killswitch_backtest_state_file_v0,
    verify_killswitch_backtest_state_file_digest_v0,
)
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    KillSwitchBoundaryMode,
)
from trading.master_v2.safety_kernel_boundary_backtest_state_file_binding_adapter_v0 import (
    SAFETY_KERNEL_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    compute_backtest_state_file_digest_from_payload_v0 as safety_kernel_digest,
    evaluate_backtest_safety_kernel_state_file_boundary_only_v0,
    parse_safety_kernel_backtest_state_file_v0,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg

REPO_ROOT = Path(__file__).resolve().parents[1]

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/killswitch_boundary_backtest_state_file_binding_adapter_v0.py",
    REPO_ROOT / "scripts/ops/run_backtest_killswitch_boundary_wiring_v0.py",
    REPO_ROOT / "tests/test_backtest_killswitch_boundary_wiring_v0.py",
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


def _killswitch_payload(*, mode: str, prior: bool = False) -> dict[str, object]:
    base = {
        "schema_version": KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "killswitch_boundary_mode": mode,
        "fencing_digest_ref": KILL_SWITCH_CONTRACT_DIGEST,
        "prior_killswitch_active": prior,
    }
    digest = compute_backtest_state_file_digest_from_payload_v0(base)
    return {**base, "state_file_digest_ref": digest}


def _safety_kernel_payload(**kwargs: object) -> dict[str, object]:
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
    return {**base, "state_file_digest_ref": safety_kernel_digest(base)}


def _record(*, mode: str, prior: bool = False):
    return parse_killswitch_backtest_state_file_v0(
        payload=_killswitch_payload(mode=mode, prior=prior)
    )


def _base_evidence(*, decision_outcome: str = DecisionOutcome.ENTER_LONG.value):
    return build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-killswitch-boundary-decision",
        replay_id="backtest-killswitch-boundary-replay",
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


def test_owner_constants_reuse_surface_k_adapter_v0() -> None:
    assert KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER.endswith(
        "killswitch_boundary_backtest_state_file_binding_adapter_v0"
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


def test_block_new_semantics_represented_in_backtest_v0() -> None:
    evidence = evaluate_backtest_state_file_boundary_only_v0(
        _record(mode=KillSwitchBoundaryMode.BLOCK_NEW.value)
    )
    assert evidence.killswitch_boundary_represented_in_backtest is True
    assert evidence.block_new_represented_in_backtest is True
    assert apply_backtest_killswitch_exposure_gate_v0(1, evidence=evidence) == 0


def test_cancel_pending_semantics_represented_in_backtest_v0() -> None:
    evidence = evaluate_backtest_state_file_boundary_only_v0(
        _record(mode=KillSwitchBoundaryMode.CANCEL_PENDING.value)
    )
    assert evidence.cancel_pending_represented_in_backtest is True
    assert evidence.cancel_pending_required is True
    assert apply_backtest_killswitch_exposure_gate_v0(1, evidence=evidence) == 1


def test_reduce_to_flat_semantics_represented_in_backtest_v0() -> None:
    evidence = evaluate_backtest_state_file_boundary_only_v0(
        _record(mode=KillSwitchBoundaryMode.REDUCE_TO_FLAT.value)
    )
    assert evidence.reduce_to_flat_represented_in_backtest is True
    assert evidence.reduce_to_flat_required is True
    assert apply_backtest_killswitch_exposure_gate_v0(1, evidence=evidence) == 1


def test_no_automatic_resume_semantics_represented_in_backtest_v0() -> None:
    evidence = evaluate_backtest_state_file_boundary_only_v0(
        _record(mode=KillSwitchBoundaryMode.BLOCK_NEW.value, prior=True)
    )
    assert evidence.no_automatic_resume_represented_in_backtest is True
    assert "killswitch_no_auto_resume" in evidence.offline_binding.boundary.hard_block_reasons
    assert apply_backtest_killswitch_exposure_gate_v0(1, evidence=evidence) == 0


def test_no_order_without_safety_and_killswitch_pass_represented_v0() -> None:
    ks_evidence = evaluate_backtest_state_file_boundary_only_v0(
        _record(mode=KillSwitchBoundaryMode.NORMAL.value)
    )
    sk_evidence = evaluate_backtest_safety_kernel_state_file_boundary_only_v0(
        parse_safety_kernel_backtest_state_file_v0(payload=_safety_kernel_payload())
    )
    assert ks_evidence.no_order_without_safety_and_killswitch_pass_represented_in_backtest
    gated = apply_backtest_combined_safety_and_killswitch_exposure_gate_v0(
        1,
        killswitch_evidence=ks_evidence,
        safety_kernel_evidence=sk_evidence,
    )
    assert gated == 1
    blocked_sk = evaluate_backtest_safety_kernel_state_file_boundary_only_v0(
        parse_safety_kernel_backtest_state_file_v0(
            payload=_safety_kernel_payload(
                killswitch_blocked=True,
                safety_decision_allowed=False,
                safety_mode=SafetyMode.BLOCKED.value,
            )
        )
    )
    assert (
        apply_backtest_combined_safety_and_killswitch_exposure_gate_v0(
            1,
            killswitch_evidence=ks_evidence,
            safety_kernel_evidence=blocked_sk,
        )
        == 0
    )


def test_backtest_binding_uses_surface_k_adapter_not_duplicate_semantics_v0() -> None:
    bound = bind_killswitch_boundary_backtest_state_file_evidence_v0(
        _base_evidence(decision_outcome=DecisionOutcome.ENTER_LONG.value),
        state_file=_record(mode=KillSwitchBoundaryMode.BLOCK_NEW.value),
    )
    assert (
        bound.surface_k_adapter_owner_ref
        == KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
    )
    assert killswitch_boundary_semantics_represented_in_backtest_v0(bound)


def test_non_authority_invariants_v0() -> None:
    evidence = evaluate_backtest_state_file_boundary_only_v0(
        _record(mode=KillSwitchBoundaryMode.EMERGENCY_FLATTEN.value)
    )
    assert evidence.runtime_authority is False
    assert evidence.orders_allowed is False
    assert evidence.credentials_used is False
    assert evidence.economic_evaluation is False
    assert backtest_state_file_binding_non_authority_ok_v0(evidence)


def test_parity_gap_assessment_surface_k_backtest_boundary_wiring_pass_v0() -> None:
    killswitch = next(item for item in parity_surface_assessments_v0() if item.surface_id == "K")
    assert killswitch.parity_status == "PASS"
    assert killswitch.missing_binding_if_any == ""
    assert "bind_killswitch_boundary_backtest_state_file_evidence_v0" in (
        killswitch.current_backtest_binding
    )
    assert (
        NEXT_RECOMMENDED_SLICE == "INTEGRATED_VS_SCENARIO_REPLAY_FULL_SYSTEM_4_WAY_PARITY_REWIRE_V0"
    )


def test_mv2_research_wiring_binds_killswitch_and_safety_kernel_chain_v0(
    tmp_path: Path,
) -> None:
    ks_payload = _killswitch_payload(mode=KillSwitchBoundaryMode.BLOCK_NEW.value)
    sk_payload = _safety_kernel_payload()
    ks_path = tmp_path / "killswitch_backtest_state.json"
    sk_path = tmp_path / "safety_kernel_backtest_state.json"
    ks_path.write_text(json.dumps(ks_payload, indent=2), encoding="utf-8")
    sk_path.write_text(json.dumps(sk_payload, indent=2), encoding="utf-8")
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        killswitch_state_file_binding=KillSwitchBacktestStateFileBindingConfigV1(
            state_file_path=ks_path,
            expected_state_file_digest_ref=str(ks_payload["state_file_digest_ref"]),
        ),
        safety_kernel_state_file_binding=SafetyKernelBacktestStateFileBindingConfigV1(
            state_file_path=sk_path,
            expected_state_file_digest_ref=str(sk_payload["state_file_digest_ref"]),
        ),
    )
    assert result.bar_outcomes
    sample = result.bar_outcomes[0]
    assert sample.killswitch_backtest_state_file_evidence is not None
    assert sample.safety_kernel_backtest_state_file_evidence is not None
    ks = sample.killswitch_backtest_state_file_evidence
    assert ks.killswitch_boundary_represented_in_backtest is True
    assert ks.no_order_without_safety_and_killswitch_pass_represented_in_backtest is True
    assert all(o.position_signal == 0 for o in result.bar_outcomes)


def test_mv2_research_wiring_legacy_without_state_file_unchanged_v0() -> None:
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
    )
    assert all(o.killswitch_backtest_state_file_evidence is None for o in result.bar_outcomes)


def test_required_state_file_missing_fails_closed_v0() -> None:
    with pytest.raises(ValueError, match="killswitch_backtest_state_file_missing"):
        run_mv2_research_backtest_wiring_v1(
            _bars(n=4),
            strategy_id="ma_crossover",
            cfg=_cfg(),
            explicit_zero_cost_non_economic=True,
            killswitch_state_file_binding=KillSwitchBacktestStateFileBindingConfigV1(
                require_state_file=True,
            ),
        )


def test_verify_state_file_digest_ref_v0() -> None:
    record = _record(mode=KillSwitchBoundaryMode.NORMAL.value)
    verify_killswitch_backtest_state_file_digest_v0(
        record,
        expected_digest_ref=record.state_file_digest_ref,
    )
    with pytest.raises(ValueError, match="killswitch_backtest_state_file_digest_mismatch"):
        verify_killswitch_backtest_state_file_digest_v0(record, expected_digest_ref="0" * 64)
