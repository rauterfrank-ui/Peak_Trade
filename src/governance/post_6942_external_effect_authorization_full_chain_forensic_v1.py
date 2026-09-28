"""Post-6942 EXTERNAL_EFFECT_AUTHORIZATION full-chain forensic (non-authorizing).

Extends post-6941 intent_to_execution seam adjudication through credential-access and
material-load policy admissions, venue-POST admission evaluation, and one-shot join
standing boundary — without permit mint perform, credential load, or venue POST.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

from src.governance.post_6941_pre_external_intent_to_execution_seam_adjudication_v1 import (
    probe_intent_to_execution_seam_v1,
    resolve_first_real_blocker_v1,
    summarize_canonical_decision_chain_v1,
)

WORKPACKAGE_ID: Final[str] = "POST_6942_EXTERNAL_EFFECT_AUTHORIZATION_FULL_CHAIN_FORENSIC_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/AUTHORITY_MAP_ATLAS_GUIDED_EXTERNAL_EFFECT_AUTHORIZATION_FULL_CHAIN_FROM_POST_6942_MAIN_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/post_6942_external_effect_authorization_full_chain_forensic_v1_decision_v1.json"
)
MAP_SOURCE_REL: Final[str] = (
    "config/governance/current_system_interaction_authority_map_v1/source_v1.json"
)
ATLAS_CENSUS_REL: Final[str] = "docs/system_atlas/census/census_meta.yaml"

CANONICAL_DECISION_CHAIN: Final[tuple[tuple[str, str], ...]] = (
    (
        "external_effect_authorization_policy",
        "config/governance/external_effect_authorization_policy_v1_decision_v1.json",
    ),
    (
        "standing_external_effect_lift",
        "config/governance/standing_external_effect_lift_owner_go_v1_decision.json",
    ),
    (
        "external_effect_permit_mint_policy_admission",
        "config/governance/external_effect_permit_mint_owner_go_v1_decision.json",
    ),
    (
        "checkout_independent_credential_access",
        "config/governance/checkout_independent_credential_access_owner_go_v1_decision.json",
    ),
    (
        "real_keychain_or_credential_material_load",
        "config/governance/real_keychain_access_or_credential_material_load_owner_go_v1_decision.json",
    ),
    (
        "actual_venue_post_owner_go_record",
        "config/governance/current_productive_actual_venue_post_owner_go_v1_decision.json",
    ),
)

PERMIT_MINT_OWNER_GO_TOKEN: Final[str] = "EXTERNAL_EFFECT_PERMIT_MINT_OWNER_GO"
CREDENTIAL_ACCESS_OWNER_GO_TOKEN: Final[str] = "CHECKOUT_INDEPENDENT_CREDENTIAL_ACCESS_OWNER_GO"
MATERIAL_LOAD_OWNER_GO_TOKEN: Final[str] = (
    "REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD_OWNER_GO"
)
VENUE_POST_OWNER_GO_TOKEN: Final[str] = (
    "OWNER_GO_CURRENT_PRODUCTIVE_ACTUAL_VENUE_POST_WITH_FRESH_ENVELOPE_BOUND_SINGLE_USE_PERMIT_V1"
)
K1_OPAQUE_SIGNING_NEXT_BLOCKER: Final[str] = (
    "OWNER_GO_CURRENT_PRODUCTIVE_K1_REAL_KEYCHAIN_ACCESS_AND_OPAQUE_SIGNING_HANDLE_PRE_POST_V1"
)


@dataclass(frozen=True)
class AuthorityLayerRowV1:
    layer_id: str
    epistemic_class: str
    normative_owner: str
    decision_record: str
    admission_granted: bool | None
    performed: bool | None
    reason_codes: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "LAYER_ID": self.layer_id,
            "EPISTEMIC_CLASS": self.epistemic_class,
            "NORMATIVE_OWNER": self.normative_owner,
            "DECISION_RECORD": self.decision_record,
            "ADMISSION_GRANTED": self.admission_granted,
            "PERFORMED": self.performed,
            "REASON_CODES": list(self.reason_codes),
        }


def load_canonical_decision_v1(repo_root: Path, rel_path: str) -> dict[str, Any]:
    return json.loads((repo_root / rel_path).read_text(encoding="utf-8"))


def probe_downstream_policy_and_sink_chain_v1(*, repo_root: Path) -> dict[str, Any]:
    from src.governance.checkout_independent_credential_access_gate_binding_v1 import (
        evaluate_credential_access_bound_checkout_independent_capability_seam_v1,
    )
    from src.governance.current_productive_real_venue_post_admission_v1 import (
        evaluate_real_venue_post_admission_v1,
    )
    from src.governance.real_keychain_access_or_credential_material_load_gate_binding_v1 import (
        evaluate_material_load_bound_credential_acquisition_seam_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_one_shot_fresh_envelope_permit_mint_durable_consume_and_post_join_v1 import (
        prove_one_shot_join_standing_boundary_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.current_productive_governed_cycle_orchestrator_v1 import (
        AUTONOMY_CAN_MINT_PERMIT,
        AUTONOMY_CAN_POST,
    )

    seam_6941 = probe_intent_to_execution_seam_v1(repo_root=repo_root)
    cred_bound = evaluate_credential_access_bound_checkout_independent_capability_seam_v1(
        repo_root=repo_root
    )
    material_bound = evaluate_material_load_bound_credential_acquisition_seam_v1(
        repo_root=repo_root
    )
    post_admission = evaluate_real_venue_post_admission_v1(
        post_owner_go=None,
        one_shot_real_post=True,
        permit=None,
        store_root=None,
    )
    one_shot_boundary = prove_one_shot_join_standing_boundary_v1()

    full_policy_admissions = (
        seam_6941.get("POLICY_CHAIN_ADMISSIONS_RUNTIME_PROVEN") is True
        and cred_bound.credential_access_admission_granted is True
        and material_bound.material_load_admission_granted is True
        and cred_bound.credential_access_performed is False
        and material_bound.post_allowed is False
    )

    layers: list[AuthorityLayerRowV1] = []
    for layer_id, rel in CANONICAL_DECISION_CHAIN:
        decision = load_canonical_decision_v1(repo_root, rel)
        if layer_id == "external_effect_authorization_policy":
            admission = seam_6941.get("POLICY_BOUND_GATE", {}).get("policy_admission_granted")
            performed = None
        elif layer_id == "standing_external_effect_lift":
            admission = seam_6941.get("LIFT_BOUND_GATE", {}).get("lift_admission_granted")
            performed = None
        elif layer_id == "external_effect_permit_mint_policy_admission":
            admission = seam_6941.get("PERMIT_MINT_BOUND_SEAM", {}).get(
                "permit_mint_admission_granted"
            )
            performed = seam_6941.get("PERMIT_MINT_BOUND_SEAM", {}).get("permit_mint_performed")
        elif layer_id == "checkout_independent_credential_access":
            admission = cred_bound.credential_access_admission_granted
            performed = cred_bound.credential_access_performed
        elif layer_id == "real_keychain_or_credential_material_load":
            admission = material_bound.material_load_admission_granted
            performed = None
        else:
            admission = post_admission.post_admission_granted is False
            performed = post_admission.real_venue_post_performed

        layers.append(
            AuthorityLayerRowV1(
                layer_id=layer_id,
                epistemic_class="CANONICAL_AUTHORITY",
                normative_owner=str(decision.get("workpackage_id") or layer_id),
                decision_record=rel,
                admission_granted=admission if isinstance(admission, bool) else bool(admission),
                performed=performed if isinstance(performed, (bool, type(None))) else False,
                reason_codes=(),
            )
        )

    return {
        "POST_6941_SEAM_PROBE": seam_6941,
        "CREDENTIAL_ACCESS_BOUND": {
            "credential_access_admission_granted": cred_bound.credential_access_admission_granted,
            "credential_access_performed": cred_bound.credential_access_performed,
            "real_credential_access_performed": cred_bound.real_credential_access_performed,
            "real_secret_load_performed": cred_bound.real_secret_load_performed,
        },
        "MATERIAL_LOAD_BOUND": {
            "material_load_admission_granted": material_bound.material_load_admission_granted,
            "real_keychain_access_authorized": material_bound.real_keychain_access_authorized,
            "credential_material_load_authorized": material_bound.credential_material_load_authorized,
            "request_signing_authorized": material_bound.request_signing_authorized,
            "post_allowed": material_bound.post_allowed,
        },
        "VENUE_POST_ADMISSION": {
            "admission_status": post_admission.admission_status,
            "post_admission_granted": post_admission.post_admission_granted,
            "post_owner_go_required": post_admission.post_owner_go_required,
            "next_owner_go": post_admission.next_owner_go,
            "reason_codes": list(post_admission.reason_codes),
        },
        "ONE_SHOT_JOIN_STANDING_BOUNDARY": one_shot_boundary,
        "AUTONOMY_FLAGS": {
            "AUTONOMY_CAN_MINT_PERMIT": AUTONOMY_CAN_MINT_PERMIT is True,
            "AUTONOMY_CAN_POST": AUTONOMY_CAN_POST is True,
        },
        "AUTHORITY_LAYERS": [row.to_dict() for row in layers],
        "FULL_POLICY_CHAIN_ADMISSIONS_RUNTIME_PROVEN": full_policy_admissions,
    }


def build_canonical_authority_chain_narrative_v1() -> list[dict[str, str]]:
    return [
        {
            "step": "PRE_EXTERNAL_EFFECT",
            "owner": "ops.pre_external_to_external_effect_boundary_bounded_wp_v1",
            "effect": "RUNTIME_PROVEN; no venue POST",
        },
        {
            "step": "intent_to_execution",
            "owner": "CSIA edge index; gates in src/governance/* and composition_root",
            "effect": "AUTHORITY_BLOCKED at operational sinks",
        },
        {
            "step": "external_effect_authorization_policy",
            "owner": "governance.external_effect_authorization_policy_v1",
            "effect": "policy admission granted; standing import pins remain false",
        },
        {
            "step": "standing_external_effect_lift",
            "owner": "governance.standing_external_effect_lift_policy_v1",
            "effect": "lift admission granted; no standing lift apply",
        },
        {
            "step": "permit_mint_admission",
            "owner": "governance.external_effect_permit_mint_policy_v1",
            "effect": "governed permit-mint policy admission; permit_mint_performed=false",
        },
        {
            "step": "credential_access_admission",
            "owner": "governance.checkout_independent_credential_access_policy_v1",
            "effect": "policy admission; credential_access_performed=false",
        },
        {
            "step": "material_load_admission",
            "owner": "governance.real_keychain_access_or_credential_material_load_policy_v1",
            "effect": "policy admission; real_secret_load_performed=false",
        },
        {
            "step": "permit_bound_send_envelope",
            "owner": "ops.full_core_live_path_composition_root_v1.envelope_bound_external_effect_send_seam_v1",
            "effect": "fail-closed NO_PERMIT without scoped permit object",
        },
        {
            "step": "venue_post_sink",
            "owner": "governed_productive_account_equity_authority_producer_v1."
            "current_productive_actual_venue_post_with_fresh_envelope_bound_single_use_permit_v1",
            "effect": "requires VENUE_POST_OWNER_GO; POST_COUNT=0 until invoked",
        },
    ]


def resolve_operational_blockers_v1(
    *,
    chain_probe: Mapping[str, Any],
) -> tuple[str, str, str, str, str]:
    """Return umbrella blocker, class, first irreversible op, mint owner, credential owner."""

    first_irreversible = "REAL_KEYCHAIN_ACCESS_OR_CREDENTIAL_MATERIAL_LOAD"
    if chain_probe.get("FULL_POLICY_CHAIN_ADMISSIONS_RUNTIME_PROVEN") is not True:
        return (
            "EXTERNAL_EFFECT_AUTHORIZATION",
            "POLICY_CHAIN_INCOMPLETE",
            "PRE_EXTERNAL_OR_POLICY_ADMISSION",
            PERMIT_MINT_OWNER_GO_TOKEN,
            CREDENTIAL_ACCESS_OWNER_GO_TOKEN,
        )
    return (
        "EXTERNAL_EFFECT_AUTHORIZATION",
        "OPERATIONAL_EXTERNAL_EFFECT_PERFORMANCE_BLOCKED",
        first_irreversible,
        PERMIT_MINT_OWNER_GO_TOKEN,
        MATERIAL_LOAD_OWNER_GO_TOKEN,
    )


def build_full_chain_forensic_report_v1(
    *,
    repo_root: Path,
    baseline_sha: str,
    treasury_report: Mapping[str, Any],
    map_sha256: str,
    atlas_sha256: str,
    e2e_run_id: str,
    evidence_root: str,
) -> dict[str, Any]:
    chain = probe_downstream_policy_and_sink_chain_v1(repo_root=repo_root)
    seam_6941 = chain["POST_6941_SEAM_PROBE"]
    first_blocker, blocker_class, first_irreversible, mint_owner, cred_owner = (
        resolve_operational_blockers_v1(chain_probe=chain)
    )
    _, blocker_class_6941, blocker_subtype_6941 = resolve_first_real_blocker_v1(
        treasury_report=treasury_report,
        seam_probe=seam_6941,
    )
    pre_external = bool(treasury_report.get("PRE_EXTERNAL_REACHED")) or bool(
        seam_6941.get("PRE_EXTERNAL_BOUNDARY_OK")
    )
    decision_chain = summarize_canonical_decision_chain_v1(repo_root=repo_root)
    material_decision = load_canonical_decision_v1(repo_root, CANONICAL_DECISION_CHAIN[4][1])
    fixpoint = (
        pre_external
        and chain.get("FULL_POLICY_CHAIN_ADMISSIONS_RUNTIME_PROVEN") is True
        and seam_6941.get("INVOKE_SINK_PROBE") == "FullCoreExternalEffectNotAuthorizedError"
        and seam_6941.get("ENVELOPE_SEAM_PROBE")
        in {"NO_PERMIT", "TRANSPORT_MISSING", "DURABLE_STORE_REQUIRED"}
        and chain["VENUE_POST_ADMISSION"]["post_admission_granted"] is False
    )
    return {
        "WP": WORKPACKAGE_ID,
        "BASELINE_SHA": baseline_sha,
        "MAP_SHA256": map_sha256,
        "ATLAS_SHA256": atlas_sha256,
        "E2E_RUN_ID": e2e_run_id,
        "EVIDENCE_ROOT": evidence_root,
        "PAPER_STATUS": "PARKED",
        "PRE_EXTERNAL_EFFECT_REACHED": pre_external,
        "CANONICAL_AUTHORITY_CHAIN": build_canonical_authority_chain_narrative_v1(),
        "CANONICAL_DECISION_CHAIN_SUMMARY": decision_chain,
        "DOWNSTREAM_CHAIN_PROBE": chain,
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "BLOCKER_SUBTYPE_6941": blocker_subtype_6941,
        "BLOCKER_CLASS_6941": blocker_class_6941,
        "ADJUDICATED_CONCLUSIONS": {
            "policy_admissions_through_material_load_runtime_proven": chain.get(
                "FULL_POLICY_CHAIN_ADMISSIONS_RUNTIME_PROVEN"
            ),
            "permit_mint_admission_not_permit_mint_perform": (
                seam_6941.get("PERMIT_MINT_BOUND_SEAM", {}).get("permit_mint_performed") is False
            ),
            "credential_and_material_load_admissions_distinct_from_perform": True,
            "separate_owner_go_required_for_mint_perform_credential_load_and_venue_post": True,
            "map_atlas_are_navigation_only": True,
        },
        "PERMIT_MINT_OWNER": mint_owner,
        "CREDENTIAL_ACCESS_OWNER": cred_owner,
        "VENUE_POST_OWNER": VENUE_POST_OWNER_GO_TOKEN,
        "K1_OPAQUE_SIGNING_NEXT_OWNER": K1_OPAQUE_SIGNING_NEXT_BLOCKER,
        "PERMIT_SCOPE_REQUIREMENTS": {
            "single_use": True,
            "max_post_count": 1,
            "envelope_digest_binding": True,
            "authority_ref_must_match_post_owner_go": VENUE_POST_OWNER_GO_TOKEN,
            "standing_external_effect_authorized_must_remain_false": True,
        },
        "POST_PRECONDITIONS": [
            "PRE_EXTERNAL_RUNTIME_PROVEN",
            "FULL_POLICY_CHAIN_ADMISSIONS",
            "FRESH_FINAL_ORDER_ENVELOPE",
            "EXTERNAL_EFFECT_PERMIT_MINTED_FOR_ENVELOPE",
            "DURABLE_SENT_INITIATED_CONSUME",
            "K1_OPAQUE_SIGNING_HANDLE_WITHOUT_MATERIAL_LOAD",
            "UNCONSUMED_VENUE_POST_OWNER_GO",
            "TRANSPORT_TO_AUTHORIZED_HOST",
        ],
        "FIRST_IRREVERSIBLE_OPERATION": first_irreversible,
        "FIRST_REAL_BLOCKER_OPERATIONAL": chain["ONE_SHOT_JOIN_STANDING_BOUNDARY"].get(
            "FIRST_REAL_BLOCKER"
        ),
        "EXACT_OWNER_GO_REQUIRED": [
            f"{MATERIAL_LOAD_OWNER_GO_TOKEN} (perform real Keychain / credential material load)",
            f"{K1_OPAQUE_SIGNING_NEXT_BLOCKER} (opaque signing handle pre-POST)",
            f"{VENUE_POST_OWNER_GO_TOKEN} (at most one venue trade-order POST)",
        ],
        "NAVIGATION_ONLY_FINDINGS": [
            "Post-6941 fixpoint preserved; post-6942 extends through credential/material-load admissions.",
            f"Material-load decision next_genuine_blocker={material_decision.get('next_genuine_blocker')}",
        ],
        "OPEN_CONFLICTS": [],
        "FIXPOINT_REACHED": fixpoint,
        "NEXT_WP_ANCHOR": (
            "SCOPED_OWNER_GO_FOR_REAL_KEYCHAIN_MATERIAL_LOAD_THEN_K1_THEN_VENUE_POST"
            if fixpoint
            else "CLOSE_POLICY_OR_PRE_EXTERNAL_GAP"
        ),
        "EXTERNAL_EFFECT_AUTHORIZED": False,
        "EXTERNAL_EFFECT_PERMIT_MINTED": False,
        "CREDENTIALS_ACCESSED": False,
        "POST_ALLOWED": False,
        "REAL_EXTERNAL_EFFECT_COUNT": 0,
        "VENUE_POST_COUNT": 0,
        "TREASURY_E2E_REFERENCE": {
            "WHOLE_SYSTEM_E2E_RUN_ID": treasury_report.get("WHOLE_SYSTEM_E2E_RUN_ID"),
            "EVIDENCE_ROOT": treasury_report.get("EVIDENCE_ROOT"),
        },
    }
