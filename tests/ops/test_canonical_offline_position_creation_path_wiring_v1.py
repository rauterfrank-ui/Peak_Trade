"""Canonical offline position-creation path wiring tests (R4 / no-wire)."""

from __future__ import annotations

import ast
from dataclasses import dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest

import src.governance.canonical_order_intent_v1 as intent_mod
import src.governance.capital_risk_sizing_v1 as sizing
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.action_identity_v1 import (
    compute_action_identity_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.composition_v1 import (
    AssembledCanonicalLineageV1,
    CanonicalOfflinePositionCreationPathInputV1,
    run_canonical_offline_position_creation_path_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.constants_v1 import (
    CANONICAL_INSTRUMENT_ID,
    ENDPOINT_SUBMIT,
    OWNER_GO as Z2DB_OWNER_GO,
    PRODUCTIVE_WIRE_REACHABLE,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.fixtures_v1 import (
    canonical_offline_boundary_fixture_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.lineage_assembler_v1 import (
    CanonicalLineageAssemblyInputV1,
    LineageAssemblyStatusV1,
    assemble_canonical_lineage_snapshot_v1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.models_v1 import (
    EvidenceFreshnessV1,
    PermissionDecisionV1,
    TransportOutcomeKindV1,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.path_wiring_constants_v1 import (
    HOST_GRAPH_ACTIVATION,
    LINEAGE_PROVENANCE_FIXTURE,
    LINEAGE_PROVENANCE_PRODUCTIVE,
    PATH_WIRING_OWNER_GO,
)
from src.ops.offline_execution_permission_and_position_creation_producer_wiring_v1.recording_transport_v1 import (
    OfflineRecordingTransportV1,
    RecordingTransportError,
)
from src.ops.wallclock_full_canonical_decision_to_simulated_economics_runtime_bridge_v1.intended_action_mapper_v1 import (
    IntendedAnalyticalActionV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    LIVE_ARMED,
    LIVE_AUTHORIZED,
    LIVE_ENABLED,
    SUBMIT_UNLOCKED,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    CanonicalTradingDecisionEvidenceV1,
)
from trading.master_v2.double_play_entry_exit_policy_v0 import (
    SafetyMode,
    TradingGate,
)
from trading.master_v2.safety_kernel_offline_replay_binding_adapter_v0 import (
    SafetyKernelOfflineReplayContextV0,
    bind_safety_kernel_offline_replay_evidence_v0,
)

PACKAGE_ROOT = Path(__file__).resolve().parents[2] / (
    "src/ops/offline_execution_permission_and_position_creation_producer_wiring_v1"
)
_FORBIDDEN_IMPORT_PREFIXES = ("requests", "httpx", "socket", "urllib", "aiohttp")
OTHER_INSTRUMENT = "ETH-USD-PERP"


def _evidence(
    *, intent_action: str = "ENTER_LONG", **overrides: object
) -> CanonicalTradingDecisionEvidenceV1:
    enter_long = intent_action == "ENTER_LONG"
    base: dict[str, object] = {
        "decision_id": "decision-offline-path-1",
        "replay_id": "replay-offline-path-1",
        "instrument_id": CANONICAL_INSTRUMENT_ID,
        "trading_epoch": 1,
        "market_context_ref": "ctx",
        "scope_initialization_ref": "init",
        "scope_event_ref": "evt",
        "bull_assessment_ref": "bull",
        "bear_assessment_ref": "bear",
        "state_switch_ref": "sw",
        "bull_survival_ref": "bs",
        "bear_survival_ref": "brs",
        "bull_suitability_ref": "bsu",
        "bear_suitability_ref": "brsu",
        "composition_result_ref": "comp",
        "entry_exit_policy_ref": "eep",
        "current_scope_ref": "cs",
        "next_scope_ref": "ns",
        "previous_direction_state": "neutral",
        "next_direction_state": "long_active" if enter_long else "short_active",
        "selected_side": "LONG" if enter_long else "SHORT",
        "selected_strategy_ref": "strat",
        "decision_outcome": "enter_long" if enter_long else "enter_short",
        "entry_or_exit_policy_ref": "eep",
        "reason_codes": (),
        "decision_precedence_trace": (),
        "component_versions": {},
        "policy_versions": {"capital_risk_sizing_policy_v1": "v1"},
        "config_digest": "cfg_digest_test",
        "implementation_digest": sizing.IMPLEMENTATION_DIGEST,
        "input_digest": "a" * 64,
        "semantic_digest": "",
        "execution_eligible": False,
        "adapter_compatible": False,
    }
    base.update(overrides)
    return CanonicalTradingDecisionEvidenceV1(**base)  # type: ignore[arg-type]


def _instrument() -> sizing.InstrumentQuantityConstraintsV1:
    return sizing.InstrumentQuantityConstraintsV1(
        instrument_id=CANONICAL_INSTRUMENT_ID,
        market_type="futures",
        contract_kind="LINEAR",
        contract_multiplier=Decimal("1"),
        lot_size=Decimal("1"),
        minimum_quantity=Decimal("1"),
        maximum_quantity=Decimal("100"),
        minimum_notional=Decimal("1"),
        tick_size=Decimal("0.0001"),
        instrument_metadata_version="sui_xperp_metadata_v1_test",
    )


def _policy() -> sizing.CapitalRiskSizingPolicyV1:
    return sizing.CapitalRiskSizingPolicyV1(
        policy_version="capital_risk_sizing_policy_v1",
        total_capital_limit_usd=Decimal("500"),
        order_limit_usd=Decimal("25"),
        daily_loss_limit_usd=Decimal("25"),
        max_positions=1,
    )


def _context(*, enter_long: bool = True) -> sizing.CapitalRiskSizingContextV1:
    price = Decimal("1.2345")
    stop = Decimal("1.1345") if enter_long else Decimal("1.3345")
    return sizing.CapitalRiskSizingContextV1(
        reference_price=price,
        protective_stop_price=stop,
        stop_distance=None,
        account_equity=Decimal("500"),
        already_committed_capital=Decimal("0"),
        daily_loss_consumed=Decimal("0"),
        current_reconciled_exposure=Decimal("0"),
        reconciled_open_position_quantity=Decimal("0"),
        current_open_positions_count=0,
        current_open_side=None,
        reconciliation_status="RECONCILED",
        configured_quantity_cap=Decimal("1"),
        leverage_ceiling=Decimal("5"),
        instrument=_instrument(),
        config_digest="b" * 64,
        order_notional_cap=Decimal("25"),
        per_trade_risk_cap=Decimal("25"),
    )


def _sizing_input(
    evidence: CanonicalTradingDecisionEvidenceV1,
    context: sizing.CapitalRiskSizingContextV1,
) -> sizing.CapitalRiskSizingInputV1:
    return sizing.CapitalRiskSizingInputV1(
        decision_id=evidence.decision_id,
        instrument_id=evidence.instrument_id,
        selected_side=evidence.selected_side,
        reference_price=context.reference_price,
        protective_stop_price=context.protective_stop_price,
        stop_distance=context.stop_distance,
        account_equity=context.account_equity,
        scope_capital_limit=Decimal("25"),
        per_trade_risk_limit=Decimal("25"),
        total_capital_limit=Decimal("500"),
        daily_loss_remaining_budget=Decimal("25"),
        current_reconciled_exposure=Decimal("0"),
        maximum_positions=1,
        current_open_positions_count=0,
        current_open_side=None,
        configured_quantity_cap=Decimal("1"),
        leverage_ceiling=Decimal("5"),
        reconciliation_status="RECONCILED",
        policy_version="capital_risk_sizing_policy_v1",
        config_digest="b" * 64,
        input_digest="a" * 64,
        instrument=context.instrument,
        decision_outcome=evidence.decision_outcome,
    )


def _decision_from_chain(
    chain: sizing.CapitalRiskSizingChainResultV1,
    *,
    selected_side: str,
) -> sizing.CapitalRiskSizingDecisionV1:
    return sizing.CapitalRiskSizingDecisionV1(
        outcome=chain.outcome,
        final_quantity=chain.final_quantity,
        selected_side=selected_side,
        scope_capital_envelope=chain.scope_capital_envelope,
        pre_sizing_risk=chain.pre_sizing_risk,
        canonical_position_sizing=chain.canonical_position_sizing,
        post_sizing_risk=chain.post_sizing_risk,
        quantity_provenance=chain.quantity_provenance,
        reason_codes=chain.reason_codes,
        authority_effect=chain.authority_effect,
        runtime_effect=chain.runtime_effect,
        adapter_compatible=chain.adapter_compatible,
    )


def _mapper_from_intent(
    intent: intent_mod.CanonicalOrderIntentV1,
    evidence: CanonicalTradingDecisionEvidenceV1,
) -> IntendedAnalyticalActionV1:
    side = "BUY" if intent.intent_action == "ENTER_LONG" else "SELL"
    return IntendedAnalyticalActionV1(
        intended_side=side,
        intended_quantity=intent.quantity,
        decision_outcome=str(evidence.decision_outcome),
        selected_side=str(evidence.selected_side).lower(),
        intent_action=intent.intent_action,
        quantity_source="canonical_order_intent",
        safety_blocked=False,
        reason_codes=tuple(intent.reason_codes),
    )


@dataclass(frozen=True)
class _TypedUpstream:
    evidence: CanonicalTradingDecisionEvidenceV1
    chain: sizing.CapitalRiskSizingChainResultV1
    safety: object
    intent: intent_mod.CanonicalOrderIntentV1
    mapper: IntendedAnalyticalActionV1


def _typed_entry(intent_action: str = "ENTER_LONG") -> _TypedUpstream:
    evidence = _evidence(intent_action=intent_action)
    context = _context(enter_long=intent_action == "ENTER_LONG")
    chain = sizing.evaluate_quantity_chain_v1(evidence, context, _policy())
    assert chain.outcome is sizing.CapitalRiskSizingOutcome.PASS
    assert chain.final_quantity > 0
    decision = _decision_from_chain(chain, selected_side=evidence.selected_side)
    build = intent_mod.build_canonical_order_intent_v1(
        intent_mod.CanonicalOrderIntentBuildInputV1(
            sizing_input=_sizing_input(evidence, context),
            sizing_decision=decision,
            intent_id="intent-offline-path-1",
            trading_epoch=str(evidence.trading_epoch),
            canonical_trading_logic_version="trading_logic_v1_test",
            intent_action=intent_action,
            policy_digest="policy_digest_test",
            order_type_policy="LIMIT_ONLY",
            price_policy="EXPLICIT_LIMIT",
            time_in_force_policy="GTC",
            max_slippage_policy="ZERO",
            expected_position_side=intent_mod.IntentSide.LONG.value
            if intent_action == "ENTER_LONG"
            else intent_mod.IntentSide.SHORT.value,
            current_reconciled_exposure=Decimal("0"),
            current_open_side=None,
        )
    )
    assert build.outcome is intent_mod.CanonicalOrderIntentBuildOutcome.PASS
    assert build.intent is not None
    safety = bind_safety_kernel_offline_replay_evidence_v0(
        evidence,
        context=SafetyKernelOfflineReplayContextV0(
            safety_mode=SafetyMode.NORMAL,
            trading_gate=TradingGate.ENTRY_ALLOWED,
        ),
    )
    mapper = _mapper_from_intent(build.intent, evidence)
    return _TypedUpstream(
        evidence=evidence,
        chain=chain,
        safety=safety,
        intent=build.intent,
        mapper=mapper,
    )


def _assembly_input(
    upstream: _TypedUpstream,
    **overrides: object,
) -> CanonicalLineageAssemblyInputV1:
    base: dict[str, object] = {
        "selection_instrument_id": upstream.evidence.instrument_id,
        "evidence": upstream.evidence,
        "risk_chain": upstream.chain,
        "safety_binding": upstream.safety,
        "intent": upstream.intent,
        "mapper_action": upstream.mapper,
        "cycle_index": 0,
        "live_send_allowed": False,
    }
    base.update(overrides)
    return CanonicalLineageAssemblyInputV1(**base)  # type: ignore[arg-type]


def _path_input(
    upstream: _TypedUpstream,
    *,
    owner_go: str = PATH_WIRING_OWNER_GO,
    **assembly_overrides: object,
) -> CanonicalOfflinePositionCreationPathInputV1:
    fixture = canonical_offline_boundary_fixture_v1()
    qty = format(upstream.intent.quantity, "f")
    prewire = replace(
        fixture.prewire,
        instrument_id=upstream.evidence.instrument_id,
        quantity=qty,
        limit_px="1.2345",
    )
    authority = replace(fixture.authority, owner_go=owner_go)
    return CanonicalOfflinePositionCreationPathInputV1(
        assembly=_assembly_input(upstream, **assembly_overrides),
        authority=authority,
        prewire=prewire,
    )


def _assert_no_live_flags(result: object) -> None:
    dumped = result.boundary.permission.to_dict()
    assert dumped["live_send_allowed"] is False
    assert dumped["productive_wire_reachable"] is False
    assert result.live_send_allowed is False
    assert result.productive_wire_reachable is False
    assert result.prerequisite_08_closed is False
    assert result.real_position_created is False
    assert result.venue_mutation_performed is False
    assert result.host_graph_activated is HOST_GRAPH_ACTIVATION
    assert LIVE_AUTHORIZED is False
    assert LIVE_ENABLED is False
    assert LIVE_ARMED is False
    assert SUBMIT_UNLOCKED is False
    assert PRODUCTIVE_WIRE_REACHABLE is False


def test_proof_c_enter_long_full_offline_graph() -> None:
    upstream = _typed_entry("ENTER_LONG")
    result = run_canonical_offline_position_creation_path_v1(_path_input(upstream))
    assert result.assembly.status is LineageAssemblyStatusV1.PASS
    assert result.assembly.provenance == LINEAGE_PROVENANCE_PRODUCTIVE
    assert result.boundary.permission.decision is PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY
    assert result.boundary.request_candidate is not None
    assert result.boundary.transport_record is not None
    assert result.boundary.transport_record.outcome is TransportOutcomeKindV1.RECORDED
    assert result.boundary.transport_record.network_call_performed is False
    assert result.boundary.request_candidate.side == "buy"
    assert result.boundary.request_candidate.endpoint == ENDPOINT_SUBMIT
    assert "reduceOnly" not in result.boundary.request_candidate.venue_native_body
    assert result.boundary.request_candidate.venue_native_body["tdMode"] == "cross"
    assert result.boundary.request_candidate.venue_native_body["ordType"] == "limit"
    _assert_no_live_flags(result)


def test_proof_d_enter_short_full_offline_graph() -> None:
    upstream = _typed_entry("ENTER_SHORT")
    result = run_canonical_offline_position_creation_path_v1(_path_input(upstream))
    assert result.assembly.status is LineageAssemblyStatusV1.PASS
    assert result.boundary.request_candidate is not None
    assert result.boundary.request_candidate.side == "sell"
    assert result.boundary.transport_record is not None
    assert result.boundary.transport_record.outcome is TransportOutcomeKindV1.RECORDED
    _assert_no_live_flags(result)


def test_proof_a_lineage_to_request_candidate() -> None:
    upstream = _typed_entry("ENTER_LONG")
    assembled = assemble_canonical_lineage_snapshot_v1(_assembly_input(upstream))
    assert assembled.status is LineageAssemblyStatusV1.PASS
    assert assembled.lineage is not None
    result = run_canonical_offline_position_creation_path_v1(_path_input(upstream))
    assert result.boundary.request_candidate is not None
    assert result.boundary.request_candidate.plan_digest == assembled.lineage.plan_digest


def test_proof_b_candidate_records_not_sent() -> None:
    transport = OfflineRecordingTransportV1()
    result = run_canonical_offline_position_creation_path_v1(
        _path_input(_typed_entry("ENTER_LONG")),
        transport=transport,
    )
    assert result.boundary.transport_record is not None
    assert result.boundary.transport_record.outcome is TransportOutcomeKindV1.RECORDED
    assert result.boundary.transport_record.network_call_performed is False
    assert result.boundary.transport_record.secret_materialized is False
    assert transport.PRODUCTIVE_WIRE_REACHABLE is False
    assert transport.wire_send_enabled is False


def test_proof_e_hold_and_exit_cannot_reach_request() -> None:
    upstream = _typed_entry("ENTER_LONG")
    hold_evidence = replace(upstream.evidence, decision_outcome="hold", selected_side="LONG")
    hold_result = run_canonical_offline_position_creation_path_v1(
        _path_input(upstream, evidence=hold_evidence, intent=None, mapper_action=None)
    )
    assert hold_result.boundary.request_candidate is None
    assert "HOLD" in hold_result.assembly.reason_codes
    exit_evidence = replace(upstream.evidence, decision_outcome="exit")
    exit_intent = replace(upstream.intent, intent_action="EXIT")
    exit_result = run_canonical_offline_position_creation_path_v1(
        _path_input(upstream, evidence=exit_evidence, intent=exit_intent)
    )
    assert exit_result.boundary.request_candidate is None
    assert "EXIT" in exit_result.assembly.reason_codes


def test_proof_f_no_authorized_or_live_flags_true() -> None:
    result = run_canonical_offline_position_creation_path_v1(
        _path_input(_typed_entry("ENTER_LONG"))
    )
    _assert_no_live_flags(result)
    assert result.boundary.permission.live_send_allowed is False


def test_proof_g_no_network_capable_transport() -> None:
    hits: list[str] = []
    for path in sorted(PACKAGE_ROOT.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split(".", 1)[0] in _FORBIDDEN_IMPORT_PREFIXES:
                        hits.append(f"{path.name}:import:{alias.name}")
            elif isinstance(node, ast.ImportFrom):
                mod = node.module or ""
                if mod.split(".", 1)[0] in _FORBIDDEN_IMPORT_PREFIXES:
                    hits.append(f"{path.name}:from:{mod}")
    assert hits == []


def test_proof_h_venue_native_body_omits_reduce_only() -> None:
    result = run_canonical_offline_position_creation_path_v1(
        _path_input(_typed_entry("ENTER_LONG"))
    )
    candidate = result.boundary.request_candidate
    assert candidate is not None
    assert candidate.reduce_only is False
    assert "reduceOnly" not in candidate.venue_native_body
    assert candidate.venue_native_body["instId"] == CANONICAL_INSTRUMENT_ID


def test_same_input_same_output() -> None:
    payload = _path_input(_typed_entry("ENTER_LONG"))
    first = run_canonical_offline_position_creation_path_v1(payload)
    second = run_canonical_offline_position_creation_path_v1(payload)
    assert first.assembly.lineage == second.assembly.lineage
    assert first.boundary.request_candidate == second.boundary.request_candidate
    assert first.assembly.assembled is not None
    assert first.assembly.assembled.assembly_digest == second.assembly.assembled.assembly_digest


def test_canonical_serialization_and_identity_stable() -> None:
    lineage = assemble_canonical_lineage_snapshot_v1(
        _assembly_input(_typed_entry("ENTER_LONG"))
    ).lineage
    assert lineage is not None
    first = compute_action_identity_v1(lineage)
    second = compute_action_identity_v1(lineage)
    assert first.action_identity == second.action_identity
    assert first.client_order_id == second.client_order_id


def test_lineage_hash_changes_when_semantic_input_changes() -> None:
    upstream = _typed_entry("ENTER_LONG")
    first = assemble_canonical_lineage_snapshot_v1(_assembly_input(upstream))
    changed = replace(upstream.evidence, decision_id="decision-offline-path-2")
    intent = replace(upstream.intent, decision_id="decision-offline-path-2")
    safety = replace(
        upstream.safety,
        evidence=replace(upstream.safety.evidence, decision_id="decision-offline-path-2"),
    )
    second = assemble_canonical_lineage_snapshot_v1(
        _assembly_input(upstream, evidence=changed, intent=intent, safety_binding=safety)
    )
    assert first.assembled is not None
    assert second.assembled is not None
    assert first.assembled.assembly_digest != second.assembled.assembly_digest
    assert compute_action_identity_v1(first.lineage).action_identity != compute_action_identity_v1(
        second.lineage
    )


def test_fixture_lineage_cannot_masquerade_as_productive() -> None:
    fixture = canonical_offline_boundary_fixture_v1()
    forged = AssembledCanonicalLineageV1(
        lineage=fixture.lineage,
        provenance=LINEAGE_PROVENANCE_FIXTURE,
        assembly_digest="0" * 64,
        assembler_id="fixtures_v1",
        assembler_contract_version="v1",
        quantity_unit="CONTRACTS",
    )
    result = run_canonical_offline_position_creation_path_v1(
        _path_input(_typed_entry("ENTER_LONG")),
        assembled_override=forged,
    )
    assert result.assembly.status is LineageAssemblyStatusV1.HALT
    assert "FIXTURE_LINEAGE_NOT_PRODUCTIVE" in result.assembly.reason_codes
    assert result.boundary.request_candidate is None


def test_missing_decision_id() -> None:
    upstream = _typed_entry("ENTER_LONG")
    evidence = replace(upstream.evidence, decision_id="")
    result = assemble_canonical_lineage_snapshot_v1(_assembly_input(upstream, evidence=evidence))
    assert result.status is LineageAssemblyStatusV1.DENY
    assert "MISSING_DECISION_ID" in result.reason_codes
    assert result.lineage is None


def test_instrument_and_selection_mismatch() -> None:
    upstream = _typed_entry("ENTER_LONG")
    result = assemble_canonical_lineage_snapshot_v1(
        _assembly_input(upstream, selection_instrument_id=OTHER_INSTRUMENT)
    )
    assert "SELECTION_BINDING_MISMATCH" in result.reason_codes
    intent = replace(upstream.intent, instrument_id=OTHER_INSTRUMENT)
    mismatch = assemble_canonical_lineage_snapshot_v1(_assembly_input(upstream, intent=intent))
    assert "INSTRUMENT_MISMATCH" in mismatch.reason_codes


def test_risk_not_pass() -> None:
    upstream = _typed_entry("ENTER_LONG")
    blocked = replace(upstream.chain, outcome=sizing.CapitalRiskSizingOutcome.BLOCKED)
    result = assemble_canonical_lineage_snapshot_v1(_assembly_input(upstream, risk_chain=blocked))
    assert result.status is LineageAssemblyStatusV1.DENY
    assert "RISK_FAIL" in result.reason_codes


def test_safety_blocked() -> None:
    upstream = _typed_entry("ENTER_LONG")
    blocked = bind_safety_kernel_offline_replay_evidence_v0(
        upstream.evidence,
        context=SafetyKernelOfflineReplayContextV0(killswitch_blocked=True),
    )
    result = assemble_canonical_lineage_snapshot_v1(
        _assembly_input(upstream, safety_binding=blocked)
    )
    assert "SAFETY_FAIL" in result.reason_codes
    assert result.lineage is None


def test_plan_and_mapper_missing() -> None:
    upstream = _typed_entry("ENTER_LONG")
    plan = assemble_canonical_lineage_snapshot_v1(_assembly_input(upstream, intent=None))
    assert "PLAN_MISSING" in plan.reason_codes
    mapper = assemble_canonical_lineage_snapshot_v1(_assembly_input(upstream, mapper_action=None))
    assert "MAPPER_MISSING" in mapper.reason_codes


def test_mapper_side_and_qty_mismatch() -> None:
    upstream = _typed_entry("ENTER_LONG")
    side = replace(upstream.mapper, intended_side="SELL")
    side_result = assemble_canonical_lineage_snapshot_v1(
        _assembly_input(upstream, mapper_action=side)
    )
    assert "MAPPER_SIDE_MISMATCH" in side_result.reason_codes
    qty = replace(upstream.mapper, intended_quantity=Decimal("99"))
    qty_result = assemble_canonical_lineage_snapshot_v1(
        _assembly_input(upstream, mapper_action=qty)
    )
    assert "MAPPER_QTY_MISMATCH" in qty_result.reason_codes


def test_qty_zero_and_invalid() -> None:
    upstream = _typed_entry("ENTER_LONG")
    zero = replace(upstream.intent, quantity=Decimal("0"))
    zero_result = assemble_canonical_lineage_snapshot_v1(_assembly_input(upstream, intent=zero))
    assert "ZERO_QTY" in zero_result.reason_codes
    invalid = replace(upstream.intent, quantity=Decimal("NaN"))
    invalid_result = assemble_canonical_lineage_snapshot_v1(
        _assembly_input(upstream, intent=invalid)
    )
    assert "QTY_INVALID" in invalid_result.reason_codes


def test_prewire_qty_mismatch_and_stale() -> None:
    upstream = _typed_entry("ENTER_LONG")
    payload = _path_input(upstream)
    qty_mismatch = CanonicalOfflinePositionCreationPathInputV1(
        assembly=payload.assembly,
        authority=payload.authority,
        prewire=replace(payload.prewire, quantity="99"),
    )
    qty_result = run_canonical_offline_position_creation_path_v1(qty_mismatch)
    assert qty_result.boundary.request_candidate is None
    assert (
        qty_result.boundary.permission.decision
        is not PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY
    )
    stale = CanonicalOfflinePositionCreationPathInputV1(
        assembly=payload.assembly,
        authority=payload.authority,
        prewire=replace(payload.prewire, freshness_status=EvidenceFreshnessV1.STALE),
    )
    stale_result = run_canonical_offline_position_creation_path_v1(stale)
    assert stale_result.boundary.request_candidate is None
    assert "PREWIRE_EVIDENCE_STALE" in stale_result.boundary.permission.reason_codes


def test_plan_only_invariants_cannot_unlock_submit() -> None:
    upstream = _typed_entry("ENTER_LONG")
    eligible = assemble_canonical_lineage_snapshot_v1(
        _assembly_input(upstream, intent=replace(upstream.intent, execution_eligible=True))
    )
    assert eligible.status is LineageAssemblyStatusV1.HALT
    assert "PLAN_EXECUTION_ELIGIBLE" in eligible.reason_codes
    authorized = assemble_canonical_lineage_snapshot_v1(
        _assembly_input(upstream, intent=replace(upstream.intent, submission_authorized=True))
    )
    assert authorized.status is LineageAssemblyStatusV1.HALT
    assert "PLAN_SUBMISSION_AUTHORIZED" in authorized.reason_codes
    live = assemble_canonical_lineage_snapshot_v1(_assembly_input(upstream, live_send_allowed=True))
    assert live.status is LineageAssemblyStatusV1.HALT
    assert "LIVE_SEND_ALLOWED" in live.reason_codes
    assert eligible.lineage is None
    assert authorized.lineage is None
    assert live.lineage is None


def test_productive_recording_transport_cannot_be_activated() -> None:
    with pytest.raises(RecordingTransportError, match="WIRE_FENCE_IMMUTABLE"):
        OfflineRecordingTransportV1(PRODUCTIVE_WIRE_ENABLED=True)
    with pytest.raises(RecordingTransportError, match="WIRE_FENCE_IMMUTABLE"):
        OfflineRecordingTransportV1(wire_send_enabled=True)
    transport = OfflineRecordingTransportV1()
    with pytest.raises(RecordingTransportError, match="WIRE_FENCE_IMMUTABLE"):
        transport.PRODUCTIVE_WIRE_REACHABLE = True


def test_unsupported_order_type_and_tdmode_and_endpoint() -> None:
    upstream = _typed_entry("ENTER_LONG")
    payload = _path_input(upstream)
    market = CanonicalOfflinePositionCreationPathInputV1(
        assembly=payload.assembly,
        authority=payload.authority,
        prewire=replace(payload.prewire, order_type="market"),
    )
    market_result = run_canonical_offline_position_creation_path_v1(market)
    assert market_result.boundary.request_candidate is None
    isolated = CanonicalOfflinePositionCreationPathInputV1(
        assembly=payload.assembly,
        authority=payload.authority,
        prewire=replace(payload.prewire, td_mode="isolated"),
    )
    isolated_result = run_canonical_offline_position_creation_path_v1(isolated)
    assert isolated_result.boundary.request_candidate is None
    happy = run_canonical_offline_position_creation_path_v1(payload)
    assert happy.boundary.request_candidate is not None
    assert happy.boundary.request_candidate.endpoint == "/api/v5/trade/order"


def test_target_instrument_mismatch_fail_closed() -> None:
    upstream = _typed_entry("ENTER_LONG")
    evidence = replace(upstream.evidence, instrument_id=OTHER_INSTRUMENT)
    intent = replace(upstream.intent, instrument_id=OTHER_INSTRUMENT)
    result = run_canonical_offline_position_creation_path_v1(
        _path_input(
            upstream,
            selection_instrument_id=OTHER_INSTRUMENT,
            evidence=evidence,
            intent=intent,
        )
    )
    assert result.boundary.request_candidate is None
    assert (
        result.boundary.permission.decision is not PermissionDecisionV1.GRANT_FOR_NON_LIVE_BOUNDARY
    )


def test_z2db_owner_go_and_wiring_go_both_compose() -> None:
    upstream = _typed_entry("ENTER_LONG")
    wiring = run_canonical_offline_position_creation_path_v1(
        _path_input(upstream, owner_go=PATH_WIRING_OWNER_GO)
    )
    z2db = run_canonical_offline_position_creation_path_v1(
        _path_input(upstream, owner_go=Z2DB_OWNER_GO)
    )
    assert wiring.boundary.request_candidate is not None
    assert z2db.boundary.request_candidate is not None
    unknown = run_canonical_offline_position_creation_path_v1(
        _path_input(upstream, owner_go="PEAK_TRADE_OWNER_GO_UNKNOWN")
    )
    assert unknown.boundary.request_candidate is None
    assert "OWNER_GO_MISMATCH" in unknown.assembly.reason_codes


def test_assembled_lineage_never_sets_submit_flags() -> None:
    assembled = assemble_canonical_lineage_snapshot_v1(_assembly_input(_typed_entry("ENTER_LONG")))
    assert assembled.lineage is not None
    assert assembled.lineage.plan_execution_eligible is False
    assert assembled.lineage.plan_adapter_compatible is False
    assert assembled.lineage.plan_submission_authorized is False
    assert assembled.lineage.safety_hard_blocked is False
