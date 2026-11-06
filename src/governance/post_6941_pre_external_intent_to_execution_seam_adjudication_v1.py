"""Post-6941 PRE_EXTERNAL → intent_to_execution seam adjudication (non-authorizing)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final, Mapping

WORKPACKAGE_ID: Final[str] = "POST_6941_PRE_EXTERNAL_INTENT_TO_EXECUTION_SEAM_ADJUDICATION_V1"
NORMATIVE_SPEC: Final[str] = (
    "docs/ops/specs/AUTHORITY_MAP_ATLAS_GUIDED_PRE_EXTERNAL_INTENT_TO_EXECUTION_SEAM_ADJUDICATION_FROM_POST_6941_MAIN_V1.md"
)
DECISION_CONFIG: Final[str] = (
    "config/governance/post_6941_pre_external_intent_to_execution_seam_adjudication_v1_decision_v1.json"
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
        "external_effect_permit_mint",
        "config/governance/external_effect_permit_mint_owner_go_v1_decision.json",
    ),
    (
        "checkout_independent_credential_access",
        "config/governance/checkout_independent_credential_access_owner_go_v1_decision.json",
    ),
)


@dataclass(frozen=True)
class SeamLayerProbeV1:
    layer_id: str
    epistemic_class: str
    runtime_status: str
    admission_granted: bool | None
    performed: bool | None
    reason_codes: tuple[str, ...]
    canonical_next_blocker: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "LAYER_ID": self.layer_id,
            "EPISTEMIC_CLASS": self.epistemic_class,
            "RUNTIME_STATUS": self.runtime_status,
            "ADMISSION_GRANTED": self.admission_granted,
            "PERFORMED": self.performed,
            "REASON_CODES": list(self.reason_codes),
            "CANONICAL_NEXT_BLOCKER": self.canonical_next_blocker,
        }


def load_canonical_decision_v1(repo_root: Path, rel_path: str) -> dict[str, Any]:
    return json.loads((repo_root / rel_path).read_text(encoding="utf-8"))


def summarize_canonical_decision_chain_v1(*, repo_root: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for layer_id, rel in CANONICAL_DECISION_CHAIN:
        decision = load_canonical_decision_v1(repo_root, rel)
        rows.append(
            {
                "layer_id": layer_id,
                "decision_config": rel,
                "earliest_unclosed_boundary": decision.get("earliest_unclosed_boundary"),
                "next_genuine_blocker": decision.get("next_genuine_blocker"),
                "owner_go": decision.get("owner_go"),
                "post_allowed": decision.get("post_allowed"),
                "permit_mint_authorized": decision.get(
                    "permit_mint_authorized", decision.get("governed_permit_mint_authorized")
                ),
                "permit_mint_performed": decision.get("permit_mint_performed"),
                "credential_access_performed": decision.get("credential_access_performed"),
            }
        )
    return rows


def probe_intent_to_execution_seam_v1(*, repo_root: Path) -> dict[str, Any]:
    from src.governance.external_effect_authorization_policy_gate_binding_v1 import (
        evaluate_policy_bound_external_effect_gate_v1,
    )
    from src.governance.external_effect_authorization_policy_v1 import (
        evaluate_external_effect_policy_admission_v1,
    )
    from src.governance.external_effect_permit_mint_gate_binding_v1 import (
        evaluate_permit_mint_bound_external_effect_permit_seam_v1,
    )
    from src.governance.standing_external_effect_lift_gate_binding_v1 import (
        evaluate_lift_bound_external_effect_gate_v1,
    )
    from src.governance.standing_external_effect_lift_policy_v1 import (
        evaluate_standing_external_effect_lift_admission_v1,
    )
    from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1.intent_to_execution_seam_sink_probe_v1 import (
        probe_envelope_bound_send_seam_without_permit_v1,
        probe_import_time_invoke_sink_v1,
    )
    from src.ops.full_core_live_path_composition_root_v1.constants_v1 import (
        EXTERNAL_EFFECT_AUTHORIZED,
        POST_ALLOWED,
        REAL_VENUE_POST_ALLOWED,
    )
    from src.ops.pre_external_to_external_effect_boundary_bounded_wp_v1.proof_v1 import (
        prove_pre_external_to_external_effect_boundary_v1,
    )

    pre_external = prove_pre_external_to_external_effect_boundary_v1()
    policy_admission = evaluate_external_effect_policy_admission_v1(repo_root=repo_root)
    policy_bound = evaluate_policy_bound_external_effect_gate_v1(repo_root=repo_root)
    standing_lift = evaluate_standing_external_effect_lift_admission_v1(repo_root=repo_root)
    lift_bound = evaluate_lift_bound_external_effect_gate_v1(repo_root=repo_root)
    permit_bound = evaluate_permit_mint_bound_external_effect_permit_seam_v1(repo_root=repo_root)

    invoke_error = probe_import_time_invoke_sink_v1()
    envelope_error = probe_envelope_bound_send_seam_without_permit_v1()

    layers: list[SeamLayerProbeV1] = [
        SeamLayerProbeV1(
            layer_id="pre_external_boundary",
            epistemic_class="RUNTIME_EVIDENCE",
            runtime_status="RUNTIME_PROVEN" if pre_external.ok else "AUTHORITY_BLOCKED",
            admission_granted=pre_external.ok is True,
            performed=None,
            reason_codes=tuple(pre_external.guard_failures or ()),
            canonical_next_blocker=None,
        ),
        SeamLayerProbeV1(
            layer_id="external_effect_authorization_policy",
            epistemic_class="CANONICAL_AUTHORITY",
            runtime_status=(
                "RUNTIME_PROVEN"
                if policy_admission.policy_admission_granted
                else "AUTHORITY_BLOCKED"
            ),
            admission_granted=policy_admission.policy_admission_granted,
            performed=None,
            reason_codes=tuple(policy_admission.reason_codes),
            canonical_next_blocker=load_canonical_decision_v1(
                repo_root, CANONICAL_DECISION_CHAIN[0][1]
            ).get("next_genuine_blocker"),
        ),
        SeamLayerProbeV1(
            layer_id="standing_external_effect_lift",
            epistemic_class="CANONICAL_AUTHORITY",
            runtime_status=(
                "RUNTIME_PROVEN"
                if standing_lift.standing_external_effect_lift_granted
                else "AUTHORITY_BLOCKED"
            ),
            admission_granted=standing_lift.standing_external_effect_lift_granted,
            performed=None,
            reason_codes=tuple(standing_lift.reason_codes),
            canonical_next_blocker=load_canonical_decision_v1(
                repo_root, CANONICAL_DECISION_CHAIN[1][1]
            ).get("next_genuine_blocker"),
        ),
        SeamLayerProbeV1(
            layer_id="external_effect_permit_mint_admission",
            epistemic_class="CANONICAL_AUTHORITY",
            runtime_status=(
                "RUNTIME_PROVEN"
                if permit_bound.permit_mint_admission_granted
                else "AUTHORITY_BLOCKED"
            ),
            admission_granted=permit_bound.permit_mint_admission_granted,
            performed=permit_bound.permit_mint_performed,
            reason_codes=tuple(permit_bound.reason_codes),
            canonical_next_blocker=load_canonical_decision_v1(
                repo_root, CANONICAL_DECISION_CHAIN[2][1]
            ).get("next_genuine_blocker"),
        ),
        SeamLayerProbeV1(
            layer_id="import_time_invoke_sink",
            epistemic_class="RUNTIME_EVIDENCE",
            runtime_status="AUTHORITY_BLOCKED",
            admission_granted=False,
            performed=False,
            reason_codes=(invoke_error or "UNKNOWN",),
            canonical_next_blocker=None,
        ),
        SeamLayerProbeV1(
            layer_id="envelope_bound_send_seam",
            epistemic_class="RUNTIME_EVIDENCE",
            runtime_status="AUTHORITY_BLOCKED",
            admission_granted=False,
            performed=False,
            reason_codes=(envelope_error or "UNKNOWN",),
            canonical_next_blocker=None,
        ),
    ]

    policy_chain_admissions = (
        policy_admission.policy_admission_granted is True
        and standing_lift.standing_external_effect_lift_granted is True
        and permit_bound.permit_mint_admission_granted is True
        and pre_external.ok is True
    )

    return {
        "INTENT_TO_EXECUTION_EDGE": "order_intent → execution_external_effect",
        "PRE_EXTERNAL_BOUNDARY_OK": pre_external.ok is True,
        "POLICY_BOUND_GATE": {
            "policy_admission_granted": policy_bound.policy_admission_granted,
            "import_standing_authorized": policy_bound.gate_decision.external_effect_authorized,
        },
        "LIFT_BOUND_GATE": {
            "lift_admission_granted": lift_bound.lift_admission_granted,
            "import_standing_authorized": (
                lift_bound.gate_decision_at_import_standing.external_effect_authorized
            ),
            "lift_standing_authorized": (
                lift_bound.gate_decision_at_lift_standing.external_effect_authorized
            ),
        },
        "PERMIT_MINT_BOUND_SEAM": {
            "permit_mint_admission_granted": permit_bound.permit_mint_admission_granted,
            "permit_mint_performed": permit_bound.permit_mint_performed,
            "governed_permit_mint_authorized": permit_bound.governed_permit_mint_authorized,
        },
        "STANDING_IMPORT_CONSTANTS": {
            "EXTERNAL_EFFECT_AUTHORIZED": EXTERNAL_EFFECT_AUTHORIZED is True,
            "POST_ALLOWED": POST_ALLOWED is True,
            "REAL_VENUE_POST_ALLOWED": REAL_VENUE_POST_ALLOWED is True,
        },
        "INVOKE_SINK_PROBE": invoke_error,
        "ENVELOPE_SEAM_PROBE": envelope_error,
        "SEAM_LAYERS": [layer.to_dict() for layer in layers],
        "POLICY_CHAIN_ADMISSIONS_RUNTIME_PROVEN": policy_chain_admissions,
    }


def resolve_first_real_blocker_v1(
    *,
    treasury_report: Mapping[str, Any],
    seam_probe: Mapping[str, Any],
) -> tuple[str, str, str]:
    pre_external = bool(treasury_report.get("PRE_EXTERNAL_REACHED")) or bool(
        seam_probe.get("PRE_EXTERNAL_BOUNDARY_OK")
    )
    if not pre_external:
        return (
            str(treasury_report.get("FIRST_REAL_BLOCKER") or "PRODUCTIVE_GRAPH_INCOMPLETE"),
            "PRODUCTIVE_GRAPH",
            "PRE_EXTERNAL_NOT_REACHED",
        )
    if seam_probe.get("POLICY_CHAIN_ADMISSIONS_RUNTIME_PROVEN") is True:
        return (
            "EXTERNAL_EFFECT_AUTHORIZATION",
            "OPERATIONAL_EXTERNAL_EFFECT_SINK_FAIL_CLOSED",
            "ENVELOPE_BOUND_ACTUAL_POST_REQUIRES_SCOPED_OWNER_GO",
        )
    return (
        "EXTERNAL_EFFECT_AUTHORIZATION",
        "EXTERNAL_EFFECT_AUTHORITY",
        "POLICY_CHAIN_ADMISSION_INCOMPLETE",
    )


def build_seam_adjudication_report_v1(
    *,
    repo_root: Path,
    baseline_sha: str,
    treasury_report: Mapping[str, Any],
    map_sha256: str,
    atlas_sha256: str,
    e2e_run_id: str,
    evidence_root: str,
) -> dict[str, Any]:
    seam = probe_intent_to_execution_seam_v1(repo_root=repo_root)
    first_blocker, blocker_class, blocker_subtype = resolve_first_real_blocker_v1(
        treasury_report=treasury_report,
        seam_probe=seam,
    )
    pre_external = bool(treasury_report.get("PRE_EXTERNAL_REACHED")) or bool(
        seam.get("PRE_EXTERNAL_BOUNDARY_OK")
    )
    decision_chain = summarize_canonical_decision_chain_v1(repo_root=repo_root)
    fixpoint = (
        pre_external
        and seam.get("POLICY_CHAIN_ADMISSIONS_RUNTIME_PROVEN") is True
        and seam.get("INVOKE_SINK_PROBE") == "FullCoreExternalEffectNotAuthorizedError"
        and seam.get("ENVELOPE_SEAM_PROBE")
        in {"NO_PERMIT", "TRANSPORT_MISSING", "DURABLE_STORE_REQUIRED"}
    )
    return {
        "WP": WORKPACKAGE_ID,
        "BASELINE_SHA": baseline_sha,
        "MAP_SHA256": map_sha256,
        "ATLAS_SHA256": atlas_sha256,
        "E2E_RUN_ID": e2e_run_id,
        "EVIDENCE_ROOT": evidence_root,
        "PAPER_STATUS": "PARKED",
        "PRE_EXTERNAL_REACHED": pre_external,
        "EXACT_NEXT_EDGE": "intent_to_execution",
        "CANONICAL_DECISION_CHAIN_SUMMARY": decision_chain,
        "INTENT_TO_EXECUTION_SEAM_PROBE": seam,
        "FIRST_REAL_BLOCKER": first_blocker,
        "BLOCKER_CLASS": blocker_class,
        "BLOCKER_SUBTYPE": blocker_subtype,
        "ADJUDICATED_CONCLUSIONS": {
            "policy_admissions_closed_at_runtime": seam.get(
                "POLICY_CHAIN_ADMISSIONS_RUNTIME_PROVEN"
            ),
            "import_time_standing_remains_false_by_design": not (
                seam.get("STANDING_IMPORT_CONSTANTS") or {}
            ).get("EXTERNAL_EFFECT_AUTHORIZED"),
            "invoke_sink_fail_closed_without_owner_operating_go": True,
            "map_atlas_are_navigation_only": True,
        },
        "NAVIGATION_ONLY_FINDINGS": [
            "CSIA edge intent_to_execution is index; authority from gate modules and decision records.",
        ],
        "OPEN_CONFLICTS": [],
        "FIXPOINT_REACHED": fixpoint,
        "NEXT_WP_ANCHOR": (
            "EXTERNAL_EFFECT_AUTHORIZATION → scoped Owner-GO for permit-backed venue POST (not performed in WP)"
            if fixpoint
            else "CLOSE_PRE_EXTERNAL_OR_POLICY_CHAIN_GAP"
        ),
        "EXTERNAL_EFFECT_AUTHORIZED": False,
        "EXTERNAL_EFFECT_PERMIT_MINTED": False,
        "POST_ALLOWED": False,
        "REAL_EXTERNAL_EFFECT_COUNT": 0,
        "VENUE_POST_COUNT": 0,
        "TREASURY_E2E_REFERENCE": {
            "WHOLE_SYSTEM_E2E_RUN_ID": treasury_report.get("WHOLE_SYSTEM_E2E_RUN_ID"),
            "EVIDENCE_ROOT": treasury_report.get("EVIDENCE_ROOT"),
        },
    }
