"""Original 29Q/venue-plan handoff for a source-bound BTC Demo reservation.

Plan construction only. No permit, submit attempt, signer or transport.
The Core parent and market decision stay unchanged; the canonical producers
bind the actual reserved sizing children before the original composition.
"""

from dataclasses import replace
from datetime import datetime, timezone
import json

from src.governance.canonical_order_intent_v1 import (
    CanonicalOrderIntentBuildInputV1,
    build_canonical_order_intent_v1,
    compute_quantity_provenance_ref,
)
from src.ops.btc_demo_budget_owner_v3 import BtcDemoBudgetOwnerV3
from src.ops import btc_demo_lane3_v2 as demo
from src.ops.portfolio_capital_reservation_budget_v1.durable_store_v1 import digest
from src.ops.full_core_live_path_composition_root_v1 import pretrade_acquisition_v1
from src.ops.full_core_live_path_composition_root_v1.current_productive_venue_plan_v1 import (
    try_bind_current_productive_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.final_order_envelope_v1 import (
    bind_final_order_envelope_from_venue_plan_v1,
)
from src.ops.full_core_live_path_composition_root_v1.natural_enter_cross_session_outcome_closure_v1.retention_v1 import (
    exclusive_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.sizing_binding_v1 import (
    ReservationSizingBindingV1,
)
from trading.master_v2.capital_risk_sizing_offline_replay_binding_adapter_v0 import (
    RISK_SIZING_EFFECT_BOUND_OFFLINE,
    compute_risk_sizing_decision_ref_v0,
)
from trading.master_v2.canonical_core_runtime_integration_intent_pipeline_bridge_v0 import (
    map_decision_outcome_to_intent_action,
)
from trading.master_v2.canonical_order_intent_offline_replay_binding_adapter_v0 import (
    ORDER_INTENT_EFFECT_BOUND_OFFLINE,
    _DEFAULT_ORDER_TYPE_POLICY,
    _DEFAULT_PRICE_POLICY,
    _DEFAULT_TIME_IN_FORCE_POLICY,
    _DEFAULT_MAX_SLIPPAGE_POLICY,
    _DEFAULT_CANONICAL_TRADING_LOGIC_VERSION,
)
from trading.master_v2.canonical_trading_decision_evidence_v1 import (
    finalize_offline_replay_decision_evidence_v1,
)


def _need(condition, reason):
    if not condition:
        raise ValueError(reason)


def prepare_btc_demo_entry_plan_v1(host, *, entry, reservation_id, expected_revision, clock):
    owner = host.budget.owner
    _need(type(owner) is BtcDemoBudgetOwnerV3, "BTC_DEMO_PLAN_V3_TESTNET_OWNER_REQUIRED")
    with exclusive_v1(host.cursor_root / "first_entry_mark_v2.lock"), owner._lock:
        cycle = host._original_entry_cycle(entry)
        _need(
            host.budget.budget_revision_ref_v1() == expected_revision,
            "BTC_DEMO_PLAN_BUDGET_HEAD_CHANGED",
        )
        state = owner.risk_snapshot_v1()["state"]
        holds = [r for r in state["reservations"] if r["reservation_id"] == reservation_id]
        _need(len(holds) == 1, "BTC_DEMO_PLAN_ORIGINAL_HOLD_REQUIRED")
        hold = holds[0]
        _need(
            hold["state"] in {"RESERVED", "COMMITTED"}
            and hold["decision_id"] == cycle.replay.evidence.decision_id
            and hold["cycle_id"] == cycle.cycle_id
            and hold["slot_id"] == "LANE_3"
            and reservation_id not in state["execution_links"],
            "BTC_DEMO_PLAN_ORIGINAL_HOLD_REQUIRED",
        )
        sizing = ReservationSizingBindingV1.from_dict_v1(state["sizing_bindings"][reservation_id])
        _need(
            sizing.offline_testnet_source_digest is None
            and sizing.monetary_source is not None
            and sizing.monetary_source.contract_settlement_sources_json,
            "BTC_DEMO_PLAN_ORIGINAL_DEMO_SOURCES_REQUIRED",
        )
        now = datetime.fromtimestamp(clock(), timezone.utc).isoformat()
        source_checksum = sizing.applied_input.config_digest
        source_path = (
            demo._demo_lane_root(host.budget.root)
            / "entry-reservation-sources"
            / (source_checksum + ".json")
        )
        _need(source_path.resolve() == source_path, "BTC_DEMO_PLAN_SOURCE_PATH_INVALID")
        packet = json.loads(source_path.read_bytes())
        _need(
            digest(packet) == source_checksum
            and packet["decision_id"] == hold["decision_id"]
            and packet["cycle_id"] == hold["cycle_id"]
            and packet["bound"] == host.budget.bound.to_dict()
            and packet["execution_environment"] == "TESTNET",
            "BTC_DEMO_PLAN_ORIGINAL_SOURCE_MISMATCH",
        )
        for source in packet["sources"].values():
            pretrade_acquisition_v1.acquisition_age_seconds_v1(
                acquired_at_utc=source["acquired_at_utc"], now_utc=now
            )
        parent = cycle.replay.evidence
        intent_build = build_canonical_order_intent_v1(
            CanonicalOrderIntentBuildInputV1(
                sizing_input=sizing.applied_input,
                sizing_decision=sizing.decision,
                intent_id="intent-" + parent.decision_id,
                trading_epoch=str(parent.trading_epoch),
                canonical_trading_logic_version=_DEFAULT_CANONICAL_TRADING_LOGIC_VERSION,
                intent_action=map_decision_outcome_to_intent_action(parent.decision_outcome),
                policy_digest=owner.entry_budget_policy_v1().digest_v1(),
                order_type_policy=_DEFAULT_ORDER_TYPE_POLICY,
                price_policy=_DEFAULT_PRICE_POLICY,
                time_in_force_policy=_DEFAULT_TIME_IN_FORCE_POLICY,
                max_slippage_policy=_DEFAULT_MAX_SLIPPAGE_POLICY,
                expected_position_side=sizing.applied_input.selected_side,
                current_reconciled_exposure=sizing.applied_input.current_reconciled_exposure,
                current_open_side=sizing.applied_input.current_open_side,
            )
        )
        intent = intent_build.intent
        _need(
            intent is not None,
            "BTC_DEMO_CANONICAL_29Q_REQUIRED:" + ",".join(intent_build.reason_codes),
        )
        # Only financial child references are attached to the same Core decision.
        # The original finalizer hashes this body; composition revalidates it.
        financial_parent = finalize_offline_replay_decision_evidence_v1(
            replace(
                parent,
                quantity_status=sizing.decision.quantity_provenance.final_quantity_status.value,
                quantity_provenance_ref=compute_quantity_provenance_ref(
                    sizing.decision.quantity_provenance
                ),
                risk_sizing_ref=compute_risk_sizing_decision_ref_v0(sizing.decision),
                risk_sizing_effect=RISK_SIZING_EFFECT_BOUND_OFFLINE,
                order_intent_ref=intent.semantic_digest,
                order_intent_effect=ORDER_INTENT_EFFECT_BOUND_OFFLINE,
            )
        )
        replay = replace(
            cycle.replay,
            evidence=financial_parent,
            intermediate=replace(
                cycle.replay.intermediate,
                capital_risk_sizing_decision=sizing.decision,
                canonical_order_intent=intent,
                capital_risk_mode="TESTNET_ACCOUNT_BOUND",
            ),
            capital_risk_mode="TESTNET_ACCOUNT_BOUND",
        )
        status, reasons, plan = try_bind_current_productive_venue_plan_v1(
            replay=replay,
            bound_instrument=host.budget.bound,
            session_id=host.writer_session_id,
            run_id=cycle.cycle_id,
            composed_epoch=now,
            execution_mode="TESTNET",
        )
        _need(
            status.value == "PASS" and plan is not None,
            "BTC_DEMO_VENUE_PLAN_REQUIRED:" + ",".join(reasons),
        )
        envelope = bind_final_order_envelope_from_venue_plan_v1(
            plan,
            admission_ref="btc-demo-reservation:" + reservation_id,
            provenance_ref="btc-demo-sources:" + sizing.applied_input.config_digest,
            creation_epoch=now,
        )
        finished = datetime.fromtimestamp(clock(), timezone.utc).isoformat()
        pretrade_acquisition_v1.acquisition_age_seconds_v1(acquired_at_utc=now, now_utc=finished)
        for source in packet["sources"].values():
            pretrade_acquisition_v1.acquisition_age_seconds_v1(
                acquired_at_utc=source["acquired_at_utc"], now_utc=finished
            )
        if hold["state"] == "RESERVED":
            committed = owner.commit_internal_pre_external_effect_v1(reservation_id)
            _need(committed.disposition.value == "ADMITTED", "BTC_DEMO_PLAN_COMMIT_REQUIRED")
        owner.bind_execution_plan_v1(
            reservation_id,
            envelope,
            canonical_intent=intent,
            venue_plan=plan,
            core_parent=financial_parent,
            core_cursor_root=host.cursor_root,
            entry_frame_required=True,
        )
        return envelope, owner.execution_plan_context_v1(reservation_id, envelope)
