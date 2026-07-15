# src/trading/master_v2/evaluate_double_play_authority_boundary_v0.py
"""
Evaluate Double Play Authority Boundary v0 (Remediation Slice E + Slice 4 closeout).

Fail-closed authority classification for ops ``evaluate_double_play`` and offline
scenario-replay duplicate decision paths versus the canonical Master V2 offline
Double-Play composition stack / integrated replay owner. Consolidates authority
boundaries only — no runtime start, orders, adapter submission, credentials,
packet sync, or algorithm changes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Tuple

EVALUATE_DOUBLE_PLAY_AUTHORITY_BOUNDARY_LAYER_VERSION = "v0"
EVALUATE_DOUBLE_PLAY_AUTHORITY_BOUNDARY_OWNER = (
    "trading.master_v2.evaluate_double_play_authority_boundary_v0"
)
PACKAGE_MARKER = "EVALUATE_DOUBLE_PLAY_AUTHORITY_BOUNDARY_V0=true"

SLICE_E_STATUS = "EVALUATE_DOUBLE_PLAY_AUTHORITY_CONSOLIDATED"

CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER = (
    "trading.master_v2.double_play_composition_matrix_v1"
)
CANONICAL_DOUBLE_PLAY_OFFLINE_REPLAY_CHAIN_OWNER = (
    "trading.master_v2.integrated_offline_trading_logic_replay_v1"
)

OPS_EVALUATE_DOUBLE_PLAY_CALLABLE = "src.ops.double_play.specialists.evaluate_double_play"
OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY = "LEGACY_NON_AUTHORITATIVE"

OFFLINE_SCENARIO_REPLAY_CALLABLE = (
    "trading.master_v2.offline_double_play_scenario_replay_v0."
    "run_offline_double_play_scenario_replay_v0"
)
OFFLINE_SCENARIO_REPLAY_AUTHORITY = "LEGACY_NON_AUTHORITATIVE"

LEGACY_DUPLICATE_DECISION_PATH_AUTHORITY = "LEGACY_NON_AUTHORITATIVE"
REASON_LEGACY_DUPLICATE_DECISION_PATH_SYSTEM_ECONOMIC_EVIDENCE_BLOCKED = (
    "legacy_duplicate_decision_path_system_economic_evidence_blocked"
)

LIVE_GATES_DOUBLE_PLAY_ANNOTATION_ROLE = "LEGACY_NON_AUTHORITATIVE_ANNOTATION_ONLY"
LIVE_GATES_DOUBLE_PLAY_ELIGIBILITY_COUPLING = "false"

MASTER_V2_DOUBLE_PLAY_AUTHORITY_USED = "false"
RUNTIME_REWIRE_STATUS = "PARTIAL"
ZERO_ORDER_RUNTIME_READY = "false"
ZERO_ORDER_RUNTIME_EXECUTION_SUSPENDED = "true"

NEXT_REMEDIATION_SLICE = (
    "RUNBOOK_STEP_29R_RUNTIME_REWIRE_V1_IMPLEMENTATION (blocked; separate GO required)"
)

_LEGACY_DUPLICATE_DECISION_PATH_IDS = frozenset(
    {
        OPS_EVALUATE_DOUBLE_PLAY_CALLABLE,
        OFFLINE_SCENARIO_REPLAY_CALLABLE,
        OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY,
        OFFLINE_SCENARIO_REPLAY_AUTHORITY,
        LEGACY_DUPLICATE_DECISION_PATH_AUTHORITY,
    }
)


class LegacyDuplicateDecisionPathSystemEvidenceBlockedError(RuntimeError):
    """Raised when a legacy duplicate decision path requests system economic evidence."""


@dataclass(frozen=True)
class LegacyDoublePlayLiveGatesAnnotationV0:
    """Non-authorizing live_gates annotation envelope for ops evaluate_double_play."""

    enabled: bool
    active_specialist: str
    switch_state: Mapping[str, Any]
    reasons: Tuple[str, ...]
    details: Mapping[str, Any]
    authority_role: str = LIVE_GATES_DOUBLE_PLAY_ANNOTATION_ROLE
    canonical_offline_authority_owner: str = CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER
    ops_evaluate_double_play_authority: str = OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY
    eligibility_coupling: str = LIVE_GATES_DOUBLE_PLAY_ELIGIBILITY_COUPLING
    master_v2_double_play_authority_used: str = MASTER_V2_DOUBLE_PLAY_AUTHORITY_USED


def classify_ops_evaluate_double_play_authority() -> str:
    return OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY


def classify_offline_scenario_replay_authority() -> str:
    return OFFLINE_SCENARIO_REPLAY_AUTHORITY


def assert_legacy_duplicate_decision_path_blocks_system_economic_evidence_v0(
    *,
    path_id: str,
    system_economic_evidence_requested: bool,
) -> None:
    """Fail-closed guard: legacy duplicate decision paths cannot emit system evidence.

    Demo / fixture / technical comparison callers remain usable when
    ``system_economic_evidence_requested`` is false. Any request for canonical /
    system economic evidence from these paths is blocked.
    """
    normalized = str(path_id or "").strip()
    if not normalized or normalized not in _LEGACY_DUPLICATE_DECISION_PATH_IDS:
        raise LegacyDuplicateDecisionPathSystemEvidenceBlockedError(
            REASON_LEGACY_DUPLICATE_DECISION_PATH_SYSTEM_ECONOMIC_EVIDENCE_BLOCKED
        )
    if system_economic_evidence_requested:
        raise LegacyDuplicateDecisionPathSystemEvidenceBlockedError(
            REASON_LEGACY_DUPLICATE_DECISION_PATH_SYSTEM_ECONOMIC_EVIDENCE_BLOCKED
        )


def declare_legacy_duplicate_decision_path_v0(
    *,
    path_id: str,
    system_economic_evidence_requested: bool = False,
) -> str:
    """Mark a duplicate decision path as non-authoritative and enforce the guard."""
    assert_legacy_duplicate_decision_path_blocks_system_economic_evidence_v0(
        path_id=path_id,
        system_economic_evidence_requested=system_economic_evidence_requested,
    )
    return LEGACY_DUPLICATE_DECISION_PATH_AUTHORITY


def build_legacy_double_play_live_gates_annotation(
    dp_decision: Any,
) -> Mapping[str, Any]:
    """Wrap ops ``DoublePlayDecision`` for live_gates ``details['double_play']`` only."""
    base_details = dict(getattr(dp_decision, "details", {}) or {})
    annotation = LegacyDoublePlayLiveGatesAnnotationV0(
        enabled=bool(getattr(dp_decision, "enabled", False)),
        active_specialist=str(getattr(dp_decision, "active_specialist", "")),
        switch_state=dict(getattr(dp_decision, "switch_state", {}) or {}),
        reasons=tuple(getattr(dp_decision, "reasons", ()) or ()),
        details=base_details,
    )
    return {
        "enabled": annotation.enabled,
        "active_specialist": annotation.active_specialist,
        "switch_state": dict(annotation.switch_state),
        "reasons": list(annotation.reasons),
        "legacy_annotation": dict(base_details),
        "authority_boundary": {
            "authority_role": annotation.authority_role,
            "canonical_offline_authority_owner": annotation.canonical_offline_authority_owner,
            "ops_evaluate_double_play_authority": annotation.ops_evaluate_double_play_authority,
            "eligibility_coupling": annotation.eligibility_coupling,
            "master_v2_double_play_authority_used": annotation.master_v2_double_play_authority_used,
        },
    }


def build_slice_e_status_fields_v0() -> Mapping[str, str]:
    return {
        "SLICE_E_STATUS": SLICE_E_STATUS,
        "CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER": CANONICAL_DOUBLE_PLAY_OFFLINE_AUTHORITY_OWNER,
        "CANONICAL_DOUBLE_PLAY_OFFLINE_REPLAY_CHAIN_OWNER": (
            CANONICAL_DOUBLE_PLAY_OFFLINE_REPLAY_CHAIN_OWNER
        ),
        "OPS_EVALUATE_DOUBLE_PLAY_CALLABLE": OPS_EVALUATE_DOUBLE_PLAY_CALLABLE,
        "OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY": OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY,
        "LIVE_GATES_DOUBLE_PLAY_ANNOTATION_ROLE": LIVE_GATES_DOUBLE_PLAY_ANNOTATION_ROLE,
        "LIVE_GATES_DOUBLE_PLAY_ELIGIBILITY_COUPLING": LIVE_GATES_DOUBLE_PLAY_ELIGIBILITY_COUPLING,
        "MASTER_V2_DOUBLE_PLAY_AUTHORITY_USED": MASTER_V2_DOUBLE_PLAY_AUTHORITY_USED,
        "EVALUATE_DOUBLE_PLAY_SLICE_E_RESIDUAL": "false",
        "CANONICAL_CORE_SINGLE_SSOT_CONFIRMED": "true",
        "RUNTIME_REWIRE_STATUS": RUNTIME_REWIRE_STATUS,
        "ZERO_ORDER_RUNTIME_READY": ZERO_ORDER_RUNTIME_READY,
        "ZERO_ORDER_RUNTIME_EXECUTION_SUSPENDED": ZERO_ORDER_RUNTIME_EXECUTION_SUSPENDED,
        "NEXT_REMEDIATION_SLICE": NEXT_REMEDIATION_SLICE,
    }


def build_slice_4_legacy_boundary_status_fields_v0() -> Mapping[str, str]:
    """Slice-4 closeout fields for legacy duplicate decision path authority."""
    return {
        "OFFLINE_SCENARIO_REPLAY_CALLABLE": OFFLINE_SCENARIO_REPLAY_CALLABLE,
        "OFFLINE_SCENARIO_REPLAY_AUTHORITY": OFFLINE_SCENARIO_REPLAY_AUTHORITY,
        "OPS_EVALUATE_DOUBLE_PLAY_CALLABLE": OPS_EVALUATE_DOUBLE_PLAY_CALLABLE,
        "OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY": OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY,
        "LEGACY_DUPLICATE_DECISION_PATH_AUTHORITY": LEGACY_DUPLICATE_DECISION_PATH_AUTHORITY,
        "LEGACY_SYSTEM_ECONOMIC_EVIDENCE_BLOCKED": "true",
        "CANONICAL_DOUBLE_PLAY_OFFLINE_REPLAY_CHAIN_OWNER": (
            CANONICAL_DOUBLE_PLAY_OFFLINE_REPLAY_CHAIN_OWNER
        ),
        "CANONICAL_TOTAL_DECISION_OWNER": CANONICAL_DOUBLE_PLAY_OFFLINE_REPLAY_CHAIN_OWNER,
    }
