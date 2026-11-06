"""Membership and relation-class rules. No automatic ratification."""

from __future__ import annotations

from scripts.ops.mv2_outer_boundary_projector_v1.constants_v1 import (
    FORBIDDEN_AUTHORITY_DERIVATIONS,
    OWNER_RELATION_CLASSES,
    REJECTED_MEMBERSHIP_BASES,
    REPLAY_COMPONENT_ID,
)


def derive_owner_relation_class_v1(
    original_flow_type: str | None,
    corroboration: str | None,
) -> str:
    """Keep the source flow. Do not rename it into an owner class."""

    flow = (original_flow_type or "").strip()
    if flow == "":
        return "UNKNOWN"
    if flow in FORBIDDEN_AUTHORITY_DERIVATIONS:
        return "UNKNOWN"
    if flow not in OWNER_RELATION_CLASSES:
        return "UNKNOWN"
    if corroboration is None or not str(corroboration).strip():
        return "UNKNOWN"
    token = str(corroboration).strip().upper()
    if token in FORBIDDEN_AUTHORITY_DERIVATIONS:
        return "UNKNOWN"
    if flow == "AUTHORITY" and any(item in token for item in FORBIDDEN_AUTHORITY_DERIVATIONS):
        return "UNKNOWN"
    return flow


def classify_membership_candidate_v1(candidate: dict[str, object]) -> dict[str, object]:
    """Promote a symbol only when every evidence gate passes."""

    basis = str(candidate.get("basis") or "")
    component_id = str(candidate.get("component_id") or "")
    rejected = basis in REJECTED_MEMBERSHIP_BASES
    gates = (
        bool(candidate.get("exists_on_pin"))
        and bool(candidate.get("owner_places_in_joint_core"))
        and bool(candidate.get("code_confirms_role"))
        and bool(candidate.get("diff_empty"))
        and not rejected
        and not bool(candidate.get("used_filename"))
        and not bool(candidate.get("used_directory"))
        and not bool(candidate.get("used_census"))
        and not bool(candidate.get("used_landscape"))
        and not bool(candidate.get("used_graph_neighborhood"))
    )
    classification = "PROVEN_MV2_MEMBER" if gates else "POSSIBLE_MV2_MEMBER_UNCLASSIFIED"
    return {
        "component_id": component_id,
        "classification": classification,
        "automatic_promotion": False,
        "universe_ratification": False,
        "basis": basis if basis else "INSUFFICIENT_EVIDENCE",
        "scope": candidate.get("scope") or "UNSPECIFIED",
        "proof_status": "SYMBOL_ROLE_ONLY" if gates else "NOT_PROVEN",
        "uncertainty": (
            "FULL_UNIVERSE_BOUNDARY_UNRATIFIED"
            if gates
            else "MEMBERSHIP_GATES_INCOMPLETE_OR_REJECTED_BASIS"
        ),
        "countercheck": {
            "rejected_bases": sorted(REJECTED_MEMBERSHIP_BASES),
            "decision_path_anchor_is_automatic_member": False,
        },
    }


def empty_member_record_rejected_v1(component_id: str, basis: str) -> dict[str, object]:
    return classify_membership_candidate_v1(
        {
            "component_id": component_id,
            "basis": basis,
            "exists_on_pin": True,
            "owner_places_in_joint_core": False,
            "code_confirms_role": False,
            "diff_empty": False,
            "scope": "REJECTED_NON_EVIDENTIAL_BASIS",
        }
    )


def replay_membership_candidate_v1(
    *,
    exists_on_pin: bool,
    owner_places_in_joint_core: bool,
    code_confirms_role: bool,
    diff_empty: bool,
) -> dict[str, object]:
    return {
        "component_id": REPLAY_COMPONENT_ID,
        "basis": "OWNER_DECISION_ROLE_PLUS_CODE_PLUS_EMPTY_DIFF",
        "exists_on_pin": exists_on_pin,
        "owner_places_in_joint_core": owner_places_in_joint_core,
        "code_confirms_role": code_confirms_role,
        "diff_empty": diff_empty,
        "used_filename": False,
        "used_directory": False,
        "used_census": False,
        "used_landscape": False,
        "used_graph_neighborhood": False,
        "scope": "DECISION_START_SYMBOL_ONLY",
    }
