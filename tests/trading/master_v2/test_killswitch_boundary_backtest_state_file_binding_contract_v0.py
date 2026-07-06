"""Contract: KillSwitch boundary backtest state-file binding v0 (offline only)."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

from src.backtest.mv2_research_wiring_v1 import (
    KillSwitchBacktestStateFileBindingConfigV1,
    run_mv2_research_backtest_wiring_v1,
)
from src.meta.learning_loop.killswitch_writer_fencing_and_independent_read_paths_v1 import (
    KILL_SWITCH_CONTRACT_DIGEST,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import DecisionOutcome
from trading.master_v2.full_canonical_system_backtest_parity_gap_assessment_v0 import (
    NEXT_RECOMMENDED_SLICE,
    parity_surface_assessments_v0,
)
from trading.master_v2.killswitch_boundary_backtest_state_file_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_BINDING_ADAPTER_OWNER,
    KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
    apply_backtest_killswitch_exposure_gate_v0,
    backtest_state_file_binding_non_authority_ok_v0,
    bind_killswitch_boundary_backtest_state_file_evidence_v0,
    compute_backtest_state_file_digest_from_payload_v0,
    evaluate_backtest_state_file_boundary_only_v0,
    parse_killswitch_backtest_state_file_v0,
    verify_killswitch_backtest_state_file_digest_v0,
)
from trading.master_v2.killswitch_boundary_offline_replay_binding_adapter_v0 import (
    KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER,
    KillSwitchBoundaryMode,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    build_scenario_tick_decision_evidence_v0,
)
from tests.backtest.test_mv2_research_wiring_v1 import _bars, _cfg

REPO_ROOT = Path(__file__).resolve().parents[3]

_FORBIDDEN_IMPORT_SCAN_PATHS = (
    REPO_ROOT
    / "src/trading/master_v2/killswitch_boundary_backtest_state_file_binding_adapter_v0.py",
    REPO_ROOT / "scripts/ops/run_backtest_killswitch_state_file_wiring_v0.py",
    REPO_ROOT
    / "tests/trading/master_v2/test_killswitch_boundary_backtest_state_file_binding_contract_v0.py",
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


def _state_file_payload(*, mode: str, prior: bool = False) -> dict[str, object]:
    base = {
        "schema_version": KILLSWITCH_BOUNDARY_BACKTEST_STATE_FILE_SCHEMA_VERSION,
        "killswitch_boundary_mode": mode,
        "fencing_digest_ref": KILL_SWITCH_CONTRACT_DIGEST,
        "prior_killswitch_active": prior,
    }
    digest = compute_backtest_state_file_digest_from_payload_v0(base)
    return {**base, "state_file_digest_ref": digest}


def _base_evidence(*, decision_outcome: str = DecisionOutcome.OBSERVE.value):
    return build_scenario_tick_decision_evidence_v0(
        decision_id="backtest-killswitch-state-file-decision",
        replay_id="backtest-killswitch-state-file-replay",
        instrument_id="inst-eth-usdt-perp",
        trading_epoch=1,
        composition_result_id="composition",
        entry_exit_policy_ref="policy",
        selected_side="long",
        decision_outcome=decision_outcome,
        reason_codes=("PASS",),
        decision_precedence_trace=("observe",),
        config_digest="config",
        implementation_digest="impl",
    )


def _record(*, mode: str, prior: bool = False):
    return parse_killswitch_backtest_state_file_v0(
        payload=_state_file_payload(mode=mode, prior=prior)
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


@pytest.mark.parametrize(
    ("mode", "signal", "expected"),
    [
        (KillSwitchBoundaryMode.BLOCK_NEW.value, 1, 0),
        (KillSwitchBoundaryMode.NO_NEW_POSITIONS.value, 1, 0),
        (KillSwitchBoundaryMode.NO_POSITION_INCREASE.value, 1, 0),
        (KillSwitchBoundaryMode.CANCEL_PENDING.value, 1, 1),
        (KillSwitchBoundaryMode.REDUCE_TO_FLAT.value, 1, 1),
        (KillSwitchBoundaryMode.EMERGENCY_FLATTEN.value, 1, 0),
    ],
)
def test_backtest_exposure_gate_by_mode_v0(mode: str, signal: int, expected: int) -> None:
    evidence = evaluate_backtest_state_file_boundary_only_v0(_record(mode=mode))
    gated = apply_backtest_killswitch_exposure_gate_v0(signal, evidence=evidence)
    assert gated == expected


def test_no_new_positions_permits_existing_position_management_v0() -> None:
    evidence = evaluate_backtest_state_file_boundary_only_v0(
        _record(mode=KillSwitchBoundaryMode.NO_NEW_POSITIONS.value)
    )
    assert evidence.no_new_positions is True
    assert apply_backtest_killswitch_exposure_gate_v0(1, evidence=evidence) == 0
    assert (
        apply_backtest_killswitch_exposure_gate_v0(
            1,
            evidence=evidence,
            has_existing_position=True,
        )
        == 1
    )


def test_cancel_pending_maps_to_cancel_pending_required_only_v0() -> None:
    evidence = evaluate_backtest_state_file_boundary_only_v0(
        _record(mode=KillSwitchBoundaryMode.CANCEL_PENDING.value)
    )
    assert evidence.cancel_pending_required is True
    assert evidence.reduce_to_flat_required is False
    assert evidence.emergency_flatten_required is False


def test_reduce_to_flat_maps_to_reduce_required_only_v0() -> None:
    evidence = evaluate_backtest_state_file_boundary_only_v0(
        _record(mode=KillSwitchBoundaryMode.REDUCE_TO_FLAT.value)
    )
    assert evidence.reduce_to_flat_required is True
    assert evidence.emergency_flatten_required is False


def test_emergency_flatten_maps_to_emergency_required_only_v0() -> None:
    evidence = evaluate_backtest_state_file_boundary_only_v0(
        _record(mode=KillSwitchBoundaryMode.EMERGENCY_FLATTEN.value)
    )
    assert evidence.emergency_flatten_required is True


def test_missing_state_file_input_fails_closed_v0() -> None:
    with pytest.raises(ValueError, match="killswitch_backtest_state_file_input_missing"):
        parse_killswitch_backtest_state_file_v0()


def test_corrupted_state_file_digest_fails_closed_v0() -> None:
    payload = _state_file_payload(mode=KillSwitchBoundaryMode.BLOCK_NEW.value)
    payload["state_file_digest_ref"] = "0" * 64
    with pytest.raises(ValueError, match="killswitch_backtest_state_file_digest_mismatch"):
        parse_killswitch_backtest_state_file_v0(payload=payload)


def test_invalid_mode_fails_closed_v0() -> None:
    payload = _state_file_payload(mode=KillSwitchBoundaryMode.BLOCK_NEW.value)
    payload["killswitch_boundary_mode"] = "not_a_mode"
    with pytest.raises(ValueError, match="killswitch_boundary_mode_invalid"):
        parse_killswitch_backtest_state_file_v0(payload=payload)


def test_backtest_binding_uses_surface_k_adapter_not_duplicate_semantics_v0() -> None:
    evidence = _base_evidence(decision_outcome=DecisionOutcome.ENTER_LONG.value)
    bound = bind_killswitch_boundary_backtest_state_file_evidence_v0(
        evidence,
        state_file=_record(mode=KillSwitchBoundaryMode.BLOCK_NEW.value),
    )
    assert (
        bound.surface_k_adapter_owner_ref
        == KILLSWITCH_BOUNDARY_OFFLINE_REPLAY_BINDING_ADAPTER_OWNER
    )
    assert bound.offline_binding.binding_applied is True


def test_non_authority_invariants_v0() -> None:
    evidence = evaluate_backtest_state_file_boundary_only_v0(
        _record(mode=KillSwitchBoundaryMode.EMERGENCY_FLATTEN.value)
    )
    assert evidence.runtime_authority is False
    assert evidence.orders_allowed is False
    assert evidence.credentials_used is False
    assert evidence.economic_evaluation is False
    assert backtest_state_file_binding_non_authority_ok_v0(evidence)


def test_parity_gap_assessment_surface_k_backtest_state_file_pass_v0() -> None:
    killswitch = next(item for item in parity_surface_assessments_v0() if item.surface_id == "K")
    assert killswitch.parity_status == "PASS"
    assert killswitch.missing_binding_if_any == ""
    assert "bind_killswitch_boundary_backtest_state_file_evidence_v0" in (
        killswitch.current_backtest_binding
    )
    assert NEXT_RECOMMENDED_SLICE == "BACKTEST_CANONICAL_ORDER_INTENT_WIRING_V0"


def test_mv2_research_wiring_binds_state_file_and_blocks_new_exposure_v0(tmp_path: Path) -> None:
    payload = _state_file_payload(mode=KillSwitchBoundaryMode.BLOCK_NEW.value)
    state_path = tmp_path / "killswitch_backtest_state.json"
    state_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    result = run_mv2_research_backtest_wiring_v1(
        _bars(n=6),
        strategy_id="ma_crossover",
        cfg=_cfg(),
        explicit_zero_cost_non_economic=True,
        killswitch_state_file_binding=KillSwitchBacktestStateFileBindingConfigV1(
            state_file_path=state_path,
            expected_state_file_digest_ref=str(payload["state_file_digest_ref"]),
        ),
    )
    assert result.bar_outcomes
    bound = [o for o in result.bar_outcomes if o.killswitch_backtest_state_file_evidence]
    assert len(bound) == len(result.bar_outcomes)
    sample = bound[0].killswitch_backtest_state_file_evidence
    assert sample is not None
    assert sample.killswitch_boundary_backtest_state_file_bound is True
    assert sample.killswitch_boundary_mode == KillSwitchBoundaryMode.BLOCK_NEW.value
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
