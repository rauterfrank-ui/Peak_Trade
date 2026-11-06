"""Read pinned text and name symbol endpoints. No imports of productive modules."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from scripts.ops.mv2_outer_boundary_projector_v1.constants_v1 import (
    OWNER_RELATION_CLASSES,
    RESOLVER_ID,
)
from scripts.ops.mv2_outer_boundary_projector_v1.source_pins_v1 import show_text

FlowMapper = Callable[[dict[str, Any]], tuple[str | None, str]]
Check = tuple[str, str, int]

CYCLE = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_master_v2_runtime_cycle_v1.py"
)
G17 = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_g17_typed_vol_cmc_bind_v1.py"
)
EXIT = "src/ops/exit_policy_producer_binding_v1/host_binding_v1.py"
CAPTURE = "src/learning/deterministic_decision_outcome_v0/capture_v0.py"
DDO_JOIN = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_master_v2_ddo_learning_capture_join_v1.py"
)
FAMILY = (
    "src/ops/productive_decision_host_active_archive_three_family_binding_v1/"
    "family_export_adapter_v1.py"
)
DP_EXPORT = "src/ops/double_play_archive_sibling_exporter_v1/exporter_v1.py"
DS_EXPORT = "src/ops/dynamic_scope_archive_sibling_exporter_v1/exporter_v1.py"
RECON = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_master_v2_reconciliation_admission_v1.py"
)
N5 = "src/ops/current_mf_n5_full_autonomy_occupied_lane_mv2_dp_handoff_join_v1/constants_v1.py"
ORCH = (
    "src/ops/full_core_live_path_composition_root_v1/"
    "current_productive_governed_cycle_orchestrator_v1.py"
)
DROP = "src/ops/ranking_universe_to_full_core_ssf_handoff_contract_v1.py"
PROOF = "src/ops/whole_system_connection_closure_bounded_wp_v1/constants_v1.py"

SYMBOL_TEXT_PATHS = (
    CYCLE,
    G17,
    EXIT,
    CAPTURE,
    DDO_JOIN,
    FAMILY,
    DP_EXPORT,
    DS_EXPORT,
    RECON,
    N5,
    ORCH,
    DROP,
    PROOF,
)

PARTNER_IDS = (
    "selection",
    "binding",
    "reconciliation",
    "market_data_provenance",
    "kill_switch_reader",
    "exit_policy",
    "crs",
    "risk",
    "capital",
    "order_intent",
    "execution",
)

_REPLAY_INPUT = (
    "    replay_input = build_integrated_offline_replay_input_v1(\n"
    "        replay_id=replay_id,\n"
    "        instrument_id=instrument_id,\n"
)
_CRS_CALL = "    bind_input = _wire_simulated_economics_crs_boundary_onto_replay_input_v1(\n"
_CYCLE_SIGNATURE = (
    "def run_current_productive_master_v2_runtime_cycle_v1(\n"
    "    *,\n"
    "    bound_instrument: BoundInstrumentV1,\n"
)


def load_pinned_symbol_texts_v1(repo_root: Path, commit: str) -> dict[str, str]:
    return {path: show_text(repo_root, commit, path) for path in SYMBOL_TEXT_PATHS}


def _check(texts: Mapping[str, str], checks: tuple[Check, ...]) -> str:
    ambiguous = False
    for path, needle, expected in checks:
        text = texts.get(path)
        if text is None:
            return "MISSING_PINNED_TEXT"
        found = text.count(needle)
        if expected == 0:
            if found != 0:
                return "UNEXPECTED_BINDING"
            continue
        if found == 0:
            return "MISSING_BINDING"
        if found != expected:
            ambiguous = True
    if ambiguous:
        return "AMBIGUOUS_SYMBOL"
    return "BELEGT"


def _ghv_type(flow: str | None, flow_mapper: FlowMapper | None) -> str | None:
    if flow_mapper is None or flow in (None, "", "UNKNOWN"):
        return None
    mapped, _note = flow_mapper({"flow_type": flow, "contract_or_payload": "PINNED_SYMBOL"})
    if mapped is None or mapped == "":
        return None
    return str(mapped)


def _census_index(edges: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(edge.get("edge_id") or ""): edge for edge in edges}


def _base_record(
    *,
    relation_id: str,
    census: dict[str, Any] | None,
    commit: str,
    tree: str,
    producer_symbol: str,
    consumer_symbol: str,
    producer_path: str,
    consumer_path: str,
    relation_class: str,
    class_basis: str,
    evidence_status: str,
    binding_status: str,
    uncertainty: str,
    direct_replay_relation: bool,
    flow_mapper: FlowMapper | None,
    kind: str,
) -> dict[str, Any]:
    flow = None if census is None else census.get("original_flow_type")
    flow_text = "UNKNOWN" if flow in (None, "") else str(flow)
    if census is None:
        flow_text = ""
    return {
        "relation_id": relation_id,
        "kind": kind,
        "census_edge_id": None if census is None else census.get("edge_id"),
        "original_flow_type": flow_text,
        "original_direction": None if census is None else census.get("observed_direction"),
        "original_source_id": None if census is None else census.get("source_id"),
        "original_target_id": None if census is None else census.get("target_id"),
        "producer_symbol": producer_symbol,
        "consumer_symbol": consumer_symbol,
        "producer_path": producer_path,
        "consumer_path": consumer_path,
        "relation_class": relation_class,
        "class_basis": class_basis,
        "class_derived_from_census_flow": False,
        "class_derived_from_ghv_type": False,
        "ghv_edge_type": _ghv_type(None if census is None else str(flow or ""), flow_mapper),
        "ghv_edge_type_replaces_flow": False,
        "evidence_status": evidence_status,
        "binding_status": binding_status,
        "uncertainty": uncertainty,
        "direct_replay_relation": direct_replay_relation,
        "membership_granted": False,
        "universe_ratification": False,
        "synthetic": False,
        "commit": commit,
        "tree": tree,
        "active_runtime_proven": False,
    }


def _positive(
    texts: Mapping[str, str],
    census_by_id: Mapping[str, dict[str, Any]],
    *,
    relation_id: str,
    census_edge_id: str | None,
    producer_symbol: str,
    consumer_symbol: str,
    producer_path: str,
    consumer_path: str,
    binding_checks: tuple[Check, ...],
    class_name: str,
    class_checks: tuple[Check, ...],
    class_basis: str,
    direct_replay_relation: bool,
    uncertainty: str,
    contradiction_checks: tuple[Check, ...] = (),
    commit: str,
    tree: str,
    flow_mapper: FlowMapper | None,
    kind: str,
) -> dict[str, Any]:
    census = None if census_edge_id is None else census_by_id.get(census_edge_id)
    binding_status = _check(texts, binding_checks)
    if census_edge_id is not None and census is None:
        binding_status = "MISSING_CENSUS_EDGE"
    class_status = _check(texts, class_checks) if class_checks else "NOT_EVIDENCED"
    relation_class = class_name if class_status == "BELEGT" and class_name else "UNKNOWN"
    if relation_class not in OWNER_RELATION_CLASSES:
        relation_class = "UNKNOWN"
    evidence_status = "BELEGT" if binding_status == "BELEGT" else "UNGEKLÄRT"
    contradiction = ""
    if contradiction_checks:
        contradiction = _check(texts, contradiction_checks)
    record = _base_record(
        relation_id=relation_id,
        census=census,
        commit=commit,
        tree=tree,
        producer_symbol=producer_symbol,
        consumer_symbol=consumer_symbol,
        producer_path=producer_path,
        consumer_path=consumer_path,
        relation_class=relation_class,
        class_basis=class_basis
        if relation_class != "UNKNOWN"
        else "CLASS_NOT_INDEPENDENTLY_EVIDENCED",
        evidence_status=evidence_status,
        binding_status=binding_status,
        uncertainty=uncertainty,
        direct_replay_relation=direct_replay_relation,
        flow_mapper=flow_mapper,
        kind=kind,
    )
    record["class_check_status"] = class_status
    record["census_source_status"] = "WIDERLEGT" if contradiction == "BELEGT" else ""
    if binding_status == "BELEGT":
        record["endpoint_classification"] = "RESOLVED_SYMBOL_ENDPOINT"
    elif binding_status == "AMBIGUOUS_SYMBOL":
        record["endpoint_classification"] = "UNRESOLVED_EDGE"
        record["uncertainty"] = "AMBIGUOUS_SYMBOL"
    else:
        record["endpoint_classification"] = "UNRESOLVED_EDGE"
    return record


def _negative(
    texts: Mapping[str, str],
    census_by_id: Mapping[str, dict[str, Any]],
    *,
    relation_id: str,
    census_edge_id: str,
    absent_checks: tuple[Check, ...],
    present_checks: tuple[Check, ...] = (),
    uncertainty: str,
    counterevidence: str,
    commit: str,
    tree: str,
    flow_mapper: FlowMapper | None,
) -> dict[str, Any]:
    census = census_by_id.get(census_edge_id)
    absent_status = _check(texts, absent_checks)
    present_status = _check(texts, present_checks) if present_checks else ""
    record = _base_record(
        relation_id=relation_id,
        census=census,
        commit=commit,
        tree=tree,
        producer_symbol="",
        consumer_symbol="",
        producer_path="",
        consumer_path="",
        relation_class="UNKNOWN",
        class_basis="CLASS_NOT_INDEPENDENTLY_EVIDENCED",
        evidence_status="UNGEKLÄRT" if absent_status == "BELEGT" else "UNGEKLÄRT",
        binding_status="MISSING_BINDING" if absent_status == "BELEGT" else absent_status,
        uncertainty=uncertainty,
        direct_replay_relation=False,
        flow_mapper=flow_mapper,
        kind="CENSUS_EDGE",
    )
    record["endpoint_classification"] = "UNRESOLVED_EDGE"
    counterevidence_status = counterevidence if absent_status == "BELEGT" else "UNGEKLÄRT"
    if present_checks and present_status != "BELEGT":
        counterevidence_status = "UNGEKLÄRT"
    record["counterevidence_status"] = counterevidence_status
    record["adjacent_token_status"] = present_status
    if census is None:
        record["binding_status"] = "MISSING_CENSUS_EDGE"
    return record


def _candidate_records(
    candidates: list[dict[str, Any]],
    *,
    commit: str,
    tree: str,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for candidate in candidates:
        component_id = str(candidate.get("component_id") or "")
        if component_id == "":
            continue
        basis = str(candidate.get("basis") or "")
        records.append(
            {
                "relation_id": f"candidate:{component_id}",
                "kind": "CANDIDATE",
                "component_id": component_id,
                "endpoint_classification": "UNRESOLVED_COMPONENT",
                "membership_classification": candidate.get("classification"),
                "membership_basis": basis,
                "membership_granted": False,
                "universe_ratification": False,
                "synthetic": False,
                "relation_class": "UNKNOWN",
                "evidence_status": "UNGEKLÄRT",
                "binding_status": "PACKAGE_OR_ROLE_WITHOUT_UNIQUE_SYMBOL",
                "uncertainty": "PACKAGE_DIRECTORY_CENSUS_OR_ROLE_IS_NOT_A_SYMBOL",
                "direct_replay_relation": False,
                "commit": commit,
                "tree": tree,
                "class_derived_from_census_flow": False,
                "class_derived_from_ghv_type": False,
                "ghv_edge_type_replaces_flow": False,
            }
        )
    return records


def resolve_symbol_endpoints_v1(
    *,
    commit: str,
    tree: str,
    texts: Mapping[str, str],
    census_edges: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
    flow_mapper: FlowMapper | None,
    ignored_observations: list[dict[str, Any]] | None = None,
    causal_graph_status: str = "NOT_MATERIALIZED",
) -> dict[str, Any]:
    """Resolve only the known census edges, candidates, and owner-named partners."""

    census_by_id = _census_index(census_edges)
    ignored = list(ignored_observations or [])
    common = {
        "commit": commit,
        "tree": tree,
        "flow_mapper": flow_mapper,
    }
    positives = [
        _positive(
            texts,
            census_by_id,
            relation_id="g17_bind_into_mv2_cycle",
            census_edge_id="g17_bind_into_mv2_cycle",
            producer_symbol="apply_current_productive_g17_typed_vol_cmc_bind_v1",
            consumer_symbol="build_integrated_offline_replay_input_v1",
            producer_path=G17,
            consumer_path=CYCLE,
            binding_checks=(
                (G17, "def apply_current_productive_g17_typed_vol_cmc_bind_v1(", 1),
                (CYCLE, "apply_current_productive_g17_typed_vol_cmc_bind_v1(", 1),
                (CYCLE, "market_context = g17_cmc_bind.context", 1),
                (CYCLE, "canonical_market_context=market_context", 1),
            ),
            class_name="DATA",
            class_checks=(
                (CYCLE, "market_context = g17_cmc_bind.context", 1),
                (CYCLE, "canonical_market_context=market_context", 1),
            ),
            class_basis="CONTEXT_OBJECT_ASSIGNED_INTO_REPLAY_INPUT",
            direct_replay_relation=True,
            uncertainty="ACTIVE_RUNTIME_NOT_PROVEN",
            kind="CENSUS_EDGE",
            **common,
        ),
        _positive(
            texts,
            census_by_id,
            relation_id="safety_signals_into_integrated_replay",
            census_edge_id="safety_signals_into_integrated_replay",
            producer_symbol="evaluate_host_exit_policy_producers_v1",
            consumer_symbol="build_integrated_offline_replay_input_v1",
            producer_path=EXIT,
            consumer_path=CYCLE,
            binding_checks=(
                (EXIT, "def evaluate_host_exit_policy_producers_v1(", 1),
                (CYCLE, "evaluate_host_exit_policy_producers_v1(", 1),
                (CYCLE, "trading_gate=exit_trading_gate", 1),
                (CYCLE, "safety_mode=exit_safety_mode", 1),
                (CYCLE, 'safety_exit_signal=exit_signals["safety_exit_signal"]', 1),
            ),
            class_name="SAFETY",
            class_checks=(
                (CYCLE, "safety_mode=exit_safety_mode", 1),
                (CYCLE, 'safety_exit_signal=exit_signals["safety_exit_signal"]', 1),
                (CYCLE, "trading_gate=exit_trading_gate", 1),
            ),
            class_basis="EXIT_POLICY_RESULT_BOUND_TO_REPLAY_SAFETY_FIELDS",
            direct_replay_relation=True,
            uncertainty="CENSUS_EXPORTER_SOURCE_IS_NOT_THE_PRODUCER",
            contradiction_checks=(
                (
                    CYCLE,
                    "export_safety_authority_to_archive_sibling_from_replay_commit_v1",
                    0,
                ),
            ),
            kind="CENSUS_EDGE",
            **common,
        ),
        _positive(
            texts,
            census_by_id,
            relation_id="learning_capture",
            census_edge_id="learning_capture",
            producer_symbol="run_integrated_offline_trading_logic_replay_v1",
            consumer_symbol="run_integrated_offline_replay_with_productive_ddo_capture_v1",
            producer_path=DDO_JOIN,
            consumer_path=DDO_JOIN,
            binding_checks=(
                (DDO_JOIN, "def run_integrated_offline_replay_with_productive_ddo_capture_v1(", 1),
                (DDO_JOIN, "run_integrated_offline_trading_logic_replay_v1(", 1),
                (CAPTURE, "CAPTURE_FAILURE_CHANGES_DECISION: bool = False", 1),
                (CAPTURE, 'CAPTURE_RUNTIME_EFFECT: str = "OBSERVATION_ONLY"', 1),
                (DDO_JOIN, "assert CAPTURE_FAILURE_CHANGES_DECISION is False", 1),
                (CYCLE, "if ddo_binding is not None:", 1),
                (CYCLE, "run_integrated_offline_replay_with_productive_ddo_capture_v1(", 1),
            ),
            class_name="EVIDENCE",
            class_checks=(
                (CAPTURE, 'CAPTURE_RUNTIME_EFFECT: str = "OBSERVATION_ONLY"', 1),
                (CAPTURE, "CAPTURE_FAILURE_CHANGES_DECISION: bool = False", 1),
                (DDO_JOIN, "assert CAPTURE_FAILURE_CHANGES_DECISION is False", 1),
            ),
            class_basis="OBSERVATION_ONLY_CAPTURE_CONTRACT",
            direct_replay_relation=True,
            uncertainty="CONDITIONAL_ON_DDO_LEDGER_PATH",
            kind="CENSUS_EDGE",
            **common,
        ),
        _positive(
            texts,
            census_by_id,
            relation_id="binding_to_mv2",
            census_edge_id="binding_to_mv2",
            producer_symbol="BoundInstrumentV1.instrument_id",
            consumer_symbol="build_integrated_offline_replay_input_v1",
            producer_path=CYCLE,
            consumer_path=CYCLE,
            binding_checks=(
                (CYCLE, _CYCLE_SIGNATURE, 1),
                (CYCLE, "instrument_id = str(bound_instrument.instrument_id", 1),
                (CYCLE, _REPLAY_INPUT, 1),
            ),
            class_name="DATA",
            class_checks=((CYCLE, _REPLAY_INPUT, 1),),
            class_basis="INSTRUMENT_ID_COPIED_INTO_REPLAY_INPUT",
            direct_replay_relation=True,
            uncertainty="BINDING_AUTHORITY_NOT_TRANSFERRED",
            kind="CENSUS_EDGE",
            **common,
        ),
        _positive(
            texts,
            census_by_id,
            relation_id="partner:crs",
            census_edge_id=None,
            producer_symbol="_wire_simulated_economics_crs_boundary_onto_replay_input_v1",
            consumer_symbol="run_integrated_offline_trading_logic_replay_v1",
            producer_path=CYCLE,
            consumer_path=CYCLE,
            binding_checks=(
                (CYCLE, "def _wire_simulated_economics_crs_boundary_onto_replay_input_v1(", 1),
                (CYCLE, _CRS_CALL, 1),
                (
                    CYCLE,
                    "current_instrument_capital_risk_sizing_boundary_state_file=boundary",
                    1,
                ),
                (CYCLE, "run_integrated_offline_trading_logic_replay_v1(bind_input)", 1),
            ),
            class_name="DATA",
            class_checks=((CYCLE, "propagation-only", 1),),
            class_basis="PROPAGATION_ONLY_BOUNDARY_ATTACHMENT",
            direct_replay_relation=True,
            uncertainty="ATTACHMENT_IS_CONDITIONAL_INSIDE_THE_WIRING_FUNCTION",
            kind="PARTNER",
            **common,
        ),
        _positive(
            texts,
            census_by_id,
            relation_id="archive_smoke_host_to_double_play_exporter",
            census_edge_id="archive_smoke_host_to_double_play_exporter",
            producer_symbol="export_families_after_runtime_commit_v1",
            consumer_symbol="export_double_play_display_to_archive_sibling_from_replay_commit_v1",
            producer_path=FAMILY,
            consumer_path=DP_EXPORT,
            binding_checks=(
                (FAMILY, "def export_families_after_runtime_commit_v1(", 1),
                (
                    FAMILY,
                    "export_double_play_display_to_archive_sibling_from_replay_commit_v1(",
                    1,
                ),
                (
                    DP_EXPORT,
                    "def export_double_play_display_to_archive_sibling_from_replay_commit_v1(",
                    1,
                ),
            ),
            class_name="",
            class_checks=(),
            class_basis="",
            direct_replay_relation=False,
            uncertainty="DISPLAY_EXPORT_IS_NOT_A_REPLAY_INPUT_EDGE",
            kind="CENSUS_EDGE",
            **common,
        ),
        _positive(
            texts,
            census_by_id,
            relation_id="archive_smoke_host_to_dynamic_scope_exporter",
            census_edge_id="archive_smoke_host_to_dynamic_scope_exporter",
            producer_symbol="export_families_after_runtime_commit_v1",
            consumer_symbol="export_dynamic_scope_state_to_archive_sibling_v1",
            producer_path=FAMILY,
            consumer_path=DS_EXPORT,
            binding_checks=(
                (FAMILY, "def export_families_after_runtime_commit_v1(", 1),
                (FAMILY, "export_dynamic_scope_state_to_archive_sibling_v1(", 1),
                (DS_EXPORT, "def export_dynamic_scope_state_to_archive_sibling_v1(", 1),
            ),
            class_name="",
            class_checks=(),
            class_basis="",
            direct_replay_relation=False,
            uncertainty="DISPLAY_EXPORT_IS_NOT_A_REPLAY_INPUT_EDGE",
            kind="CENSUS_EDGE",
            **common,
        ),
        _positive(
            texts,
            census_by_id,
            relation_id="partner:reconciliation",
            census_edge_id=None,
            producer_symbol="integrated_replay_reconciliation_state_v1",
            consumer_symbol="build_integrated_offline_replay_input_v1",
            producer_path=RECON,
            consumer_path=CYCLE,
            binding_checks=(
                (RECON, "def integrated_replay_reconciliation_state_v1(", 1),
                (CYCLE, "integrated_replay_reconciliation_state_v1()", 1),
                (CYCLE, "reconciliation_state=replay_reconciliation_state", 1),
            ),
            class_name="",
            class_checks=(),
            class_basis="",
            direct_replay_relation=True,
            uncertainty="FIELD_NAME_DOES_NOT_PROVE_STATE_CLASS",
            kind="PARTNER",
            **common,
        ),
    ]
    negatives = [
        _negative(
            texts,
            census_by_id,
            relation_id="CE-004",
            census_edge_id="CE-004",
            absent_checks=((CYCLE, "whole_system_connection_closure_bounded_wp_v1", 0),),
            uncertainty="PROOF_PACKAGE_IS_NOT_A_CYCLE_CALL",
            counterevidence="WIDERLEGT"
            if _proof_baseline_differs(texts.get(PROOF, ""), commit)
            else "UNGEKLÄRT",
            **common,
        ),
        _negative(
            texts,
            census_by_id,
            relation_id="fa_compose_mv2_dp_handoff_join",
            census_edge_id="fa_compose_mv2_dp_handoff_join",
            absent_checks=((CYCLE, "compose_occupied_lane_mv2_dp_handoff_v1(", 0),),
            present_checks=(
                (N5, "JOIN_TRADING_AUTHORITY = False", 1),
                (N5, "THIS_SLICE_MAY_INVOKE_FIRST_TRADING_DECISION_CONSUMER = False", 1),
            ),
            uncertainty="N5_MUST_NOT_INVOKE_THE_DECISION_CONSUMER",
            counterevidence="WIDERLEGT",
            **common,
        ),
        _negative(
            texts,
            census_by_id,
            relation_id="governed_cycle_t2_mv2_stack",
            census_edge_id="governed_cycle_t2_mv2_stack",
            absent_checks=((ORCH, "run_current_productive_master_v2_runtime_cycle_v1", 0),),
            present_checks=((ORCH, "t2_cycle_dispatch", 2),),
            uncertainty="DISPATCH_SLOT_IS_NOT_A_BOUND_CYCLE_CALL",
            counterevidence="UNGEKLÄRT",
            **common,
        ),
        _negative(
            texts,
            census_by_id,
            relation_id="replay_provenance_drop",
            census_edge_id="replay_provenance_drop",
            absent_checks=((CYCLE, "validate_replay_drops_handoff_provenance_v1", 0),),
            present_checks=((DROP, "def validate_replay_drops_handoff_provenance_v1(", 1),),
            uncertainty="CONTRACT_EXISTS_PRODUCTIVE_CYCLE_CALL_ABSENT",
            counterevidence="UNGEKLÄRT",
            **common,
        ),
        _negative(
            texts,
            census_by_id,
            relation_id="c1_injected_governed_cycle",
            census_edge_id="c1_injected_governed_cycle",
            absent_checks=((CYCLE, "map_injected_candles", 0),),
            uncertainty="NO_DIRECT_CYCLE_CALL",
            counterevidence="UNGEKLÄRT",
            **common,
        ),
        _negative(
            texts,
            census_by_id,
            relation_id="integrated_replay_safety_gate_before_intent",
            census_edge_id="integrated_replay_safety_gate_before_intent",
            absent_checks=((CYCLE, "typed_pre_29q_entry_blocked_v1", 0),),
            uncertainty="ADMISSION_FUNCTION_NOT_CALLED_BY_THE_CYCLE",
            counterevidence="UNGEKLÄRT",
            **common,
        ),
        _negative(
            texts,
            census_by_id,
            relation_id="mv2_to_sizing",
            census_edge_id="mv2_to_sizing",
            absent_checks=((CYCLE, "current_productive_mv2_capital_context_rebind_v1", 0),),
            uncertainty="REBIND_SEAM_NOT_CALLED_BY_THE_CYCLE",
            counterevidence="UNGEKLÄRT",
            **common,
        ),
        _negative(
            texts,
            census_by_id,
            relation_id="mv2_valid_no_trade_terminal",
            census_edge_id="mv2_valid_no_trade_terminal",
            absent_checks=((CYCLE, "NO_EXECUTABLE_DECISION", 0),),
            uncertainty="NO_DIRECT_CYCLE_TERMINAL_BINDING",
            counterevidence="UNGEKLÄRT",
            **common,
        ),
        _negative(
            texts,
            census_by_id,
            relation_id="mv2_executable_pre_external_terminal",
            census_edge_id="mv2_executable_pre_external_terminal",
            absent_checks=((CYCLE, "EXECUTABLE_VENUE_PLAN", 0),),
            uncertainty="NO_DIRECT_CYCLE_TERMINAL_BINDING",
            counterevidence="UNGEKLÄRT",
            **common,
        ),
    ]
    partner_gaps = [
        _partner_gap(
            texts,
            relation_id="partner:selection",
            partner_id="selection",
            uncertainty="SELECTION_ID_IS_NOT_A_REPLAY_INPUT_FIELD",
            commit=commit,
            tree=tree,
        ),
        _partner_gap(
            texts,
            relation_id="partner:market_data_provenance",
            partner_id="market_data_provenance",
            uncertainty="CYCLE_FORWARDS_A_PARAMETER_EXTERNAL_PRODUCER_UNRESOLVED",
            commit=commit,
            tree=tree,
        ),
        _partner_gap(
            texts,
            relation_id="partner:kill_switch_reader",
            partner_id="kill_switch_reader",
            uncertainty="KILL_SWITCH_FEEDS_EXIT_POLICY_NOT_THE_REPLAY_INPUT",
            commit=commit,
            tree=tree,
        ),
        _partner_gap(
            texts,
            relation_id="partner:risk",
            partner_id="risk",
            uncertainty="NO_DIRECT_CYCLE_CALL",
            commit=commit,
            tree=tree,
        ),
        _partner_gap(
            texts,
            relation_id="partner:capital",
            partner_id="capital",
            uncertainty="NO_DIRECT_CYCLE_CALL",
            commit=commit,
            tree=tree,
        ),
        _partner_gap(
            texts,
            relation_id="partner:order_intent",
            partner_id="order_intent",
            uncertainty="NO_DIRECT_CYCLE_CALL",
            commit=commit,
            tree=tree,
        ),
        _partner_gap(
            texts,
            relation_id="partner:execution",
            partner_id="execution",
            uncertainty="NO_DIRECT_CYCLE_CALL",
            commit=commit,
            tree=tree,
        ),
    ]
    records = (
        positives
        + negatives
        + partner_gaps
        + _candidate_records(candidates, commit=commit, tree=tree)
    )
    for record in records:
        record["ignored_observation_ids"] = sorted(
            str(item.get("edge_id") or item.get("component_id") or "") for item in ignored
        )
    resolved = [
        record
        for record in records
        if record.get("endpoint_classification") == "RESOLVED_SYMBOL_ENDPOINT"
    ]
    proven = [record for record in resolved if _is_proven(record)]
    unresolved = [
        record
        for record in records
        if record.get("endpoint_classification") != "RESOLVED_SYMBOL_ENDPOINT"
    ]
    resolved = _sort(resolved)
    proven = _sort(proven)
    unresolved = _sort(unresolved)
    flow_kept = all(
        record.get("ghv_edge_type_replaces_flow") is False
        and record.get("class_derived_from_census_flow") is False
        and record.get("class_derived_from_ghv_type") is False
        and record.get("synthetic") is False
        for record in records
    )
    return {
        "RESOLVER_ID": RESOLVER_ID,
        "INPUT_SCOPE": {
            "resolver_id": RESOLVER_ID,
            "candidate_count": len(candidates),
            "census_edge_count": len(census_edges),
            "partner_count": len(PARTNER_IDS),
            "pinned_paths": list(SYMBOL_TEXT_PATHS),
            "historical_graphs_excluded": True,
            "causal_graph_status": causal_graph_status,
            "execution_ghosv_imported": False,
            "current_graph_ghosv_assumed": False,
        },
        "RESOLVED_SYMBOL_ENDPOINTS": resolved,
        "PROVEN_SYMBOL_RELATIONS": proven,
        "UNRESOLVED_SYMBOL_ENDPOINTS": unresolved,
        "ORIGINAL_FLOW_PRESERVATION": {
            "preserved": flow_kept,
            "ghv_edge_type_replaces_flow": False,
            "synthetic_edge_count": 0,
            "historical_graph_edges_admitted": 0,
            "ignored_observation_count": len(ignored),
        },
    }


def _is_proven(record: dict[str, Any]) -> bool:
    return (
        record.get("evidence_status") == "BELEGT"
        and record.get("binding_status") == "BELEGT"
        and record.get("relation_class") in OWNER_RELATION_CLASSES
        and record.get("direct_replay_relation") is True
        and record.get("synthetic") is False
        and record.get("membership_granted") is False
        and record.get("universe_ratification") is False
        and record.get("class_derived_from_census_flow") is False
        and record.get("class_derived_from_ghv_type") is False
    )


def _partner_gap(
    texts: Mapping[str, str],
    *,
    relation_id: str,
    partner_id: str,
    uncertainty: str,
    commit: str,
    tree: str,
) -> dict[str, Any]:
    binding_status = "MISSING_DIRECT_REPLAY_BINDING"
    if CYCLE not in texts:
        binding_status = "MISSING_PINNED_TEXT"
    return {
        "relation_id": relation_id,
        "kind": "PARTNER",
        "partner_id": partner_id,
        "endpoint_classification": "UNRESOLVED_EDGE",
        "relation_class": "UNKNOWN",
        "class_basis": "CLASS_NOT_INDEPENDENTLY_EVIDENCED",
        "class_derived_from_census_flow": False,
        "class_derived_from_ghv_type": False,
        "ghv_edge_type": None,
        "ghv_edge_type_replaces_flow": False,
        "evidence_status": "UNGEKLÄRT",
        "binding_status": binding_status,
        "uncertainty": uncertainty,
        "direct_replay_relation": False,
        "membership_granted": False,
        "universe_ratification": False,
        "synthetic": False,
        "commit": commit,
        "tree": tree,
        "active_runtime_proven": False,
        "census_edge_id": None,
        "original_flow_type": "",
    }


def _proof_baseline_differs(text: str, commit: str) -> bool:
    marker = 'BASELINE_ORIGIN_MAIN_SHA = "'
    start = text.find(marker)
    if start < 0:
        return False
    sha = text[start + len(marker) : start + len(marker) + 40]
    if len(sha) != 40 or any(char not in "0123456789abcdef" for char in sha):
        return False
    return sha != commit


def _sort(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(records, key=lambda item: str(item.get("relation_id")))
