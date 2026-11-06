"""Evidence-backed CURRENT semantic surface census helpers. AUTHORITY=NONE."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]

# Closed by OD-ACCOUNT-EQUITY-SIZING-SOURCE-ADJUDICATION-V1 / SEM-SURF-DIV-00003 (navigation guard).
_SUPPRESSED_UNKNOWN_RELATION_IDS = frozenset({"unk_account_equity_sizing_source"})


def file_sha256(rel: str) -> str:
    path = REPO_ROOT / rel
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return digest


def law_ref(
    law_id: str,
    canonical_source: str,
    canonical_anchor: str,
    source_authority_class: str,
    semantic_object_ids: list[str],
    evidence_refs: list[str],
    display_label: str | None = None,
) -> dict[str, Any]:
    return {
        "law_id": law_id,
        "canonical_source": canonical_source,
        "canonical_anchor": canonical_anchor,
        "source_sha256": file_sha256(canonical_source),
        "source_authority_class": source_authority_class,
        "index_status": "INDEXED",
        "law_reference_authority": "NONE",
        "display_label": display_label or law_id,
        "semantic_object_ids": semantic_object_ids,
        "evidence_refs": evidence_refs,
    }


def sobj(
    sid: str,
    semantic_class: str,
    current_status: str,
    code_surfaces: list[str],
    law_ref_ids: list[str],
    evidence_refs: list[str],
    *,
    config_surfaces: list[str] | None = None,
    csia_record_id: str | None = None,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "id": sid,
        "semantic_class": semantic_class,
        "current_status": current_status,
        "code_surfaces": code_surfaces,
        "config_surfaces": config_surfaces or [],
        "law_ref_ids": law_ref_ids,
        "evidence_refs": evidence_refs,
    }
    if csia_record_id:
        row["csia_record_id"] = csia_record_id
    return row


def edge(
    eid: str,
    edge_class: str,
    from_id: str,
    to_id: str,
    evidence_refs: list[str],
    *,
    propagate_impact: bool = True,
) -> dict[str, Any]:
    return {
        "id": eid,
        "edge_class": edge_class,
        "from_id": from_id,
        "to_id": to_id,
        "propagate_impact": propagate_impact,
        "evidence_refs": evidence_refs,
    }


def expansion_payload() -> dict[str, Any]:
    """Return records to merge into source_v1 (additive)."""
    ssf_spec = "docs/ops/specs/RANKING_UNIVERSE_TO_FULL_CORE_SSF_HANDOFF_CONTRACT_V1.md"
    cap22_spec = "docs/ops/specs/MASTER_V2_CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1.md"
    cap21_code = "src/ops/governed_futures_universe_producer_v1/constants_v1.py"
    cap23_code = "src/ops/single_selected_future_policy_v1/constants_v1.py"
    cap24_code = "src/ops/single_selected_future_runtime_binding_v1/constants_v1.py"
    handoff_code = "src/ops/ranking_universe_to_full_core_ssf_handoff_contract_v1.py"
    g17_code = "src/ops/full_core_live_path_composition_root_v1/current_productive_g17_typed_vol_cmc_bind_v1.py"
    pubmd_policy = "config/governance/peak_trade_public_market_data_runtime_v1_policy_v1.json"
    portfolio_code = "src/ops/portfolio_capital_reservation_budget_v1/contract_v1.py"
    elem_code = "src/trading/market_state/elementary_direction_v1.py"
    orch_code = "src/ops/full_core_live_path_composition_root_v1/current_productive_governed_continuous_cycle_orchestrator_v1.py"
    m9_decision = "config/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1_decision_v1.json"

    new_lrefs = [
        law_ref(
            "CAP-SSF-HANDOFF-V1",
            ssf_spec,
            "RANKING_UNIVERSE_TO_FULL_CORE_SSF_HANDOFF_CONTRACT_V1",
            "CANONICAL_SPEC",
            ["sobj_ranking_ssf_handoff"],
            [
                ssf_spec,
                handoff_code,
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
            display_label="Ranking universe to Full-Core SSF handoff",
        ),
        law_ref(
            "CAP22-PRODUCTIVE-RANKING-V1",
            cap22_spec,
            "MASTER_V2_CAPABILITY_2_2_PRODUCTIVE_FUTURES_RANKING_PRODUCER_V1",
            "CANONICAL_SPEC",
            ["sobj_cap22_ranking"],
            [
                cap22_spec,
                "src/ops/productive_futures_ranking_producer_v1/constants_v1.py",
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
        ),
        law_ref(
            "CAP21-GOVERNED-UNIVERSE-V1",
            cap21_code,
            "GOVERNED_FUTURES_UNIVERSE_PRODUCER_V1",
            "EVIDENCE_CENSUS",
            ["sobj_cap21_universe"],
            [
                cap21_code,
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
        ),
        law_ref(
            "CAP23-SINGLE-SELECTED-FUTURE-V1",
            cap23_code,
            "SINGLE_SELECTED_FUTURE_POLICY_V1",
            "EVIDENCE_CENSUS",
            ["sobj_cap23_selection"],
            [
                cap23_code,
                "src/ops/single_selected_future_policy_v1/selection_v1.py",
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
        ),
        law_ref(
            "CAP24-RUNTIME-BINDING-V1",
            cap24_code,
            "SINGLE_SELECTED_FUTURE_RUNTIME_BINDING_V1",
            "EVIDENCE_CENSUS",
            ["sobj_cap24_runtime_binding"],
            [
                cap24_code,
                "src/ops/single_selected_future_runtime_binding_v1/binding_gate_v1.py",
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
        ),
        law_ref(
            "G17-TYPED-VOL-CMC-BIND-V1",
            g17_code,
            "apply_current_productive_g17_typed_vol_cmc_bind_v1",
            "EVIDENCE_CENSUS",
            ["sobj_g17_typed_vol_bind"],
            [
                g17_code,
                "src/trading/master_v2/canonical_volatility_productive_runtime_cmc_typed_binding_v1.py",
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
        ),
        law_ref(
            "PUBLIC-MD-RUNTIME-POLICY-V1",
            pubmd_policy,
            "peak_trade_public_market_data_runtime_v1_policy_v1",
            "CANONICAL_SPEC",
            ["sobj_public_md_runtime"],
            [
                pubmd_policy,
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
        ),
        law_ref(
            "M9-VOL-MAX-AGE-DECISION-V1",
            m9_decision,
            "m9_volatility_numeric_max_age_numeric_productive_target_v1_decision_v1",
            "CANONICAL_SPEC",
            ["sobj_m9_vol_max_age"],
            [
                m9_decision,
                "src/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1.py",
            ],
        ),
    ]

    new_sobjs = [
        sobj(
            "sobj_cap21_universe",
            "CURRENT_PRODUCTIVE_SEMANTIC",
            "UNKNOWN_CURRENT",
            [cap21_code],
            ["CAP21-GOVERNED-UNIVERSE-V1"],
            [
                cap21_code,
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
            csia_record_id="universe_cap21",
        ),
        sobj(
            "sobj_cap22_ranking",
            "CURRENT_PRODUCTIVE_SEMANTIC",
            "UNKNOWN_CURRENT",
            ["src/ops/productive_futures_ranking_producer_v1/producer_v1.py"],
            ["CAP22-PRODUCTIVE-RANKING-V1"],
            [
                cap22_spec,
                "src/ops/productive_futures_ranking_producer_v1/producer_v1.py",
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
            csia_record_id="ranking_cap22",
        ),
        sobj(
            "sobj_cap23_selection",
            "CURRENT_PRODUCTIVE_SEMANTIC",
            "UNKNOWN_CURRENT",
            ["src/ops/single_selected_future_policy_v1/selection_v1.py"],
            ["CAP23-SINGLE-SELECTED-FUTURE-V1"],
            [
                cap23_code,
                "src/ops/single_selected_future_policy_v1/selection_v1.py",
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
            csia_record_id="selection_cap23",
        ),
        sobj(
            "sobj_cap24_runtime_binding",
            "CURRENT_PRODUCTIVE_SEMANTIC",
            "UNKNOWN_CURRENT",
            ["src/ops/single_selected_future_runtime_binding_v1/binding_gate_v1.py"],
            ["CAP24-RUNTIME-BINDING-V1", "CAP-SSF-HANDOFF-V1"],
            [
                cap24_code,
                handoff_code,
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
            csia_record_id="runtime_binding_cap24",
        ),
        sobj(
            "sobj_ranking_ssf_handoff",
            "ENFORCEMENT_CONTRACT",
            "PROVEN_CURRENT",
            [handoff_code],
            ["CAP-SSF-HANDOFF-V1"],
            [
                ssf_spec,
                handoff_code,
                "tests/test_ranking_universe_to_full_core_ssf_handoff_contract_v1.py",
            ],
            csia_record_id="selection_cap23",
        ),
        sobj(
            "sobj_public_md_runtime",
            "CURRENT_PRODUCTIVE_SEMANTIC",
            "UNKNOWN_CURRENT",
            ["src/ops/peak_trade_public_market_data_runtime_v1/facts_v1.py"],
            ["PUBLIC-MD-RUNTIME-POLICY-V1"],
            [
                pubmd_policy,
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
            csia_record_id="peak_trade_public_market_data_runtime_wp_a",
        ),
        sobj(
            "sobj_portfolio_capital_budget",
            "CURRENT_PRODUCTIVE_SEMANTIC",
            "UNKNOWN_CURRENT",
            [portfolio_code],
            [],
            [
                portfolio_code,
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
            csia_record_id="portfolio_reservation",
        ),
        sobj(
            "sobj_g17_typed_vol_bind",
            "CURRENT_PRODUCTIVE_SEMANTIC",
            "UNKNOWN_CURRENT",
            [g17_code],
            ["G17-TYPED-VOL-CMC-BIND-V1", "M9-VOL-MAX-AGE-DECISION-V1"],
            [
                g17_code,
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
            csia_record_id="g17_typed_vol_cmc_bind",
        ),
        sobj(
            "sobj_m9_vol_max_age",
            "NAVIGATION_ONLY",
            "UNKNOWN_CURRENT",
            ["src/governance/m9_volatility_numeric_max_age_numeric_productive_target_v1.py"],
            ["M9-VOL-MAX-AGE-DECISION-V1"],
            [
                m9_decision,
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
            config_surfaces=[m9_decision],
            csia_record_id="m9_volatility_max_age",
        ),
        sobj(
            "sobj_elementary_direction",
            "CANONICAL_MODEL_SEMANTIC",
            "UNKNOWN_CURRENT",
            [elem_code],
            [],
            [
                elem_code,
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
            csia_record_id="elementary_direction",
        ),
        sobj(
            "sobj_full_core_cycle_orchestrator",
            "CURRENT_PRODUCTIVE_SEMANTIC",
            "UNKNOWN_CURRENT",
            [orch_code],
            ["PROD-CANONICAL-PRICE-PROVENANCE-V1"],
            [
                orch_code,
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
            csia_record_id="full_core_live_path_composition_root",
        ),
    ]

    new_edges = [
        edge(
            "edge_cap21_to_cap22",
            "PRODUCES",
            "sobj_cap21_universe",
            "sobj_cap22_ranking",
            [
                cap21_code,
                "src/ops/productive_futures_ranking_producer_v1/producer_v1.py",
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
        ),
        edge(
            "edge_cap22_to_cap23",
            "PRODUCES",
            "sobj_cap22_ranking",
            "sobj_cap23_selection",
            [
                cap22_spec,
                "src/ops/single_selected_future_policy_v1/selection_v1.py",
                "config/governance/current_system_interaction_authority_map_v1/source_v1.json",
            ],
        ),
        edge(
            "edge_handoff_cap23_cap24",
            "TRANSFORMS",
            "sobj_ranking_ssf_handoff",
            "sobj_cap24_runtime_binding",
            [ssf_spec, handoff_code, cap24_code],
        ),
        edge(
            "edge_cap24_binds_l1",
            "BINDS",
            "sobj_cap24_runtime_binding",
            "sobj_mv2_layer_l1_selected_future",
            [
                cap24_code,
                "src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/l1_selected_future_v1.py",
                "docs/evidence/master_v2_double_play_evidence_input_plane_p0/l1_l10_evidence_seam_census_v1.json",
            ],
        ),
        edge(
            "edge_pubmd_to_observation",
            "PRODUCES",
            "sobj_public_md_runtime",
            "sobj_mv2_layer_l2_market_observation",
            [
                pubmd_policy,
                "src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/l2_market_observation_v1.py",
            ],
        ),
        edge(
            "edge_g17_to_cycle",
            "TRANSFORMS",
            "sobj_g17_typed_vol_bind",
            "sobj_mv2_runtime_cycle_host",
            [
                g17_code,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py",
            ],
        ),
        edge(
            "edge_orchestrator_consumes_cap24",
            "CONSUMES",
            "sobj_full_core_cycle_orchestrator",
            "sobj_cap24_runtime_binding",
            [orch_code, cap24_code],
        ),
        edge(
            "edge_orchestrator_to_mv2_cycle",
            "CONSUMES",
            "sobj_full_core_cycle_orchestrator",
            "sobj_mv2_runtime_cycle_host",
            [
                orch_code,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py",
            ],
        ),
        edge(
            "edge_portfolio_constrains_cycle",
            "CONSTRAINS",
            "sobj_portfolio_capital_budget",
            "sobj_full_core_cycle_orchestrator",
            [portfolio_code, orch_code],
        ),
        edge(
            "edge_m9_constrains_g17",
            "CONSTRAINS",
            "sobj_m9_vol_max_age",
            "sobj_g17_typed_vol_bind",
            [m9_decision, g17_code],
        ),
        edge(
            "edge_elem_to_direction_layer",
            "PRODUCES",
            "sobj_elementary_direction",
            "sobj_mv2_layer_l3_initial_direction",
            [
                elem_code,
                "src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/l3_initial_direction_v1.py",
            ],
        ),
    ]

    new_unknown = [
        {
            "id": "unk_cap24_l1_productive_mark_provenance",
            "unknown_class": "EVIDENCE_DISCOVERY_UNKNOWN",
            "statement": "Whether Cap 2.4 bound instrument identity and composition-root canonical mark/index provenance share one CURRENT freshness/instrument binding chain is not adjudicated in durable compliance evidence.",
            "left_ref": "sobj_cap24_runtime_binding:BoundInstrumentV1",
            "right_ref": "sobj_canonical_price_provenance:venue_native_id",
            "evidence_refs": [
                cap24_code,
                "src/ops/full_core_live_path_composition_root_v1/current_productive_canonical_price_provenance_v1.py",
            ],
        },
    ]

    new_unknown = [u for u in new_unknown if u["id"] not in _SUPPRESSED_UNKNOWN_RELATION_IDS]

    divergences = [
        {
            "id": "SEM-SURF-DIV-00001",
            "adjudication": "UNKNOWN_CURRENT",
            "producer_ref": "sobj_mv2_runtime_cycle_host",
            "consumer_ref": "sobj_mv2_layer_l5_nullline",
            "statement": "M_t/mark_px at composition-root vs L5 nullline initialization_mark — identity OPEN (maps to unk_mt_l5_nullline_identity).",
            "expected_canonical_source": "UNKNOWN",
            "evidence_refs": [
                "src/ops/full_core_live_path_composition_root_v1/current_productive_master_v2_runtime_cycle_v1.py",
                "src/trading/master_v2/naked_mv2_dp_explicit_layered_core_v1/l5_nullline_v1.py",
                "tests/ops/test_current_productive_semantic_enforcement_repair_v1.py",
            ],
            "reproof_required": True,
            "unknown_relation_id": "unk_mt_l5_nullline_identity",
        },
        {
            "id": "SEM-SURF-DIV-00002",
            "adjudication": "UNKNOWN_CURRENT",
            "producer_ref": "sobj_canonical_price_provenance",
            "consumer_ref": "sobj_mv2_runtime_cycle_host",
            "statement": "Index vs mark distinctness enforced at composition-root (SEM-DIV-00001/00002 tests); downstream MV2 layer interpretation of those fields remains UNKNOWN_CURRENT for full chain.",
            "expected_canonical_source": "tests/ops/test_current_productive_semantic_enforcement_repair_v1.py",
            "evidence_refs": [
                "tests/ops/test_current_productive_semantic_enforcement_repair_v1.py",
                "src/ops/full_core_live_path_composition_root_v1/current_productive_canonical_price_provenance_v1.py",
            ],
            "reproof_required": True,
            "unknown_relation_id": None,
        },
    ]

    return {
        "law_references": new_lrefs,
        "semantic_objects": new_sobjs,
        "impact_edges": new_edges,
        "unknown_relations": new_unknown,
        "semantic_divergence_index": divergences,
    }


def discover_unclassified_current_productive(
    doc: dict[str, Any] | None = None,
    limit: int = 120,
) -> list[dict[str, Any]]:
    """List current_productive_* modules not covered by any indexed code surface."""
    indexed: set[str] = set()
    if doc is None:
        import json

        source = REPO_ROOT / "config/governance/current_law_impact_map_v1/source_v1.json"
        doc = json.loads(source.read_text(encoding="utf-8"))
    for so in doc.get("semantic_objects", []):
        for surf in so.get("code_surfaces", []):
            if surf.endswith("/"):
                for p in (REPO_ROOT / surf.rstrip("/")).rglob("*.py"):
                    indexed.add(p.relative_to(REPO_ROOT).as_posix())
            else:
                indexed.add(surf)
    unclassified: list[dict[str, Any]] = []
    for path in sorted((REPO_ROOT / "src/ops").rglob("current_productive*.py")):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in indexed:
            continue
        if any(rel.startswith(p.rstrip("/") + "/") or rel == p for p in indexed if p.endswith("/")):
            continue
        unclassified.append(
            {
                "path": rel,
                "classification": "UNCLASSIFIED_CURRENT",
                "reason": "Material CURRENT productive module not indexed in Law Impact Map code_surfaces (census WP1).",
            }
        )
        if len(unclassified) >= limit:
            break
    return unclassified
