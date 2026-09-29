"""Remaining-29 UCS evidence exhaustion audit (navigation only). AUTHORITY=NONE."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.ops.law_map_v1.surface_census_v1 import file_sha256, law_ref, sobj

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_PATH = REPO_ROOT / "config/governance/current_law_impact_map_v1/source_v1.json"
UCS_WORKSET = REPO_ROOT / "config/governance/current_law_impact_map_v1/ucs_frozen_workset_v1.json"
R29_JSON = (
    REPO_ROOT / "config/governance/current_law_impact_map_v1/remaining_29_frozen_workset_v1.json"
)
RUNBOOK = "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"
EQUITY_RAT = "config/governance/risk_sizing_account_equity_authority_owner_full_core_track_ratification_v1.json"

POST_MERGE_BASELINE_SHA = "e2a3dbdb202edb32f01a30da488538b40976b26a"
CENSUS_ID = "REMAINING_29_EVIDENCE_EXHAUSTION_V1"

SOBJ_NAV_EXTERNAL = "sobj_nav_external_effect_seam"
SOBJ_NAV_B05 = "sobj_nav_b05_account_equity_productive_chain"
SOBJ_NAV_COMPOSITION = "sobj_nav_full_core_composition_joins"

OWNER_DECISION_ACCOUNT_EQUITY = "OD_ACCOUNT_EQUITY_SIZING_SOURCE"
OWNER_DECISION_SEALED_29P = "OD_SEALED_VENUE_29P_NORMATIVE"
OWNER_DECISION_EXTERNAL_EFFECT = "OD_EXTERNAL_EFFECT_AND_CREDENTIAL_AUTHORITY"
OWNER_DECISION_CAP24_MARK = "OD_CAP24_PRODUCTIVE_MARK_PROVENANCE"
OWNER_DECISION_VENUE_PLAN_IDENTITY = "OD_VENUE_PLAN_CAP24_MV2_IDENTITY"
OWNER_DECISION_COMPLIANCE_ADJUDICATOR = "OD_CANONICAL_COMPLIANCE_AND_REPROOF_ADJUDICATOR"


@dataclass(frozen=True)
class ExhaustionRow:
    workset_id: str
    surface: str
    ucs6958_disposition: str
    root_cause_group: str
    unknown_pins: tuple[str, ...]
    exhaustion_disposition: str
    domain_law_adjudication: str
    primary_evidence_refs: tuple[str, ...]
    missing_canonical_fact: str | None
    owner_decision_boundary: str | None
    bind_lref: str | None
    bind_sobj: str | None


def _frozen_remaining_paths() -> list[str]:
    """Paths frozen at #6958 merge (UCS dispositions still UNCLASSIFIED-class)."""
    ucs = _ucs_meta()
    paths = sorted(
        surface
        for surface, meta in ucs.items()
        if str(meta.get("disposition", "")).startswith("UNCLASSIFIED")
    )
    if len(paths) != 29:
        raise RuntimeError(f"FROZEN_REMAINING_WORKSET_COUNT expected 29, got {len(paths)}")
    return paths


def assert_source_matches_frozen_workset() -> None:
    doc = json.loads(SOURCE_PATH.read_text(encoding="utf-8"))
    live = sorted(r["path"] for r in doc.get("unclassified_current_surfaces", []))
    frozen = _frozen_remaining_paths()
    if live != frozen:
        raise RuntimeError(
            "source unclassified_current_surfaces drift vs frozen remaining-29 workset"
        )


def _ucs_meta() -> dict[str, dict[str, Any]]:
    data = json.loads(UCS_WORKSET.read_text(encoding="utf-8"))
    return {row["surface"]: row for row in data["dispositions"]}


def _build_rows() -> list[ExhaustionRow]:
    ucs = _ucs_meta()
    rows: list[ExhaustionRow] = []

    def row(
        ucs_id: str,
        path: str,
        exhaustion: str,
        domain: str,
        evidence: tuple[str, ...],
        missing: str | None,
        owner_boundary: str | None,
        bind_lref: str | None = None,
        bind_sobj: str | None = None,
        pins: tuple[str, ...] = (),
    ) -> ExhaustionRow:
        meta = ucs[path]
        return ExhaustionRow(
            workset_id=ucs_id,
            surface=path,
            ucs6958_disposition=meta["disposition"],
            root_cause_group=meta.get("root_cause_group") or "",
            unknown_pins=pins or tuple(),
            exhaustion_disposition=exhaustion,
            domain_law_adjudication=domain,
            primary_evidence_refs=evidence,
            missing_canonical_fact=missing,
            owner_decision_boundary=owner_boundary,
            bind_lref=bind_lref,
            bind_sobj=bind_sobj,
        )

    p = "src/ops"
    rows.extend(
        [
            row(
                "UCS-0002",
                f"{p}/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_immediate_pre_mutation_freshness_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (
                    f"{p}/full_core_live_path_composition_root_v1/current_productive_actual_venue_post_immediate_pre_mutation_freshness_v1.py",
                ),
                "No Master Runbook DEFINITION_SCHEMA_PATH or CURRENT spec naming this freshness seam.",
                OWNER_DECISION_EXTERNAL_EFFECT,
                pins=("unk_sealed_venue_number_29p",),
            ),
            row(
                "UCS-0019",
                f"{p}/full_core_live_path_composition_root_v1/current_productive_occupancy_classify_and_c1_gate_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (
                    f"{p}/full_core_live_path_composition_root_v1/current_productive_occupancy_classify_and_c1_gate_v1.py",
                    RUNBOOK,
                ),
                "Relocated classify/gate tokens without durable CURRENT spec owner in CSIA domains.",
                OWNER_DECISION_EXTERNAL_EFFECT,
            ),
            row(
                "UCS-0027",
                f"{p}/full_core_live_path_composition_root_v1/current_productive_venue_plan_td_mode_and_order_environment_authority_v1.py",
                "EXISTING_CURRENT_EVIDENCE_BINDABLE",
                "UNKNOWN_CURRENT",
                (
                    RUNBOOK,
                    f"{p}/full_core_live_path_composition_root_v1/current_productive_venue_plan_td_mode_and_order_environment_authority_v1.py",
                ),
                None,
                None,
                bind_lref="RUNBOOK-VENUE-PLAN-TDMODE-AUTHORITY-V1",
                bind_sobj=SOBJ_NAV_COMPOSITION,
            ),
            row(
                "UCS-0028",
                f"{p}/full_core_live_path_composition_root_v1/current_productive_venue_plan_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (
                    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_ENTER_LIVE_29P_JOIN_BEFORE_EXECUTABLE_EXTERNAL_EFFECT_V1.md",
                    f"{p}/full_core_live_path_composition_root_v1/current_productive_venue_plan_v1.py",
                ),
                "Cap24/MV2 replay vs venue-plan bind owner not identity-proven; no CSIA code_ref.",
                OWNER_DECISION_VENUE_PLAN_IDENTITY,
            ),
            row(
                "UCS-0031",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_29p_common_epoch_handoff_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (
                    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_29P_CAP24_BOUND_INSTRUMENT_PROVENANCE_HANDOFF_V1.md",
                    "tests/ops/test_full_core_current_productive_29p_common_epoch_handoff_v1.py",
                ),
                "Sealed venue 29P normative epoch semantics OPEN.",
                OWNER_DECISION_SEALED_29P,
                pins=("unk_sealed_venue_number_29p",),
            ),
            row(
                "UCS-0032",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_sizing_value_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (
                    EQUITY_RAT,
                    "tests/ops/test_full_core_current_productive_29p_fresh_trusted_usdc_free_margin_get_and_produce_sizing_value_v1.py",
                ),
                "Trusted GET sizing value vs account-equity mapping CSIA PARTIAL (account_equity_mapping_unbound).",
                OWNER_DECISION_ACCOUNT_EQUITY,
                pins=("unk_account_equity_sizing_source",),
            ),
            row(
                "UCS-0033",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_29p_live_account_bound_and_instrument_scope_v1.py",
                "EXISTING_CURRENT_EVIDENCE_BINDABLE",
                "UNKNOWN_CURRENT",
                (
                    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_V1.md",
                    RUNBOOK,
                ),
                None,
                None,
                bind_lref="SPEC-29P-LIVE-ACCOUNT-BOUND-V1",
                bind_sobj=SOBJ_NAV_B05,
                pins=("unk_sealed_venue_number_29p",),
            ),
            row(
                "UCS-0034",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_29p_risk_capital_model_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (
                    "tests/ops/test_full_core_current_productive_29p_risk_capital_model_v1.py",
                    RUNBOOK,
                ),
                "Risk capital vs treasury/B05 equity identity not proven.",
                OWNER_DECISION_SEALED_29P,
            ),
            row(
                "UCS-0035",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_account_equity_source_architecture_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (EQUITY_RAT, RUNBOOK),
                "Architecture module; CSIA account_equity_mapping_unbound remains OPEN.",
                OWNER_DECISION_ACCOUNT_EQUITY,
                pins=("unk_account_equity_sizing_source",),
            ),
            row(
                "UCS-0037",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_available_for_sizing_base_binding_models_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (EQUITY_RAT,),
                "Sizing source selection not adjudicated.",
                OWNER_DECISION_ACCOUNT_EQUITY,
                pins=("unk_account_equity_sizing_source",),
            ),
            row(
                "UCS-0038",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_available_for_sizing_base_binding_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (EQUITY_RAT,),
                None,
                OWNER_DECISION_ACCOUNT_EQUITY,
                pins=("unk_account_equity_sizing_source",),
            ),
            row(
                "UCS-0039",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_available_for_sizing_producer_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (EQUITY_RAT,),
                None,
                OWNER_DECISION_ACCOUNT_EQUITY,
                pins=("unk_account_equity_sizing_source",),
            ),
            row(
                "UCS-0040",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_available_for_sizing_source_selection_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (EQUITY_RAT,),
                "Direct selector for account-equity sizing source.",
                OWNER_DECISION_ACCOUNT_EQUITY,
                pins=("unk_account_equity_sizing_source",),
            ),
            row(
                "UCS-0042",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_cap24_reserved_productivity_root_guard_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (
                    f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_cap24_reserved_productivity_root_guard_v1.py",
                ),
                "No CURRENT spec/runbook DEFINITION_SCHEMA for guard semantics.",
                OWNER_DECISION_CAP24_MARK,
                pins=("unk_cap24_l1_productive_mark_provenance",),
            ),
            row(
                "UCS-0045",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_common_epoch_to_enter_live_29p_handoff_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (
                    f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_common_epoch_to_enter_live_29p_handoff_v1.py",
                ),
                "29P handoff epoch; sealed venue pin OPEN.",
                OWNER_DECISION_SEALED_29P,
                pins=("unk_sealed_venue_number_29p",),
            ),
            row(
                "UCS-0049",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_execute_network_credential_join_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (
                    f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_execute_network_credential_join_v1.py",
                    RUNBOOK,
                ),
                "Execute-network credential join; checkout_independent runbook defs name different surfaces.",
                OWNER_DECISION_EXTERNAL_EFFECT,
            ),
            row(
                "UCS-0050",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_execute_network_read_credential_loader_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (
                    f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_execute_network_read_credential_loader_v1.py",
                ),
                "Credential loader authority not indexed in CURRENT runbook definition schema.",
                OWNER_DECISION_EXTERNAL_EFFECT,
            ),
            row(
                "UCS-0051",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_execution_admission_remainder_v1.py",
                "EXISTING_CURRENT_EVIDENCE_BINDABLE",
                "UNKNOWN_CURRENT",
                (
                    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_EXECUTION_ADMISSION_REMAINDER_V1.md",
                    RUNBOOK,
                ),
                None,
                None,
                bind_lref="SPEC-EXECUTION-ADMISSION-REMAINDER-V1",
                bind_sobj=SOBJ_NAV_EXTERNAL,
            ),
            row(
                "UCS-0062",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_live_armed_standing_gate_v1.py",
                "EXISTING_CURRENT_EVIDENCE_BINDABLE",
                "UNKNOWN_CURRENT",
                (
                    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE_V1.md",
                    RUNBOOK,
                ),
                None,
                None,
                bind_lref="SPEC-LIVE-ARMED-STANDING-GATE-V1",
                bind_sobj=SOBJ_NAV_EXTERNAL,
            ),
            row(
                "UCS-0064",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_live_enabled_standing_gate_v1.py",
                "EXISTING_CURRENT_EVIDENCE_BINDABLE",
                "UNKNOWN_CURRENT",
                (
                    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ENABLED_STANDING_GATE_V1.md",
                    RUNBOOK,
                ),
                None,
                None,
                bind_lref="SPEC-LIVE-ENABLED-STANDING-GATE-V1",
                bind_sobj=SOBJ_NAV_EXTERNAL,
            ),
            row(
                "UCS-0065",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_live_execution_port_construction_v1.py",
                "EXISTING_CURRENT_EVIDENCE_BINDABLE",
                "UNKNOWN_CURRENT",
                (
                    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_LIVE_EXECUTION_PORT_CONSTRUCTION_V1.md",
                    RUNBOOK,
                ),
                None,
                None,
                bind_lref="SPEC-LIVE-EXECUTION-PORT-V1",
                bind_sobj=SOBJ_NAV_EXTERNAL,
            ),
            row(
                "UCS-0067",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_p01_policy_replacement_and_29p_continuation_v1.py",
                "EXISTING_CURRENT_EVIDENCE_BINDABLE",
                "UNKNOWN_CURRENT",
                (
                    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_V1.md",
                    RUNBOOK,
                ),
                None,
                None,
                bind_lref="SPEC-P01-POLICY-REPLACEMENT-V1",
                bind_sobj=SOBJ_NAV_B05,
                pins=("unk_sealed_venue_number_29p",),
            ),
            row(
                "UCS-0068",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_p01_policy_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                ("docs/system_atlas/entities/catalog.yaml",),
                "No runbook DEFINITION_SCHEMA for p01_policy_v1; atlas navigation only.",
                OWNER_DECISION_SEALED_29P,
            ),
            row(
                "UCS-0070",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_submission_authorized_v1.py",
                "EXISTING_CURRENT_EVIDENCE_BINDABLE",
                "UNKNOWN_CURRENT",
                (
                    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED_V1.md",
                    RUNBOOK,
                ),
                None,
                None,
                bind_lref="SPEC-SUBMISSION-AUTHORIZED-V1",
                bind_sobj=SOBJ_NAV_EXTERNAL,
            ),
            row(
                "UCS-0071",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_u01_account_mode_adapter_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (
                    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION_V1.md",
                ),
                "Runbook/spec name ratification module as authority; adapter not primary DEFINITION_SCHEMA.",
                OWNER_DECISION_ACCOUNT_EQUITY,
            ),
            row(
                "UCS-0072",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_u01_account_mode_semantic_ratification_v1.py",
                "EXISTING_CURRENT_EVIDENCE_BINDABLE",
                "UNKNOWN_CURRENT",
                (
                    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION_V1.md",
                    RUNBOOK,
                ),
                None,
                None,
                bind_lref="SPEC-U01-ACCOUNT-MODE-RATIFICATION-V1",
                bind_sobj=SOBJ_NAV_B05,
            ),
            row(
                "UCS-0073",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_models_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (EQUITY_RAT,),
                "U04/P01 sizing eligibility vs unbound account-equity mapping.",
                OWNER_DECISION_ACCOUNT_EQUITY,
                pins=("unk_account_equity_sizing_source",),
            ),
            row(
                "UCS-0074",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_u04_p01_eligibility_inputs_for_ct_sizing_produce_binding_v1.py",
                "GENUINELY_CANONICAL_OWNER_BLOCKED",
                "UNKNOWN_CURRENT",
                (EQUITY_RAT,),
                None,
                OWNER_DECISION_ACCOUNT_EQUITY,
                pins=("unk_account_equity_sizing_source",),
            ),
            row(
                "UCS-0076",
                f"{p}/governed_productive_account_equity_authority_producer_v1/current_productive_wire_send_permitted_standing_gate_v1.py",
                "EXISTING_CURRENT_EVIDENCE_BINDABLE",
                "UNKNOWN_CURRENT",
                (
                    "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_WIRE_SEND_PERMITTED_STANDING_GATE_V1.md",
                    RUNBOOK,
                ),
                None,
                None,
                bind_lref="SPEC-WIRE-SEND-STANDING-GATE-V1",
                bind_sobj=SOBJ_NAV_EXTERNAL,
            ),
        ]
    )
    paths = _frozen_remaining_paths()
    if {r.surface for r in rows} != set(paths):
        raise RuntimeError("exhaustion rows must cover exactly remaining 29 paths")
    return sorted(rows, key=lambda r: r.workset_id)


def frozen_workset_sha256(rows: list[ExhaustionRow]) -> str:
    payload = json.dumps(
        [
            {
                "workset_id": r.workset_id,
                "surface": r.surface,
                "exhaustion_disposition": r.exhaustion_disposition,
            }
            for r in rows
        ],
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_artifact() -> dict[str, Any]:
    rows = _build_rows()
    return {
        "authority": "NONE",
        "ssot": False,
        "navigation_evidence_only": True,
        "post_merge_baseline_sha": POST_MERGE_BASELINE_SHA,
        "frozen_remaining_workset_count": len(rows),
        "frozen_remaining_workset_sha256": frozen_workset_sha256(rows),
        "census_id": CENSUS_ID,
        "records": [
            {
                "workset_id": r.workset_id,
                "surface": r.surface,
                "ucs6958_disposition": r.ucs6958_disposition,
                "root_cause_group": r.root_cause_group,
                "unknown_pins": list(r.unknown_pins),
                "exhaustion_disposition": r.exhaustion_disposition,
                "domain_law_adjudication": r.domain_law_adjudication,
                "primary_evidence_refs": list(r.primary_evidence_refs),
                "missing_canonical_fact": r.missing_canonical_fact,
                "owner_decision_boundary": r.owner_decision_boundary,
                "bind_lref": r.bind_lref,
                "bind_sobj": r.bind_sobj,
            }
            for r in rows
        ],
    }


def _additive_lrefs() -> list[dict[str, Any]]:
    specs = [
        (
            "RUNBOOK-VENUE-PLAN-TDMODE-AUTHORITY-V1",
            RUNBOOK,
            "CURRENT Venue-Plan tdMode and Order-Environment Authority",
            SOBJ_NAV_COMPOSITION,
        ),
        (
            "SPEC-29P-LIVE-ACCOUNT-BOUND-V1",
            "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_V1.md",
            "FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ACCOUNT_BOUND_AND_INSTRUMENT_SCOPE_FOR_29P_V1",
            SOBJ_NAV_B05,
        ),
        (
            "SPEC-EXECUTION-ADMISSION-REMAINDER-V1",
            "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_EXECUTION_ADMISSION_REMAINDER_V1.md",
            "FULL_CORE_CURRENT_PRODUCTIVE_EXECUTION_ADMISSION_REMAINDER_V1",
            SOBJ_NAV_EXTERNAL,
        ),
        (
            "SPEC-LIVE-ARMED-STANDING-GATE-V1",
            "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE_V1.md",
            "FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ARMED_STANDING_GATE_V1",
            SOBJ_NAV_EXTERNAL,
        ),
        (
            "SPEC-LIVE-ENABLED-STANDING-GATE-V1",
            "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ENABLED_STANDING_GATE_V1.md",
            "FULL_CORE_CURRENT_PRODUCTIVE_LIVE_ENABLED_STANDING_GATE_V1",
            SOBJ_NAV_EXTERNAL,
        ),
        (
            "SPEC-LIVE-EXECUTION-PORT-V1",
            "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_LIVE_EXECUTION_PORT_CONSTRUCTION_V1.md",
            "FULL_CORE_CURRENT_PRODUCTIVE_LIVE_EXECUTION_PORT_CONSTRUCTION_V1",
            SOBJ_NAV_EXTERNAL,
        ),
        (
            "SPEC-P01-POLICY-REPLACEMENT-V1",
            "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_V1.md",
            "FULL_CORE_CURRENT_PRODUCTIVE_P01_POLICY_REPLACEMENT_V1",
            SOBJ_NAV_B05,
        ),
        (
            "SPEC-SUBMISSION-AUTHORIZED-V1",
            "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED_V1.md",
            "FULL_CORE_CURRENT_PRODUCTIVE_SUBMISSION_AUTHORIZED_V1",
            SOBJ_NAV_EXTERNAL,
        ),
        (
            "SPEC-U01-ACCOUNT-MODE-RATIFICATION-V1",
            "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION_V1.md",
            "FULL_CORE_CURRENT_PRODUCTIVE_U01_ACCOUNT_MODE_SEMANTIC_RATIFICATION_V1",
            SOBJ_NAV_B05,
        ),
        (
            "SPEC-WIRE-SEND-STANDING-GATE-V1",
            "docs/ops/specs/FULL_CORE_CURRENT_PRODUCTIVE_WIRE_SEND_PERMITTED_STANDING_GATE_V1.md",
            "FULL_CORE_CURRENT_PRODUCTIVE_WIRE_SEND_PERMITTED_STANDING_GATE_V1",
            SOBJ_NAV_EXTERNAL,
        ),
    ]
    out = []
    for law_id, src, anchor, sobj_id in specs:
        out.append(
            law_ref(
                law_id,
                src,
                anchor,
                "CANONICAL_SPEC" if src.endswith(".md") and "runbooks" not in src else "RUNBOOK",
                [sobj_id],
                [src, RUNBOOK],
                display_label=law_id,
            )
        )
    return out


def _merge_by_id(existing: list[dict], new: list[dict], key: str) -> list[dict]:
    seen = {row[key]: row for row in existing}
    for row in new:
        seen[row[key]] = row
    return [seen[k] for k in sorted(seen)]


def _merge_code_surface(sobjs: list[dict[str, Any]], sid: str, path: str) -> None:
    for so in sobjs:
        if so["id"] != sid:
            continue
        surfaces = list(so.get("code_surfaces", []))
        if path not in surfaces:
            surfaces.append(path)
            so["code_surfaces"] = sorted(surfaces)
            return
    raise KeyError(sid)


def apply_bindings(doc: dict[str, Any]) -> dict[str, Any]:
    rows = _build_rows()
    doc["law_references"] = _merge_by_id(doc["law_references"], _additive_lrefs(), "law_id")
    sobjs = doc["semantic_objects"]
    remaining: list[dict[str, Any]] = []
    for r in rows:
        if r.exhaustion_disposition == "EXISTING_CURRENT_EVIDENCE_BINDABLE":
            assert r.bind_sobj and r.bind_lref
            _merge_code_surface(sobjs, r.bind_sobj, r.surface)
        else:
            remaining.append(
                {
                    "path": r.surface,
                    "classification": "UNCLASSIFIED_CURRENT",
                    "reason": (
                        f"{r.workset_id} EXHAUSTION={r.exhaustion_disposition}: "
                        f"{r.missing_canonical_fact or 'see remaining_29_frozen_workset_v1.json'}"
                    ),
                }
            )
    doc["semantic_objects"] = sobjs
    doc["unclassified_current_surfaces"] = sorted(remaining, key=lambda x: x["path"])

    new_div = {
        "id": "SEM-SURF-DIV-00003",
        "adjudication": "UNKNOWN_CURRENT",
        "producer_ref": "csia:account_equity_mapping_unbound",
        "consumer_ref": "sobj_nav_b05_account_equity_productive_chain",
        "statement": (
            "CSIA open_epistemic record account_equity_mapping_unbound (PARTIAL) vs "
            "B05 ratification JSON chain-closure claims — sizing source selection remains "
            "not Law-Map adjudicated; maps to unk_account_equity_sizing_source."
        ),
        "expected_canonical_source": EQUITY_RAT,
        "evidence_refs": [
            "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            EQUITY_RAT,
            "config/governance/risk_sizing_authority_decision_contract_freeze_v1.json",
        ],
        "reproof_required": True,
        "unknown_relation_id": "unk_account_equity_sizing_source",
    }
    divs = doc.get("semantic_divergence_index", [])
    if not any(d["id"] == new_div["id"] for d in divs):
        divs.append(new_div)
    doc["semantic_divergence_index"] = divs
    doc["baseline_sha"] = POST_MERGE_BASELINE_SHA
    return doc


def render_markdown(artifact: dict[str, Any]) -> str:
    lines = [
        "<!-- GENERATED FILE. DO NOT EDIT BY HAND. AUTHORITY=NONE SSOT=false NAVIGATION/EVIDENCE ONLY -->",
        "# Remaining-29 Evidence Exhaustion",
        "",
        f"post_merge_baseline_sha={artifact['post_merge_baseline_sha']}",
        f"frozen_remaining_workset_sha256={artifact['frozen_remaining_workset_sha256']}",
        "",
    ]
    for rec in artifact["records"]:
        lines.append(
            f"- {rec['workset_id']} exhaustion={rec['exhaustion_disposition']} "
            f"domain={rec['domain_law_adjudication']} surface={rec['surface']}"
        )
    lines.append("")
    return "\n".join(lines)


def write_artifact() -> dict[str, Any]:
    artifact = build_artifact()
    R29_JSON.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    md = (
        REPO_ROOT
        / "docs/governance/current_law_impact_map_v1/generated/remaining_29_evidence_exhaustion_v1.md"
    )
    md.write_text(render_markdown(artifact), encoding="utf-8")
    return artifact
