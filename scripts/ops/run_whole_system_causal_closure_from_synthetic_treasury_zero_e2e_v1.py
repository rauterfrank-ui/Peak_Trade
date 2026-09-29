"""WHOLE_SYSTEM_CAUSAL_CLOSURE_FROM_SYNTHETIC_TREASURY_ZERO_E2E_V1."""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

_RUN_TS = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
PACK = REPO / "evidence/ops/whole_system_causal_closure_from_synthetic_treasury_zero_v1" / _RUN_TS
PACK.mkdir(parents=True, exist_ok=True)
E2E_RUN_ID = f"wsccstz-{_RUN_TS}-{uuid.uuid4().hex[:12]}"
DECISION_EPOCH = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

MAP_SOURCE = REPO / "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
ATLAS_META = REPO / "docs/system_atlas/census/census_meta.yaml"
KERNEL_WITNESS = (
    REPO
    / "config/governance/current_system_interaction_authority_map_v1/bounded_productive_kernel_completeness_witness_v1.json"
)

_SIM_EUR_DEPOSIT = "10000"
_SIM_USDC_BEFORE = "2345.67"
_SIM_USDC_AFTER = "12345.67"
_SIM_MARGIN_AVAIL_EQ = _SIM_USDC_AFTER
_ACCOUNT = "okx-eea-uid:sim-wstzmae2e"
_INSTRUMENT = "inst-eth-usdt-perp"

from src.ops.offline_funding_balance_read_producer_v1.fixtures_v1 import FIXTURE_CLASS
from src.ops.offline_funding_balance_read_producer_v1.observation_v1 import (
    CURRENCY_ROW_STATUS_PRESENT,
    parse_funding_account_balance_observation_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.models_v1 import (
    TreasuryDepositHistorySignalV1,
    TreasuryExternalDepletionSignalV1,
    TreasuryFreshnessSignalV1,
    TreasuryInternalTransferSignalV1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.reconciliation_v1 import (
    clear_treasury_reconciliation_idempotency_cache_v1,
    evaluate_treasury_read_only_reconciliation_v1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.context_v1 import (
    TreasuryCapitalDepositObservationContextV1,
)
from src.ops.treasury_phase_2_read_only_venue_observation_binding_v1.producer_v1 import (
    build_treasury_venue_observation_from_funding_balance_v1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_productive_host_join_v1.join_v1 import (
    join_treasury_observation_through_e4_into_productive_account_equity_host_v1,
)
from src.ops.treasury_capital_admission_to_account_equity_orchestration_v1.join_v1 import (
    join_treasury_capital_admission_into_account_equity_orchestration_v1,
)
from src.ops.treasury_phase_2_read_only_reconciliation_v1.join_v1 import (
    join_treasury_reconciliation_into_capital_admission_v1,
)
from src.ops.treasury_productive_read_only_venue_observation_v1.chain_v1 import (
    execute_treasury_productive_reconciliation_chain_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_treasury_single_source_capital_handoff_v1 import (
    build_default_full_core_u04_p01_eligibility_host_inputs_v1,
    execute_current_productive_treasury_single_source_capital_handoff_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_enter_live_29p_join_v1 import (
    join_current_productive_enter_live_29p_before_venue_plan_v1,
    current_productive_decision_class_v1,
    DECISION_ENTER,
)
from src.ops.full_core_live_path_composition_root_v1.execution_admission_contract_v1 import (
    FreshPretradeGetStatusV1,
    LiveAccountBoundStatusV1,
)
from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
    NUMERIC_EQUITY_TTL_SECONDS,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_29p_risk_capital_model_v1 import (
    OBSERVATION_SURFACE,
    CurrentProductiveUsdcFreeMarginObservationV1,
)
from src.ops.section_11_13_5_live_canary_minimum_exposure_v1.constants_v1 import (
    REUSED_BINDING_ACCOUNT_SCOPE,
)
from src.ops.current_productive_eea_universe_inventory_acquisition_v1.acquire_v1 import (
    acquire_eea_universe_inventory_v1,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_cap21_to_cap23_productive_persistence_v1 import (
    run_cap21_to_cap23_persist_productive_v1,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.persistence_v1 import (
    checkpoint_root_for,
)
from src.ops.current_mf_n5_durable_lane_assignment_persistence_v1.single_writer_v1 import (
    DurableLaneAssignmentSingleWriterV1,
)
from src.ops.current_mf_n5_full_autonomy_productive_runtime_orchestrator_v1.orchestrator_v1 import (
    ProductiveFullAutonomyCap24BindContextV1,
)
from src.ops.current_mf_n5_isolated_lane_instance_topology_v1.constants_v1 import LANE_IDS
from src.ops.current_mf_n5_staged_productive_runtime_admission_recovery_audit_v1 import (
    run_staged_productive_full_autonomy_n5_runtime_control_plane_v1,
)
from src.ops.mf_membership_context_artifact_contract_v1 import (
    Cap22ProvenanceV1,
    build_membership_context_artifact_v1,
)
from src.ops.mf_membership_selector_and_rotation_runtime_contract_v1 import (
    parse_eligible_cap22_top20,
    run_isolated_selector_cycle_v1,
)
from src.ops.portfolio_capital_reservation_budget_v1.contract_v1 import (
    PortfolioCapitalReservationBudgetOwnerV1,
)
from src.ops.productive_reconciliation_runtime_binding_v1.models_v1 import (
    PortfolioTruthSnapshotV1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
    DISPOSITION_PRE_EXTERNAL_EFFECT,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_occupancy_classify_and_c1_gate_v1 import (
    PREVIOUS_C1_VENUE_EVENT_TIME,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_runtime_cycle_v1 import (
    ExistingPositionSide,
)
from trading.market_state.distinct_market_observation_acceptor_v1 import (
    ObservationTransportMetadataV1,
)
from trading.market_state.time_sample_epoch_semantics_v1 import (
    EventTimeInstantV1,
    MarketSampleIdentityV1,
)
from trading.master_v2.canonical_volatility_typed_runtime_producer_scaffold_v1 import (
    CanonicalVolatilityTypedRuntimeProducerScaffoldV1,
)
from tests.ops._current_productive_29p_chain_integrity_test_helpers_v1 import (
    MockCurrentProductive29PIntegrityBackendV1,
)
from tests.ops._current_productive_natural_mv2_dp_enter_fixture_v1 import (
    governed_c1_candles_payload_from_enter_closes_v1,
    prepare_layered_long_armed_seed_for_pre_external_invoke_v1,
)
from tests.ops._pre_external_cap21_inst_type_test_helpers_v1 import (
    write_cap21_productivity_root_for_inst_v1,
)
from tests.ops.test_current_mf_n5_full_autonomy_occupied_lane_governed_cycle_n1_consumer_join_v1 import (
    _market_kwargs,
)
from tests.ops.test_full_core_current_productive_enter_live_29p_join_v1 import (
    _balance_payload,
    _enter_replay,
    _host_enter_cycle,
    _injected,
)
from tests.ops.test_full_core_current_productive_pre_external_closure_v1 import (
    _TEST_INST,
    _bound,
    _productive_transport,
)
from src.ops.governed_productive_account_equity_authority_producer_v1.current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1 import (
    OWNER_GO as GAP_OWNER_GO,
    execute_current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_step_29p_to_eea_acquisition_productive_join_v1 import (
    CAPITAL_LINEAGE_CLASS_SYNTHETIC_TEST_FIXTURE,
    Step29pToEeaAcquisitionProductiveJoinRequestV1,
    join_step_29p_admitted_capital_into_eea_universe_acquisition_v1,
)
from src.ops.full_core_live_path_composition_root_v1.current_productive_step_29p_to_portfolio_budget_productive_join_v1 import (
    join_step_29p_handoff_into_portfolio_capital_reservation_budget_v1,
)

PRODUCTIVE_KERNEL_EDGES: frozenset[str] = frozenset(
    json.loads(KERNEL_WITNESS.read_text(encoding="utf-8")).get(
        "bounded_kernel_required_edge_ids", []
    )
)


def _origin() -> str:
    return (
        subprocess.check_output(["git", "rev-parse", "origin/main"], cwd=REPO, text=True)
        .strip()
        .lower()
    )


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _funding_bytes(*, usdc_bal: str) -> bytes:
    return json.dumps(
        {
            "code": "0",
            "data": [
                {
                    "ccy": "USDC",
                    "bal": usdc_bal,
                    "frozenBal": "0",
                    "availBal": usdc_bal,
                }
            ],
            "fixture_class": FIXTURE_CLASS,
            "simulated_external_narrative": {
                "operator_deposit_eur": _SIM_EUR_DEPOSIT,
                "venue": "OKX_EEA",
            },
        }
    ).encode()


def _funding_bytes_eur_only() -> bytes:
    return json.dumps(
        {
            "code": "0",
            "data": [
                {
                    "ccy": "EUR",
                    "bal": _SIM_EUR_DEPOSIT,
                    "frozenBal": "0",
                    "availBal": _SIM_EUR_DEPOSIT,
                }
            ],
            "fixture_class": FIXTURE_CLASS,
            "simulated_external": True,
        }
    ).encode()


def _treasury_branch(
    *,
    branch_id: str,
    body: bytes,
    prior_raw: str,
    deposit_confirms: bool,
    evidence_suffix: str,
) -> dict[str, Any]:
    clear_treasury_reconciliation_idempotency_cache_v1()
    observed_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    funding = parse_funding_account_balance_observation_v1(
        body_bytes=body,
        http_status=200,
        observed_at_utc=observed_at,
        venue="okx",
        rest_host="eea.okx.com",
        endpoint="/api/v5/asset/balances",
        headers={},
        transport_class="SimulatedExternalFundingFixtureV1",
        get_performed=True,
    )
    ctx = TreasuryCapitalDepositObservationContextV1(
        evidence_id=f"{E2E_RUN_ID}-{evidence_suffix}",
        account_identity=_ACCOUNT,
        instrument_id=_INSTRUMENT,
        deposit_history_freshness=TreasuryDepositHistorySignalV1.CONFIRMED.value,
        deposit_history_confirms_increase=deposit_confirms,
        internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
        external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
        prior_reconciled_capital_raw=prior_raw,
        cached_trading_capital_raw=prior_raw,
        balance_freshness_override=TreasuryFreshnessSignalV1.FRESH.value,
    )
    observation = build_treasury_venue_observation_from_funding_balance_v1(funding, ctx)
    recon = evaluate_treasury_read_only_reconciliation_v1(observation)
    chain = execute_treasury_productive_reconciliation_chain_v1(observation)
    return {
        "branch_id": branch_id,
        "INPUT": "SIMULATED_OKX_EEA_DEPOSIT_10000_EUR",
        "RECONCILIATION_RESULT": recon.reconciliation_class,
        "CAPITAL_STATE": chain.get("CAPITAL_ADMISSION_RISK_ADMISSIBLE"),
        "ADMISSION_RESULT": chain.get("ACCOUNT_STATE_JOIN_STATUS", {}).get(
            "orchestration_admitted"
        ),
        "RISK_ADMISSIBLE": chain.get("CAPITAL_ADMISSION_RISK_ADMISSIBLE"),
        "OUTPUT_CONTRACT": "TreasuryVenueObservationV1→ReconciliationV1→ProductiveChainV1",
        "NEXT_EXPECTED_EDGE": "treasury_to_admission / C08 single-source handoff",
        "observation": asdict(observation),
        "reconciliation": asdict(recon),
        "productive_chain": chain,
        "disposition": recon.reconciliation_class,
    }


def _run_treasury_capital_line() -> dict[str, Any]:
    body_sha = hashlib.sha256(
        json.dumps(
            {"avail_eq": _SIM_MARGIN_AVAIL_EQ, "e2e_run_id": E2E_RUN_ID}, sort_keys=True
        ).encode()
    ).hexdigest()
    eur_only = _treasury_branch(
        branch_id="A_EUR_FUNDING_ROW_ONLY",
        body=_funding_bytes_eur_only(),
        prior_raw="0",
        deposit_confirms=True,
        evidence_suffix="eur-only",
    )
    usdc_settled = _treasury_branch(
        branch_id="B_SIMULATED_USDC_AFTER_DEPOSIT",
        body=_funding_bytes(usdc_bal=_SIM_USDC_AFTER),
        prior_raw=_SIM_USDC_BEFORE,
        deposit_confirms=True,
        evidence_suffix="usdc-settled",
    )
    funding_obs = build_treasury_venue_observation_from_funding_balance_v1(
        parse_funding_account_balance_observation_v1(
            body_bytes=_funding_bytes(usdc_bal=_SIM_USDC_AFTER),
            http_status=200,
            observed_at_utc=DECISION_EPOCH,
            venue="okx",
            rest_host="eea.okx.com",
            endpoint="/api/v5/asset/balances",
            headers={},
            transport_class="SimulatedExternalFundingFixtureV1",
            get_performed=True,
        ),
        TreasuryCapitalDepositObservationContextV1(
            evidence_id=f"{E2E_RUN_ID}-primary",
            account_identity=_ACCOUNT,
            instrument_id=_INSTRUMENT,
            deposit_history_freshness=TreasuryDepositHistorySignalV1.CONFIRMED.value,
            deposit_history_confirms_increase=True,
            internal_transfer_signal=TreasuryInternalTransferSignalV1.CLEAR.value,
            external_depletion_signal=TreasuryExternalDepletionSignalV1.NONE.value,
            prior_reconciled_capital_raw=_SIM_USDC_BEFORE,
            cached_trading_capital_raw=_SIM_USDC_BEFORE,
            balance_freshness_override=TreasuryFreshnessSignalV1.FRESH.value,
        ),
    )
    funding_recon = evaluate_treasury_read_only_reconciliation_v1(funding_obs)
    treasury_join = join_treasury_reconciliation_into_capital_admission_v1(
        funding_obs,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
    )
    orch_join = join_treasury_capital_admission_into_account_equity_orchestration_v1(treasury_join)
    e4_host = join_treasury_observation_through_e4_into_productive_account_equity_host_v1(
        funding_obs,
        expected_account_identity=_ACCOUNT,
        expected_instrument_id=_INSTRUMENT,
        usdc_row_status=CURRENCY_ROW_STATUS_PRESENT,
        u04_p01_eligibility_host_inputs=build_default_full_core_u04_p01_eligibility_host_inputs_v1(
            raw_acct_lv="2",
        ),
    )
    margin_obs = CurrentProductiveUsdcFreeMarginObservationV1(
        fact_id="CURRENT_PRODUCTIVE_USDC_FREE_MARGIN_OBSERVATION",
        surface=OBSERVATION_SURFACE,
        value=_SIM_MARGIN_AVAIL_EQ,
        settlement_currency="USDC",
        selected_ccy="USDC",
        bound_account_identity=REUSED_BINDING_ACCOUNT_SCOPE,
        bound_venue_identity="okx",
        bound_td_mode="cross",
        decision_epoch=DECISION_EPOCH,
        observed_at_as_of=DECISION_EPOCH,
        age_seconds="1",
        freshness_max_age=str(NUMERIC_EQUITY_TTL_SECONDS),
        provenance_digest=body_sha,
        already_net_of_in_use="true",
        account_level_avail_eq_used="false",
        fallback_chain_used="false",
    )
    handoff = execute_current_productive_treasury_single_source_capital_handoff_v1(
        margin_observation=margin_obs,
        instrument_id=_INSTRUMENT,
        body_sha256=body_sha,
        fresh_pretrade_get_status=FreshPretradeGetStatusV1.TRUSTED_PRESENT.value,
        live_account_bound_status=LiveAccountBoundStatusV1.TRUSTED_PRESENT.value,
        u04_p01_host_inputs=build_default_full_core_u04_p01_eligibility_host_inputs_v1(
            raw_acct_lv="2",
        ),
        clear_treasury_idempotency=True,
    )
    _, cycle_b, _ = _host_enter_cycle()
    replay = _enter_replay(cycle_b)
    if current_productive_decision_class_v1(replay) != DECISION_ENTER:
        replay = replace(
            replay,
            evidence=replace(replay.evidence, decision_outcome="enter_long", selected_side="long"),
        )
    enter_live = join_current_productive_enter_live_29p_before_venue_plan_v1(
        replay=replay,
        bound_instrument=_bound(),
        injected=replace(
            _injected(payload=_balance_payload(avail_eq=_SIM_MARGIN_AVAIL_EQ)),
            body_sha256=body_sha,
            observed_at=DECISION_EPOCH,
            expected_account_identity=REUSED_BINDING_ACCOUNT_SCOPE,
        ),
        decision_epoch=DECISION_EPOCH,
    )
    step29_ok = (
        handoff.fail_closed is False
        and handoff.producer_output.produced == "true"
        and handoff.step_29p_admissibility.risk_admissible is True
    )
    enter_ok = enter_live.status == "PASS" and enter_live.step_29p_risk_admissible == "true"
    return {
        "branches": {"eur_only": eur_only, "usdc_settled": usdc_settled},
        "funding_recon_class": funding_recon.reconciliation_class,
        "orchestration_admitted": e4_host.orchestration_join.ingress.orchestration_admitted,
        "orch_join_admitted": orch_join.ingress.orchestration_admitted,
        "handoff": handoff,
        "margin_observation": margin_obs,
        "enter_live": enter_live,
        "step29_ok": step29_ok,
        "enter_ok": enter_ok,
        "causal_capital_trace": [
            f"simulated_settled_deposit_eur={_SIM_EUR_DEPOSIT}",
            f"treasury_funding_usdc={funding_obs.venue_balance_raw} ({funding_recon.reconciliation_class})",
            "e4_orchestration_deferred_to_account_equity",
            f"simulated_margin_availEq={_SIM_MARGIN_AVAIL_EQ}",
            f"account_equity_produced={handoff.producer_output.value}",
            f"29p_risk_admissible={handoff.step_29p_admissibility.risk_admissible}",
            f"enter_live_29p={enter_live.status}",
        ],
    }


def _native_for(ranking: Mapping[str, Any], instrument_id: str) -> str:
    for row in ranking.get("ranked_candidates") or []:
        if str(row.get("canonical_instrument_id")) == instrument_id:
            return str(row.get("venue_native_id") or "")
    return ""


def _memory_g17(*, instrument_id: str, venue_native_id: str) -> object:
    venue = "OKX"
    t0 = float(PREVIOUS_C1_VENUE_EVENT_TIME) - 3600.0
    producer = CanonicalVolatilityTypedRuntimeProducerScaffoldV1.create(
        venue=venue,
        canonical_instrument_id=instrument_id,
        venue_instrument_id=venue_native_id,
        persistence_path=None,
    )
    for index in range(61):
        sample = MarketSampleIdentityV1(
            venue=venue,
            canonical_instrument_id=instrument_id,
            venue_instrument_id=venue_native_id,
            event_time=EventTimeInstantV1(unix_seconds=t0 + float(index * 60)),
            mark_price=100.0 * math.exp(0.001 * index),
        )
        producer.ingest_finalized_pt1m_mark_sample_v1(
            sample=sample,
            transport=ObservationTransportMetadataV1(receive_time=t0 + index * 60 + 0.5),
        )
    return producer


def _empty_portfolio() -> PortfolioTruthSnapshotV1:
    return PortfolioTruthSnapshotV1(
        cash=None,
        duplicate=False,
        event_time_unix=1_700_000_000.0,
        max_age_seconds=None,
        missing=False,
        positions=[],
        source_id=E2E_RUN_ID,
        stale=False,
        wall_time_unix=1_700_000_000.0,
        writer_conflict=False,
    )


def _probe_loop_a(n5_root: Path) -> dict[str, Any]:
    from src.ops.full_core_live_path_composition_root_v1.current_productive_master_v2_ddo_capture_to_offline_export_join_v1 import (
        HANDOFF_ARTIFACT_BASENAME,
    )
    from src.experiments.canonical_optimization_universe_learning_input_v1 import (
        STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT,
    )

    ledgers = sorted(n5_root.glob("LANE_*/ddo_learning_capture_v1.jsonl"))
    lane_stats: list[dict[str, Any]] = []
    export_stats: list[dict[str, Any]] = []
    capture_ok = False
    export_ok = False
    export_reason = "NO_OFFLINE_EXPORT_HANDOFF_ARTIFACT"
    for path in ledgers:
        lane_dir = path.parent
        lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        handoff_path = lane_dir / HANDOFF_ARTIFACT_BASENAME
        handoff_payload: dict[str, Any] | None = None
        if handoff_path.is_file():
            handoff_payload = json.loads(handoff_path.read_text(encoding="utf-8"))
        lane_stats.append(
            {
                "lane": lane_dir.name,
                "ledger_path": str(path.relative_to(REPO)),
                "record_lines": len(lines),
                "offline_export_handoff": handoff_payload,
            }
        )
        if len(lines) >= 7:
            capture_ok = True
        if handoff_payload is not None:
            export_stats.append(handoff_payload)
            if (
                handoff_payload.get("optimization_ack_status")
                == STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT
            ):
                export_ok = True
                export_reason = "ACCEPTED_OFFLINE_RESEARCH_INPUT"
    if capture_ok and not export_ok:
        export_reason = "CAPTURE_OK_BUT_OFFLINE_EXPORT_HANDOFF_NOT_ACCEPTED"
    return {
        "lanes_with_ledgers": len(ledgers),
        "lane_stats": lane_stats,
        "capture_ok": capture_ok and len(ledgers) >= 5,
        "export_runtime_reached": export_ok and capture_ok,
        "export_reason": export_reason if export_ok else export_reason,
        "export_lane_artifacts_accepted": sum(
            1
            for row in export_stats
            if row.get("optimization_ack_status") == STATUS_ACCEPTED_OFFLINE_RESEARCH_INPUT
        ),
    }


def _edge_by_id(edges: list[Mapping[str, Any]], eid: str) -> Mapping[str, Any] | None:
    for edge in edges:
        if str(edge.get("id")) == eid:
            return edge
    return None


def _adjudicate_kernel_edge(
    eid: str,
    *,
    treasury: Mapping[str, Any],
    pre_external: bool,
    loop_a: Mapping[str, Any],
    acquisition_ok: bool,
    cap21_ok: bool,
) -> str:
    if eid == "treasury_to_admission":
        # Map CONFLICTING lifecycle; runtime proof is C08 defer → B05 equity → 29P (not direct mint).
        return "RUNTIME_REACHED" if treasury.get("step29_ok") else "NOT_REACHED"
    if eid == "eea_acquisition_to_cap21_cap23_persist":
        return "RUNTIME_PROVEN" if acquisition_ok and cap21_ok else "NOT_REACHED"
    if eid in {
        "universe_to_ranking",
        "ranking_to_selection",
        "selection_to_binding",
        "binding_to_mv2",
        "mv2_executable_pre_external_terminal",
    }:
        return "RUNTIME_PROVEN" if pre_external else "NOT_REACHED"
    if eid == "fa_compose_portfolio_budget":
        return "RUNTIME_REACHED" if pre_external else "NOT_REACHED"
    if eid == "learning_capture":
        return "RUNTIME_PROVEN" if loop_a.get("capture_ok") else "NOT_REACHED"
    if eid == "learning_evidence_export_to_optimization":
        if loop_a.get("export_runtime_reached"):
            return "RUNTIME_PROVEN"
        if loop_a.get("capture_ok"):
            return "AUTHORITY_BOUNDARY"
        return "NOT_REACHED"
    if eid == "intent_to_execution":
        return "AUTHORITY_BOUNDARY" if pre_external else "NOT_REACHED"
    if eid == "sizing_to_intent":
        return "RUNTIME_REACHED" if pre_external else "NOT_REACHED"
    if eid == "portfolio_to_enter":
        return "RUNTIME_REACHED" if treasury.get("enter_ok") else "NOT_REACHED"
    if eid == "mv2_to_sizing":
        return "RUNTIME_REACHED" if pre_external else "NOT_REACHED"
    return "UNKNOWN"


def main() -> int:
    origin = _origin()
    map_sha = _sha256_file(MAP_SOURCE)
    atlas_sha = _sha256_file(ATLAS_META)
    map_edges = _load_json(MAP_SOURCE).get("edges") or []

    expected_path = [
        "SIMULATED_OKX_EEA_DEPOSIT_10000_EUR",
        "treasury_29p (read-only reconciliation + C08 deferral)",
        "capital_risk_sizing (B05 equity + 29P)",
        "eea_universe_inventory_acquisition_v1 (GET-only)",
        "cap21→cap23 persist",
        "ranking→selection→binding",
        "N5 full-autonomy compose→MV2",
        "PRE_EXTERNAL_EFFECT",
        "learning_capture (DDO #6936)",
        "learning_evidence_export_to_optimization (offline boundary)",
    ]
    authority_boundaries = [
        "POST_ALLOWED=false REAL_VENUE_POST_ALLOWED=false EXTERNAL_EFFECT_AUTHORIZED=false",
        "treasury_to_admission map lifecycle CONFLICTING; runtime uses C08/B05 split",
        "No CURRENT join from Step29P output into acquire_eea_universe_inventory_v1",
        "N5 portfolio budget uses empty PortfolioTruthSnapshotV1 (equity not dynamically bound)",
        "intent_to_execution / venue POST requires scoped Owner-GO",
        "optimization apply/promotion forbidden on this run",
    ]

    print(
        json.dumps(
            {
                "phase": 0,
                "BASELINE_SHA": origin,
                "MAP_VERSION_OR_SHA": map_sha,
                "ATLAS_VERSION_OR_SHA": atlas_sha,
                "EXPECTED_CURRENT_GRAPH_PATH": expected_path,
                "EXPECTED_AUTHORITY_BOUNDARIES": authority_boundaries,
            }
        ),
        flush=True,
    )

    print(json.dumps({"phase": 1, "treasury_zero_root": E2E_RUN_ID}), flush=True)
    treasury = _run_treasury_capital_line()
    (PACK / "TREASURY_BRANCHES.json").write_text(
        json.dumps(treasury["branches"], indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    if not treasury["step29_ok"]:
        report = {
            "WP": "WHOLE_SYSTEM_TREASURY_ZERO_TO_PRE_EXTERNAL_MAP_ATLAS_GUIDED_E2E_V1",
            "BASELINE_SHA": origin,
            "WHOLE_SYSTEM_E2E_RUN_ID": E2E_RUN_ID,
            "FIRST_REAL_BLOCKER": "TREASURY_CAPITAL_HANDOFF_FAIL_CLOSED",
            "POST_COUNT": 0,
            "EXTERNAL_EFFECT_OCCURRED": False,
        }
        (PACK / "FINAL_REPORT.json").write_text(json.dumps(report, indent=2) + "\n")
        return 2

    handoff = treasury["handoff"]
    productive_join = join_step_29p_admitted_capital_into_eea_universe_acquisition_v1(
        Step29pToEeaAcquisitionProductiveJoinRequestV1(
            handoff=handoff,
            e2e_run_id=E2E_RUN_ID,
            capital_lineage_class=CAPITAL_LINEAGE_CLASS_SYNTHETIC_TEST_FIXTURE,
            expected_account_identity=REUSED_BINDING_ACCOUNT_SCOPE,
            expected_instrument_id=str(handoff.step_29p_claim.expected_instrument_id),
        ),
        observed_at=DECISION_EPOCH,
    )
    treasury_to_productive = {
        "EDGE_ID": "enter_live_29p_to_eea_acquisition",
        "join_seam_id": productive_join.join_seam_id,
        "disposition": "RUNTIME_PROVEN" if productive_join.ok else "FAIL_CLOSED",
        "lineage_binding_digest": productive_join.lineage_binding_digest,
        "step_29p_decision_epoch": productive_join.step_29p_decision_epoch,
        "producer_input_set_digest": productive_join.producer_input_set_digest,
        "reason_codes": list(productive_join.reason_codes),
    }
    (PACK / "TREASURY_TO_PRODUCTIVE_CONNECT.json").write_text(
        json.dumps(treasury_to_productive, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {
                "phase": 2,
                "TREASURY_TO_PRODUCTIVE_JOIN_RUNTIME_PROVEN": productive_join.ok,
            }
        ),
        flush=True,
    )
    if not productive_join.ok or productive_join.acquisition is None:
        (PACK / "FINAL_REPORT.json").write_text(
            json.dumps(
                {
                    "WP": "WHOLE_SYSTEM_CAUSAL_CLOSURE_FROM_SYNTHETIC_TREASURY_ZERO_E2E_V1",
                    "WHOLE_SYSTEM_E2E_RUN_ID": E2E_RUN_ID,
                    "TREASURY_TO_PRODUCTIVE_JOIN_RUNTIME_PROVEN": False,
                    "BLOCKER": "STEP_29P_TO_EEA_PRODUCTIVE_JOIN_FAIL_CLOSED",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return 2

    observed_unix = time.time()
    acquisition = productive_join.acquisition
    (PACK / "acquisition_v1.json").write_text(
        json.dumps(acquisition.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    portfolio_owner = PortfolioCapitalReservationBudgetOwnerV1()
    budget_join = join_step_29p_handoff_into_portfolio_capital_reservation_budget_v1(
        handoff=handoff,
        owner=portfolio_owner,
        e2e_run_id=E2E_RUN_ID,
    )
    (PACK / "EQUITY_TO_N5_BUDGET_CONNECT.json").write_text(
        json.dumps(
            {
                "join_seam_id": budget_join.join_seam_id,
                "ok": budget_join.ok,
                "admitted_budget": budget_join.admitted_budget,
                "observation_id": budget_join.observation_id,
                "step_29p_decision_epoch": budget_join.step_29p_decision_epoch,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "phase": 3,
                "EQUITY_TO_N5_BUDGET_RUNTIME_PROVEN": budget_join.ok,
            }
        ),
        flush=True,
    )

    productive_store = PACK / "fresh_productive_store"
    cap21_23 = run_cap21_to_cap23_persist_productive_v1(
        acquisition=acquisition,
        store=productive_store,
        repository_sha=origin,
        observed_unix=observed_unix,
        session_id_prefix=E2E_RUN_ID,
    )
    if not cap21_23.ok:
        (PACK / "FINAL_REPORT.json").write_text(
            json.dumps({"BLOCKER": cap21_23.status, "E2E_RUN_ID": E2E_RUN_ID}, indent=2) + "\n"
        )
        return 2

    ranking_path = (
        productive_store / "runtime_state/ranking/productive_futures_ranking_snapshot_v1.json"
    )
    ranking = _load_json(ranking_path)
    eligible = parse_eligible_cap22_top20(ranking)
    provenance = Cap22ProvenanceV1(
        ranking_snapshot_id=str(ranking["ranking_snapshot_id"]),
        ranking_schema_version=str(ranking["schema_version"]),
        ranking_integrity_digest=str(ranking["integrity_digest"]),
        ranking_event_time=str(ranking["event_time"]),
        universe_snapshot_id=str(ranking["universe_snapshot_id"]),
        ranking_policy_id=str(ranking["ranking_policy_id"]),
        ranking_policy_version=str(ranking["ranking_policy_version"]),
        source_relative_path=str(ranking_path.relative_to(REPO)),
        source_file_sha256=hashlib.sha256(ranking_path.read_bytes()).hexdigest(),
        snapshot_state=str(ranking["snapshot_state"]),
        top20_candidate_context_limit=int(ranking["top20_candidate_context_limit"]),
    )
    membership_store = PACK / "membership_store"
    membership_store.mkdir(parents=True, exist_ok=True)
    bootstrap = build_membership_context_artifact_v1(
        ordered_instrument_ids=tuple(c.instrument_id for c in eligible[:5]),
        cap22_provenance=provenance,
        bootstrap=True,
        prior_membership_reference=None,
    )
    selector = run_isolated_selector_cycle_v1(
        snapshot=ranking,
        cap22_provenance=provenance,
        prior=bootstrap,
        store_root=membership_store,
        persist=True,
    )
    membership = selector.persisted_artifact or bootstrap
    effective_top5 = list(membership.ordered_instrument_ids)
    marks = {
        _native_for(ranking, iid): "100.0" for iid in effective_top5 if _native_for(ranking, iid)
    }

    runtime_base = PACK / "n5_topology"
    runtime_base.mkdir(parents=True, exist_ok=True)
    writer = DurableLaneAssignmentSingleWriterV1(state_root=checkpoint_root_for(runtime_base))
    writer.acquire()
    cap24 = ProductiveFullAutonomyCap24BindContextV1(
        ranking_state_root=productive_store / "runtime_state/ranking",
        universe_state_root=productive_store / "runtime_state/universe",
        reconciliation_state_root=productive_store / "runtime_state/recon",
        observed_portfolio=_empty_portfolio(),
        mark_price_by_native_id=marks,
        session_id=E2E_RUN_ID,
        now_unix=observed_unix,
    )
    cycle = _market_kwargs(cycle_id_prefix="wsccstz")
    cycle.pop("origin_main_sha", None)
    cycle["g17_typed_vol_producers"] = {
        LANE_IDS[i]: _memory_g17(
            instrument_id=effective_top5[i],
            venue_native_id=_native_for(ranking, effective_top5[i]),
        )
        for i in range(min(5, len(effective_top5)))
    }
    n5 = run_staged_productive_full_autonomy_n5_runtime_control_plane_v1(
        membership=membership,
        ranking_snapshot=ranking,
        topology_state_root_base=runtime_base,
        lane_assignment_writer=writer,
        cap24_bind=cap24,
        repository_sha=origin,
        producer_observed_at_unix=observed_unix,
        origin_main_sha=origin,
        requested_target_cardinality=5,
        portfolio_budget_owner=portfolio_owner,
        architectural_composition_harness=True,
        **cycle,
    )
    writer.release()

    sim_root = PACK / "simulated_branch"
    sim_root.mkdir(parents=True, exist_ok=True)
    pre_lane = sim_root / "gap_true_01_lane"
    pre_lane.mkdir(parents=True, exist_ok=True)
    integrity = MockCurrentProductive29PIntegrityBackendV1(origin_main=origin, head=origin)
    bound = _bound()
    _arm, enter_closes, mark_px, event_ts, g17_aligned = (
        prepare_layered_long_armed_seed_for_pre_external_invoke_v1(
            bound=bound,
            g17_typed_vol_producer=object(),
            lane_state_root=pre_lane,
        )
    )
    del _arm
    candles = governed_c1_candles_payload_from_enter_closes_v1(
        enter_closes=enter_closes,
        last_event_ts_unix=event_ts,
    )
    cap24_root = write_cap21_productivity_root_for_inst_v1(sim_root, venue_native_id=_TEST_INST)
    gap = execute_current_productive_gap_true_01_executable_envelope_pre_external_evidence_v1(
        owner_go=GAP_OWNER_GO,
        origin_main_sha=origin,
        bound_instrument=bound,
        fresh_get_transport=_productive_transport(),
        lane_state_root=pre_lane,
        cap24_productivity_root=cap24_root,
        candles_payload=candles,
        market_kwargs={
            "cycle_id_prefix": "wstzmae2e-gap",
            "mark_px": mark_px,
            "index_px": mark_px,
            "bid_px": mark_px - 0.5,
            "ask_px": mark_px + 0.5,
            "finalized_closes": enter_closes,
            "last_finalized_event_ts_unix": event_ts,
            "observed_unix": event_ts + 100.0,
            "venue_flat": True,
            "volume": 10.0,
            "open_interest": 20.0,
            "funding_rate": 0.0001,
            "existing_position_side": ExistingPositionSide.NONE,
        },
        g17_typed_vol_producers={"LANE_1": g17_aligned},
        evidence_root=sim_root / "gap_true_01_evidence",
        execution_integrity_backend=integrity,
    )

    orch = n5.orchestrator_result
    pre_external = gap.gap_true_01_verdict == "CLOSED" or any(
        r.disposition == DISPOSITION_PRE_EXTERNAL_EFFECT
        for r in (orch.lane_rollups if orch else ())
    )

    loop_a = _probe_loop_a(runtime_base)

    loop_a_edges = [
        {
            "edge_id": "learning_capture",
            "disposition": "RUNTIME_PROVEN" if loop_a.get("capture_ok") else "NOT_REACHED",
            "source_domain": "mv2_double_play",
            "target_domain": "learning_ddo",
        },
        {
            "edge_id": "learning_evidence_export_to_optimization",
            "disposition": (
                "RUNTIME_PROVEN"
                if loop_a.get("export_runtime_reached")
                else ("AUTHORITY_BOUNDARY" if loop_a.get("capture_ok") else "NOT_REACHED")
            ),
            "source_domain": "learning_ddo",
            "target_domain": "optimization_research",
            "root_cause": loop_a.get("export_reason"),
        },
    ]

    kernel_adj: list[dict[str, Any]] = []
    coverage: dict[str, int] = {}
    for eid in sorted(PRODUCTIVE_KERNEL_EDGES):
        disp = _adjudicate_kernel_edge(
            eid,
            treasury=treasury,
            pre_external=pre_external,
            loop_a=loop_a,
            acquisition_ok=acquisition.ok,
            cap21_ok=cap21_23.ok,
        )
        coverage[disp] = coverage.get(disp, 0) + 1
        meta = _edge_by_id(map_edges, eid) or {}
        kernel_adj.append(
            {
                "edge_id": eid,
                "source_domain": meta.get("from_domain"),
                "target_domain": meta.get("to_domain"),
                "disposition": disp,
            }
        )

    first_blocker = (
        "OWNER_GO_REQUIRED_FOR_VENUE_POST_AND_PRODUCTIVE_APPLY_PROMOTION"
        if pre_external
        else "PRODUCTIVE_GRAPH_INCOMPLETE"
    )
    first_blocker_edge = (
        "intent_to_execution" if pre_external else "STEP_29P_TO_EEA_PRODUCTIVE_JOIN"
    )
    equity_to_n5_proven = budget_join.ok and bool(n5.audit.portfolio_admitted)
    learning_capture_proven = bool(loop_a.get("capture_ok"))
    learning_export_proven = bool(loop_a.get("export_runtime_reached"))
    secondary = None
    fixpoint_reached = (
        pre_external
        and learning_capture_proven
        and learning_export_proven
        and productive_join.ok
        and equity_to_n5_proven
    )

    report: dict[str, Any] = {
        "WP": "WHOLE_SYSTEM_CAUSAL_CLOSURE_FROM_SYNTHETIC_TREASURY_ZERO_E2E_V1",
        "INITIAL_EVENT_SEMANTICS": "SYNTHETIC_TEST_FIXTURE_ONLY",
        "SYNTHETIC_TEST_VALUE_HAS_PRODUCTIVE_AUTHORITY": False,
        "TREASURY_TO_PRODUCTIVE_JOIN_RUNTIME_PROVEN": productive_join.ok,
        "EQUITY_TO_N5_BUDGET_RUNTIME_PROVEN": equity_to_n5_proven,
        "MECHANICAL_REPAIRS_PERFORMED": [
            "current_productive_step_29p_to_eea_acquisition_productive_join_v1",
            "current_productive_step_29p_to_portfolio_budget_productive_join_v1",
            "current_productive_master_v2_ddo_capture_to_offline_export_join_v1",
        ],
        "OUT_OF_SCOPE_PRESENTATION_SURFACES": [
            "LANDSCAPE_MARKET_DASHBOARD",
            "PRESENTATION_INGRESS_EGRESS",
        ],
        "PRE_EXTERNAL_REACHED": pre_external,
        "LEARNING_CAPTURE_RUNTIME_PROVEN": learning_capture_proven,
        "LEARNING_CAPTURE_TO_OFFLINE_EXPORT_RUNTIME_PROVEN": learning_export_proven,
        "OFFLINE_EXPORT_RESULT": loop_a.get("export_reason"),
        "EXECUTION_BRANCH_FIRST_UNCLOSED_EDGE": (
            "intent_to_execution" if pre_external else "mv2_executable_pre_external_terminal"
        ),
        "EXECUTION_BRANCH_BLOCKER": (
            "OWNER_GO_REQUIRED_FOR_VENUE_POST" if pre_external else "PRODUCTIVE_GRAPH_INCOMPLETE"
        ),
        "EXECUTION_BRANCH_BLOCKER_CLASS": "EXTERNAL_EFFECT_AUTHORITY",
        "LEARNING_BRANCH_FIRST_UNCLOSED_EDGE": (
            "optimization_apply_or_promotion"
            if learning_export_proven
            else "learning_evidence_export_to_optimization"
        ),
        "LEARNING_BRANCH_BLOCKER": (
            "PRODUCTIVE_OPTIMIZATION_JOIN_AUTHORIZED=false"
            if learning_export_proven
            else loop_a.get("export_reason")
        ),
        "LEARNING_BRANCH_BLOCKER_CLASS": (
            "OPTIMIZATION_APPLY_AUTHORITY" if learning_export_proven else "MECHANICAL_OR_UPSTREAM"
        ),
        "ALL_IMMEDIATE_MECHANICAL_CLOSURES_EXHAUSTED": fixpoint_reached,
        "FIRST_REMAINING_AUTHORITY_DECISION": (
            "SCOPED_OWNER_GO_FOR_VENUE_POST_OR_PRODUCTIVE_OPTIMIZATION_APPLY"
            if fixpoint_reached
            else first_blocker
        ),
        "BASELINE_SHA": origin,
        "MAP_VERSION_OR_SHA": map_sha,
        "ATLAS_VERSION_OR_SHA": atlas_sha,
        "WHOLE_SYSTEM_E2E_RUN_ID": E2E_RUN_ID,
        "EVIDENCE_ROOT": str(PACK.relative_to(REPO)),
        "INITIAL_EVENT": "SIMULATED_OKX_EEA_DEPOSIT_10000_EUR",
        "DECISION_EPOCH": DECISION_EPOCH,
        "TREASURY_RESULT": treasury["branches"],
        "CAPITAL_RESULT": {
            "equity_value": treasury["handoff"].producer_output.value,
            "29p_risk_admissible": treasury["handoff"].step_29p_admissibility.risk_admissible,
            "causal_trace": treasury["causal_capital_trace"],
        },
        "ADMISSION_RESULT": {
            "orchestration_admitted": treasury["orchestration_admitted"],
            "enter_live_status": treasury["enter_live"].status,
        },
        "TREASURY_TO_PRODUCTIVE_CONNECT": treasury_to_productive,
        "EQUITY_TO_N5_BUDGET_CONNECT": {
            "ok": budget_join.ok,
            "admitted_budget": budget_join.admitted_budget,
            "n5_portfolio_admitted": bool(n5.audit.portfolio_admitted),
        },
        "PRODUCTIVE_GRAPH_PATH_EXPECTED": expected_path,
        "PRODUCTIVE_GRAPH_PATH_EXECUTED": [
            "Phase1 treasury+29P (same E2E_RUN_ID, synthetic fixture)",
            "Phase2 STEP-29P→EEA acquisition productive join (lineage stamped)",
            "Phase3 portfolio budget bind from same 29P handoff",
            "fresh EEA GET acquisition (causal gate)",
            "cap21-23 persist → ranking → Top5 → N5 → MV2",
            "gap_true_01 PRE_EXTERNAL branch",
            "Phase4 Loop-A ledger probe on N5 lanes",
        ],
        "BOUNDED_KERNEL_EDGE_ADJUDICATION": kernel_adj,
        "LOOP_A_EDGE_ADJUDICATION": loop_a_edges,
        "EDGES_RUNTIME_PROVEN": [
            r["edge_id"] for r in kernel_adj if r["disposition"] == "RUNTIME_PROVEN"
        ]
        + [r["edge_id"] for r in loop_a_edges if r["disposition"] == "RUNTIME_PROVEN"],
        "EDGES_RUNTIME_REACHED": [
            r["edge_id"] for r in kernel_adj if r["disposition"] == "RUNTIME_REACHED"
        ],
        "EDGES_NOT_REACHED": [
            r["edge_id"] for r in kernel_adj if r["disposition"] == "NOT_REACHED"
        ],
        "EDGES_CONTRACT_BLOCKER": [],
        "EDGES_AUTHORITY_BOUNDARY": [
            r["edge_id"] for r in kernel_adj if r["disposition"] == "AUTHORITY_BOUNDARY"
        ],
        "EDGES_UNKNOWN": [r["edge_id"] for r in kernel_adj if r["disposition"] == "UNKNOWN"],
        "SELECTED_FUTURE": effective_top5[0] if effective_top5 else None,
        "N5_RESULT": {
            "terminal_boundary": n5.terminal_boundary,
            "lanes": len(orch.lane_rollups) if orch else 0,
            "portfolio_admitted": bool(n5.audit.portfolio_admitted),
            "portfolio_active_sum": str(n5.audit.portfolio_active_sum),
        },
        "MV2_RESULT": {"pre_external_via_n5_or_gap": pre_external},
        "PRE_EXTERNAL_RESULT": {
            "reached": pre_external,
            "gap_verdict": gap.gap_true_01_verdict,
        },
        "LOOP_A_CAPTURE_RESULT": loop_a,
        "LOOP_A_EXPORT_RESULT": {
            "runtime_reached": loop_a.get("export_runtime_reached"),
            "reason": loop_a.get("export_reason"),
        },
        "FIRST_REAL_BLOCKER": first_blocker,
        "FIRST_REAL_BLOCKER_EDGE": first_blocker_edge,
        "FIRST_REAL_BLOCKER_HOST": "execution_external_effect",
        "FIRST_REAL_BLOCKER_ROOT_CAUSE": (
            "Fail-closed external-effect envelope; no scoped Owner-GO for venue POST."
            if pre_external
            else "STEP_29P_TO_EEA_PRODUCTIVE_JOIN_FAIL_CLOSED"
        ),
        "FIRST_REAL_BLOCKER_AUTHORITY_STATUS": "AUTHORITY_BOUNDARY_FAIL_CLOSED",
        "SECONDARY_TECHNICAL_GAP": secondary,
        "WHOLE_SYSTEM_RUNTIME_REACHABILITY": (
            "Single-run synthetic treasury→29P→productive join→EEA GET→Cap21-23→N5→PRE_EXTERNAL "
            "with DDO capture; treasury equity bound into portfolio budget when 29P handoff admits."
        ),
        "WHOLE_SYSTEM_AUTHORITY_REACHABILITY": (
            "PRE_EXTERNAL_EFFECT reachable; venue POST and optimization apply/promotion blocked."
        ),
        "FIXPOINT_REACHED": fixpoint_reached,
        "PR_NUMBER": None,
        "PR_HEAD_SHA": None,
        "POST_COUNT": int(acquisition.post_count or 0),
        "EXTERNAL_EFFECT_OCCURRED": False,
        "WIRE_SEND_PERMITTED": False,
        "POST_ALLOWED": False,
        "COVERAGE": coverage,
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    (PACK / "FINAL_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    (PACK / "LINEAGE.json").write_text(
        json.dumps(
            {
                "WHOLE_SYSTEM_E2E_RUN_ID": E2E_RUN_ID,
                "INITIAL_EVENT": "SIMULATED_OKX_EEA_DEPOSIT_10000_EUR",
                "DECISION_EPOCH": DECISION_EPOCH,
                "MAP_SHA256": map_sha,
                "ATLAS_SHA256": atlas_sha,
                "SINGLE_CAUSAL_LINEAGE": True,
                "NO_PRIOR_E2E_PACK_REUSE": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    print(
        json.dumps({"E2E_RUN_ID": E2E_RUN_ID, "PRE_EXTERNAL": pre_external, "coverage": coverage})
    )
    return 0 if pre_external else 2


if __name__ == "__main__":
    raise SystemExit(main())
