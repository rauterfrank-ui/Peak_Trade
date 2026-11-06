"""Post-6940 Authority-Map-/Atlas-guided live-readiness convergence v1 (non-authorizing)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

WORKPACKAGE_ID: Final[str] = "POST_6940_AUTHORITY_MAP_ATLAS_GUIDED_LIVE_READINESS_CONVERGENCE_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/AUTHORITY_MAP_ATLAS_GUIDED_LIVE_READINESS_CONVERGENCE_FROM_POST_6940_MAIN_V1.md"
)
MAP_SOURCE_REL: Final[str] = (
    "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
)
ATLAS_CENSUS_REL: Final[str] = "docs/system_atlas/census/census_meta.yaml"
DECISION_CONFIG: Final[str] = (
    "config/governance/post_6940_live_readiness_convergence_v1_decision_v1.json"
)

PRODUCTIVE_LIVE_DOMAIN_ORDER: Final[tuple[str, ...]] = (
    "treasury_capital_admission",
    "governed_productive_account_equity_authority_producer_v1",
    "eea_universe_inventory_acquisition_v1",
    "universe_cap21",
    "ranking_cap22",
    "selection_cap23",
    "runtime_binding_cap24",
    "mv2_double_play",
    "full_core_live_path_composition_root_v1",
    "order_intent",
    "execution_external_effect",
)


@dataclass(frozen=True)
class EdgeCensusRowV1:
    edge_id: str
    producer: str
    consumer: str
    flow_type: str
    canonical_owner: str
    contract: str
    implemented_capability: bool
    runtime_wired: bool
    runtime_reachable: bool
    admission_satisfied: bool
    authorized: bool
    observed_runtime_evidence: bool
    current_status: str
    blocking_reason: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "EDGE_ID": self.edge_id,
            "PRODUCER": self.producer,
            "CONSUMER": self.consumer,
            "FLOW_TYPE": self.flow_type,
            "CANONICAL_OWNER": self.canonical_owner,
            "CONTRACT": self.contract,
            "IMPLEMENTED_CAPABILITY": self.implemented_capability,
            "RUNTIME_WIRED": self.runtime_wired,
            "RUNTIME_REACHABLE": self.runtime_reachable,
            "ADMISSION_REQUIREMENT": "canonical_owner_and_fail_closed_gates",
            "ADMISSION_SATISFIED": self.admission_satisfied,
            "AUTHORIZED": self.authorized,
            "OBSERVED_RUNTIME_EVIDENCE": self.observed_runtime_evidence,
            "CURRENT_STATUS": self.current_status,
            "BLOCKING_REASON": self.blocking_reason,
        }


def load_map_source_v1(repo_root: Path) -> dict[str, Any]:
    return json.loads((repo_root / MAP_SOURCE_REL).read_text(encoding="utf-8"))


def prove_standing_external_effect_fail_closed_v1() -> dict[str, bool]:
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
        EXTERNAL_EFFECT_AUTHORIZED,
        POST_ALLOWED,
        REAL_VENUE_POST_ALLOWED,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
        AUTONOMY_CAN_MINT_PERMIT,
        AUTONOMY_CAN_POST,
    )

    return {
        "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED is True,
        "POST_ALLOWED": POST_ALLOWED is True,
        "REAL_VENUE_POST_ALLOWED": REAL_VENUE_POST_ALLOWED is True,
        "AUTONOMY_CAN_POST": AUTONOMY_CAN_POST is True,
        "AUTONOMY_CAN_MINT_PERMIT": AUTONOMY_CAN_MINT_PERMIT is True,
    }


def prove_pre_external_boundary_v1() -> dict[str, Any]:
    from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1.proof_v1 import (
        prove_pre_external_to_external_effect_boundary_v1,
    )

    proof = prove_pre_external_to_external_effect_boundary_v1()
    return {
        "boundary_proof_ok": proof.ok is True,
        "guard_failures": list(getattr(proof, "guard_failures", ()) or ()),
        "whole_system_connection_ok": getattr(proof, "whole_system_connection_ok", None),
    }


def readjudicate_historical_blockers_v1(
    *,
    treasury_report: Mapping[str, Any] | None = None,
) -> dict[str, str]:
    treasury_report = treasury_report or {}
    pre_external = bool(treasury_report.get("PRE_EXTERNAL_REACHED"))
    enter_live = (treasury_report.get("ADMISSION_RESULT") or {}).get("enter_live_status")
    return {
        "fresh_trusted_account_equity_acquisition": (
            "BLOCKED_CURRENT"
            if enter_live == "FAIL"
            else "UNKNOWN_WITHOUT_PRIVATE_GET_AUTHORIZATION"
        ),
        "common_epoch_temporal_coherence": "RESOLVED_CURRENT",
        "live_account_bound_trusted_binding": "PARTIAL_CURRENT_SYNTHETIC_E2E_ONLY",
        "full_pretrade_get_conjunction": "PARTIAL_CURRENT_ENTER_LIVE_FAIL_ON_SYNTHETIC_FIXTURE",
        "reference_price_producer_binding": "RESOLVED_CURRENT_EXECUTE_NETWORK_PATH",
        "instrument_metadata_quantity_constraints": "RESOLVED_CURRENT_CAP21_PATH",
        "singular_risk_sizing_authority": "RESOLVED_CURRENT_B05_29P",
        "companion_c2_fraction_to_units": "NOT_ON_CURRENT_PRODUCTIVE_PRE_EXTERNAL_PATH",
        "selection_binding_singular_owner": "RESOLVED_CURRENT",
        "downstream_execution_rerank_reselect": "RESOLVED_CURRENT_NO_RERANK",
        "pre_external_static_proof": "RESOLVED_CURRENT" if pre_external else "BLOCKED_CURRENT",
        "productive_optimization_apply_promotion": "BLOCKED_CURRENT_BY_POLICY",
        "paper_g2_learning_branch": "PARKED_NOT_ON_LIVE_READINESS_WP",
        "external_effect_permit_mint": "BLOCKED_CURRENT_FAIL_CLOSED",
        "continuous_run_authorization": "BLOCKED_CURRENT_OWNER_GO",
    }


def _edge_disposition_map(treasury_report: Mapping[str, Any]) -> dict[str, str]:
    out: dict[str, str] = {}
    for row in treasury_report.get("BOUNDED_KERNEL_EDGE_ADJUDICATION") or []:
        if isinstance(row, dict) and row.get("edge_id"):
            out[str(row["edge_id"])] = str(row.get("disposition") or "UNKNOWN")
    return out


def build_live_edge_census_v1(
    *,
    repo_root: Path,
    treasury_report: Mapping[str, Any],
) -> list[EdgeCensusRowV1]:
    source = load_map_source_v1(repo_root)
    domains = {d["id"]: d for d in source.get("domains") or [] if isinstance(d, dict)}
    edges = [e for e in source.get("edges") or [] if isinstance(e, dict)]
    disp = _edge_disposition_map(treasury_report)
    pre_external = bool(treasury_report.get("PRE_EXTERNAL_REACHED"))
    rows: list[EdgeCensusRowV1] = []
    for edge in edges:
        eid = str(edge.get("id") or "")
        if eid not in disp and edge.get("from_domain") not in PRODUCTIVE_LIVE_DOMAIN_ORDER:
            continue
        if edge.get("from_domain") not in PRODUCTIVE_LIVE_DOMAIN_ORDER and eid not in (
            "intent_to_execution",
            "mv2_executable_pre_external_terminal",
            "eea_acquisition_to_cap21_cap23_persist",
            "binding_to_mv2",
            "treasury_to_account_equity",
        ):
            continue
        disposition = disp.get(eid, "UNKNOWN")
        producer = str(edge.get("from_domain") or "")
        consumer = str(edge.get("to_domain") or "")
        producer_dom = domains.get(producer) or {}
        owner = str(producer_dom.get("canonical_owner_ref") or producer)
        runtime_reached = disposition in {"RUNTIME_PROVEN", "RUNTIME_REACHED"}
        if eid == "intent_to_execution":
            status = "AUTHORITY_BOUNDARY"
            blocking = "EXTERNAL_EFFECT_AUTHORIZATION required; standing flags false"
            admission = False
            authorized = False
        elif disposition == "AUTHORITY_BOUNDARY":
            status = "AUTHORITY_BOUNDARY"
            blocking = treasury_report.get("FIRST_REAL_BLOCKER_ROOT_CAUSE") or (
                "authority boundary"
            )
            admission = False
            authorized = False
        elif runtime_reached:
            status = "RUNTIME_PROVEN"
            blocking = ""
            admission = True
            authorized = eid != "intent_to_execution"
        else:
            status = disposition
            blocking = "not proven in latest synthetic treasury E2E"
            admission = False
            authorized = False
        rows.append(
            EdgeCensusRowV1(
                edge_id=eid,
                producer=producer,
                consumer=consumer,
                flow_type=str(edge.get("flow_type") or "data_or_control"),
                canonical_owner=owner,
                contract=str(edge.get("contract_or_payload") or "")[:120],
                implemented_capability=True,
                runtime_wired=disposition != "UNKNOWN",
                runtime_reachable=runtime_reached
                or (pre_external and eid == "mv2_executable_pre_external_terminal"),
                admission_satisfied=admission,
                authorized=authorized,
                observed_runtime_evidence=runtime_reached,
                current_status=status,
                blocking_reason=blocking,
            )
        )
    return rows


def build_convergence_report_v1(
    *,
    repo_root: Path,
    baseline_sha: str,
    treasury_report: Mapping[str, Any],
    map_sha256: str,
    atlas_sha256: str,
    e2e_run_id: str,
    evidence_root: str,
) -> dict[str, Any]:
    standing = prove_standing_external_effect_fail_closed_v1()
    boundary = prove_pre_external_boundary_v1()
    blockers = readjudicate_historical_blockers_v1(treasury_report=treasury_report)
    census = build_live_edge_census_v1(repo_root=repo_root, treasury_report=treasury_report)
    pre_external = bool(treasury_report.get("PRE_EXTERNAL_REACHED"))
    mechanical_exhausted = bool(treasury_report.get("ALL_IMMEDIATE_MECHANICAL_CLOSURES_EXHAUSTED"))
    first_blocker = (
        "EXTERNAL_EFFECT_AUTHORIZATION"
        if pre_external and mechanical_exhausted
        else str(treasury_report.get("FIRST_REAL_BLOCKER") or "PRODUCTIVE_GRAPH_INCOMPLETE")
    )
    live_mechanically_complete = (
        pre_external
        and mechanical_exhausted
        and boundary.get("boundary_proof_ok") is True
        and not any(standing.values())
    )
    return {
        "WP": WORKPACKAGE_ID,
        "BASELINE_SHA": baseline_sha,
        "MAP_SHA256": map_sha256,
        "ATLAS_SHA256": atlas_sha256,
        "E2E_RUN_ID": e2e_run_id,
        "EVIDENCE_ROOT": evidence_root,
        "PAPER_STATUS": "PARKED",
        "PARTIAL_PAPER_ARTIFACTS_CLASS": (
            "ABORTED_INCOMPLETE_NON_QUALIFYING_BOUNDED_OBSERVATION_PARTIAL_ARTIFACTS"
        ),
        "CURRENT_PRODUCTIVE_LIVE_CAUSAL_PATH": list(PRODUCTIVE_LIVE_DOMAIN_ORDER)
        + ["PRE_EXTERNAL_EFFECT", "intent_to_execution (blocked)"],
        "EDGE_CENSUS": [r.to_dict() for r in census],
        "CURRENT_OBJECT_COUNT": len(load_map_source_v1(repo_root).get("domains") or []),
        "CURRENT_EDGE_COUNT": len(load_map_source_v1(repo_root).get("edges") or []),
        "HISTORICAL_BLOCKERS_READJUDICATED": blockers,
        "PRE_EXTERNAL_REACHED": pre_external,
        "PRE_EXTERNAL_PROOF_CLASSIFICATION": (
            "SYNTHETIC_TREASURY_PUBLIC_GET_MIXED_NO_POST" if pre_external else "NOT_REACHED"
        ),
        "STANDING_EXTERNAL_EFFECT_FLAGS": standing,
        "PRE_EXTERNAL_TO_EXTERNAL_EFFECT_BOUNDARY_PROOF": boundary,
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": (
            "EXTERNAL_EFFECT_AUTHORITY"
            if first_blocker == "EXTERNAL_EFFECT_AUTHORIZATION"
            else treasury_report.get("EXECUTION_BRANCH_BLOCKER_CLASS")
        ),
        "EXACT_NEXT_EDGE": str(
            treasury_report.get("EXECUTION_BRANCH_FIRST_UNCLOSED_EDGE") or "intent_to_execution"
        ),
        "EXACT_NEXT_OWNER_DECISION_REQUIRED": (
            "SCOPED_OWNER_GO_FOR_EXTERNAL_EFFECT_AUTHORIZATION_AND_VENUE_POST"
            if first_blocker == "EXTERNAL_EFFECT_AUTHORIZATION"
            else str(treasury_report.get("FIRST_REMAINING_AUTHORITY_DECISION") or "")
        ),
        "LIVE_READINESS_MECHANICALLY_COMPLETE": live_mechanically_complete,
        "ACTUAL_LIVE_EXTERNAL_EFFECT_AUTHORIZED": False,
        "TREASURY_E2E_REFERENCE": {
            "WHOLE_SYSTEM_E2E_RUN_ID": treasury_report.get("WHOLE_SYSTEM_E2E_RUN_ID"),
            "EVIDENCE_ROOT": treasury_report.get("EVIDENCE_ROOT"),
        },
        "REAL_EXTERNAL_EFFECT_COUNT": 0,
        "VENUE_POST_COUNT": 0,
        "ALL_MECHANICALLY_AUTHORIZED_CLOSURES_EXHAUSTED": mechanical_exhausted,
    }
