"""INTEGRATE_OR_DISPOSITION pass v1 payloads. Adjudication only.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
No reintegration. No identity fusion. No runtime mutation.
"""

from __future__ import annotations

from typing import Any

ADJUDICATE_BOUND_SHA = "64aa353073ae7971a966e2f7a1e2a8d3e3c9e6d2"
ADJUDICATE_BOUND_REF = "origin/main"
EVALUATE_COMPARED_SHA = "0e6cbb860f716d527873d97556d0968df4a197bf"

RETAIN = "RETAIN_AS_IS"
INSUFFICIENT = "INSUFFICIENT_EVIDENCE"
ADAPT = "ADAPT_AND_REINTEGRATE"
COVERED = "CAPABILITY_ALREADY_COVERED"
INCOMPATIBLE = "HISTORICALLY_VALID_BUT_INCOMPATIBLE"
REJECT = "REJECT_FOR_CURRENT_SYSTEM"

ALLOWED_DISPOSITIONS = frozenset({RETAIN, INSUFFICIENT, ADAPT, COVERED, INCOMPATIBLE, REJECT})

RETAIN_IDS = (
    "RCN-000001",
    "RCN-000002",
    "RCN-000003",
    "RCN-000004",
    "RCN-000005",
    "RCN-000006",
    "RCN-000007",
    "RCN-000008",
    "RCN-000013",
    "RCN-000016",
    "RCN-000017",
    "RCN-000018",
    "RCN-000021",
    "RCN-000022",
    "RCN-000024",
    "RCN-000025",
    "RCN-000026",
    "RCN-000053",
)

LANDSCAPE_V1_IDS = (
    "RCN-000009",
    "RCN-000010",
    "RCN-000011",
    "RCN-000012",
    "RCN-000023",
    "RCN-000027",
    "RCN-000028",
    "RCN-000029",
    "RCN-000030",
    "RCN-000031",
    "RCN-000032",
    "RCN-000033",
    "RCN-000034",
    "RCN-000035",
    "RCN-000047",
)


def _claim(
    cls: str, text: str, evidence: list[str], *, used_as_fact: bool = True
) -> dict[str, Any]:
    return {
        "claim_class": cls,
        "text": text,
        "evidence": evidence,
        "used_as_fact": used_as_fact,
    }


def _row(
    record_id: str,
    *,
    disposition: str,
    lifecycle_state: str,
    identity_status: str,
    positive_reason: str,
    alternatives_rejected: list[str],
    further_evidence_required: bool,
    reintegration_candidate: bool,
    claims: list[dict[str, Any]],
    evidence_refs: list[str],
    contradictions: list[str] | None = None,
    unresolved_questions: list[str] | None = None,
) -> dict[str, Any]:
    if disposition not in ALLOWED_DISPOSITIONS:
        raise ValueError(f"disposition_unknown:{record_id}:{disposition}")
    return {
        "record_id": record_id,
        "adjudication_attempted": True,
        "disposition": disposition,
        "lifecycle_state": lifecycle_state,
        "identity_status": identity_status,
        "positive_reason": positive_reason,
        "alternatives_rejected": list(alternatives_rejected),
        "further_evidence_required": further_evidence_required,
        "reintegration_candidate": reintegration_candidate,
        "reintegration_performed": False,
        "identity_fusion_forbidden": True,
        "claims": list(claims),
        "evidence_refs": list(evidence_refs),
        "contradictions": list(contradictions or []),
        "unresolved_questions": list(unresolved_questions or []),
        "bound_against_ref": ADJUDICATE_BOUND_REF,
        "bound_against_sha": ADJUDICATE_BOUND_SHA,
        "evaluate_compared_sha": EVALUATE_COMPARED_SHA,
    }


def _retain(
    record_id: str,
    *,
    identity: str,
    reason: str,
    evidence_refs: list[str],
    alternatives_rejected: list[str],
    extra_claims: list[dict[str, Any]] | None = None,
    unresolved_questions: list[str] | None = None,
) -> dict[str, Any]:
    claims = [
        _claim(
            "ADJUDICATED_CONCLUSION",
            (
                f"{identity} remains on the bound current tree as the same artifact; "
                "current role is compatible. SAME_ARTIFACT_STILL_PRESENT is comparison, "
                "not automatic retain; retain is based on proven same-path presence plus "
                "compatible authority/safety/runtime role."
            ),
            evidence_refs,
        ),
        _claim(
            "CANONICAL_CURRENT_FACT",
            "Evaluate overlap for this record is SAME_ARTIFACT_STILL_PRESENT.",
            [f"docs/system_atlas/reconciliation/evaluate/records/{record_id}.yaml"],
        ),
    ]
    claims.extend(extra_claims or [])
    return _row(
        record_id,
        disposition=RETAIN,
        lifecycle_state="DISPOSITION_DECIDED",
        identity_status="CURRENT_IDENTITY_PROVEN_SAME_PATH",
        positive_reason=reason,
        alternatives_rejected=alternatives_rejected,
        further_evidence_required=False,
        reintegration_candidate=False,
        claims=claims,
        evidence_refs=evidence_refs,
        unresolved_questions=unresolved_questions,
    )


def _open(
    record_id: str,
    *,
    identity: str,
    identity_status: str,
    reason: str,
    evidence_refs: list[str],
    alternatives_rejected: list[str],
    extra_claims: list[dict[str, Any]] | None = None,
    contradictions: list[str] | None = None,
    unresolved_questions: list[str] | None = None,
) -> dict[str, Any]:
    claims = [
        _claim(
            "ADJUDICATED_CONCLUSION",
            (
                f"{identity}: evidence is not sufficient for a stronger terminal class. "
                "INSUFFICIENT_EVIDENCE remains OPEN and is not a rejection."
            ),
            evidence_refs,
        ),
    ]
    claims.extend(extra_claims or [])
    return _row(
        record_id,
        disposition=INSUFFICIENT,
        lifecycle_state="OPEN",
        identity_status=identity_status,
        positive_reason=reason,
        alternatives_rejected=alternatives_rejected,
        further_evidence_required=True,
        reintegration_candidate=False,
        claims=claims,
        evidence_refs=evidence_refs,
        contradictions=contradictions,
        unresolved_questions=unresolved_questions,
    )


_RETAIN_META: dict[str, dict[str, Any]] = {
    "RCN-000001": {
        "identity": "Market Dashboard Landscape V2 package",
        "reason": (
            "The same Landscape V2 consumer package remains on origin/main. "
            "UNDERSTAND binds a read-only GET /market shell with DASHBOARD_AUTHORITY_EFFECT=NONE. "
            "Current owner registry still maps projection slots without owning trading truth. "
            "Compatible present artifact; reintegration is not required because it is already current."
        ),
        "evidence": [
            "src/webui/market_dashboard_landscape_v2/",
            "src/webui/market_dashboard_landscape_v2/owner_registry.py",
            "docs/system_atlas/reconciliation/understand/records/RCN-000001.yaml",
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000001.yaml",
        ],
        "rejected": [
            "CAPABILITY_ALREADY_COVERED: this record IS the current consumer, not a duplicate to drop",
            "ADAPT_AND_REINTEGRATE: no proven embedding incompatibility for unchanged retain",
            "INSUFFICIENT_EVIDENCE: purpose, path, and current role are evidence-bound",
        ],
        "questions": [
            "Identity versus deleted product_surface_v1 remains unproven and is out of this retain scope."
        ],
    },
    "RCN-000002": {
        "identity": "Market Dashboard Landscape V2 Master Runbook",
        "reason": (
            "The same documentary runbook remains on origin/main as a non-SSOT planning index "
            "with DASHBOARD_AUTHORITY_EFFECT=NONE. Compatible current documentation artifact."
        ),
        "evidence": [
            "docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md",
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000002.yaml",
        ],
        "rejected": [
            "CAPABILITY_ALREADY_COVERED: the record is this file, not a superseded duplicate of Master Runbook",
            "REJECT_FOR_CURRENT_SYSTEM: no positive reason against keeping a non-authorizing index",
        ],
    },
    "RCN-000003": {
        "identity": "Runbooks Landscape 2026-ready index",
        "reason": (
            "The same runbook catalog remains on origin/main. UNDERSTAND binds Landscape here as a "
            "catalog name, not Market Dashboard Landscape V2. Compatible navigation document."
        ),
        "evidence": [
            "docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md",
            "docs/system_atlas/reconciliation/understand/records/RCN-000003.yaml",
        ],
        "rejected": [
            "Identity fusion with Market Landscape V2: UNDERSTAND already separates the names",
        ],
    },
    "RCN-000004": {
        "identity": "Master V2 trading package",
        "reason": (
            "src/trading/master_v2/ remains the current Master V2 package with no-live-authority "
            "package marker. Compatible current trading-model artifact; not a live arming path."
        ),
        "evidence": [
            "src/trading/master_v2/",
            "docs/system_atlas/reconciliation/understand/records/RCN-000004.yaml",
        ],
        "rejected": [
            "ADAPT_AND_REINTEGRATE: no proven need to replace the current package in this pass",
        ],
    },
    "RCN-000005": {
        "identity": "Double Play composition stack on Master V2",
        "reason": (
            "The same composition modules remain under src/trading/master_v2/. UNDERSTAND binds "
            "pure in-process composition, not execution permission. Compatible current model stack."
        ),
        "evidence": [
            "src/trading/master_v2/double_play_composition.py",
            "src/trading/master_v2/double_play_survival.py",
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000005.yaml",
        ],
        "rejected": [
            "CAPABILITY_ALREADY_COVERED by ops.double_play: UNDERSTAND binds ops as non-canonical projection",
        ],
    },
    "RCN-000006": {
        "identity": "ops.double_play specialists scaffold",
        "reason": (
            "ops.double_play remains present as SAFE DEFAULT OFF projection/diagnostic consumer "
            "with switch authority fail-closed disabled. Compatible current ops scaffold."
        ),
        "evidence": [
            "src/ops/double_play/__init__.py",
            "src/ops/double_play/specialists.py",
        ],
        "rejected": [
            "Treating ops.double_play as canonical Bull/Bear switch owner: UNDERSTAND forbids that",
        ],
    },
    "RCN-000007": {
        "identity": "Forensic historical_reference Master V2 extract",
        "reason": (
            "The SHA-256-bound forensic extract remains present with AUTHORITY=NONE. Compatible "
            "as forensic preservation, not current trading authority."
        ),
        "evidence": [
            "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/master_v2/",
        ],
        "rejected": [
            "Elevating the extract to canonical Master V2 authority: headers bind AUTHORITY=NONE",
        ],
    },
    "RCN-000008": {
        "identity": "Forensic historical_reference Double Play extract",
        "reason": (
            "The forensic Double Play extract remains present with AUTHORITY=NONE. Compatible "
            "preservation artifact, distinct from src/trading/master_v2 Double Play."
        ),
        "evidence": [
            "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/double_play/",
        ],
        "rejected": [
            "Identity fusion with RCN-000005 composition stack: different trees and authority class",
        ],
    },
    "RCN-000013": {
        "identity": "Market dashboard deletion evidence pack",
        "reason": (
            "The deletion evidence pack remains on origin/main as evidence, not runtime. "
            "Compatible forensic/evidence artifact recording the product-stack deletion."
        ),
        "evidence": ["evidence/market_dashboard_deletion/"],
        "rejected": [
            "REJECT because it documents deletion: evidence packs are not rejection of the pack itself",
        ],
    },
    "RCN-000016": {
        "identity": "Kanonisches Vollautonomie-Runbook v4.4.12",
        "reason": (
            "The superseded v4.4.12 file remains present. Map of Truth and the file header bind "
            "STATUS=SUPERSEDED and SUPERSEDED_BY the Canonical Master Runbook. Retain as historical "
            "document in that declared role, not as current authority."
        ),
        "evidence": [
            "docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md",
            "docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md",
            "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        ],
        "rejected": [
            "Using v4.4.12 as current SSOT: header and Map of Truth bind SUPERSEDED",
            "CAPABILITY_ALREADY_COVERED as a reason to delete the historical file: lineage preservation is the current role",
            "REJECT_FOR_CURRENT_SYSTEM merely because it is old: forbidden by taxonomy",
        ],
    },
    "RCN-000017": {
        "identity": "Information Corpus Persistence Base",
        "reason": (
            "The persistence-base markdown remains present with AUTHORITY=NONE / NAVIGATION_ONLY. "
            "Compatible non-authoritative navigation artifact."
        ),
        "evidence": [
            "docs/forensics/persistence/PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md",
        ],
        "rejected": ["Treating it as a second Master Runbook: header forbids override"],
    },
    "RCN-000018": {
        "identity": "Historical Child Ledger forensic extract",
        "reason": (
            "HISTORICAL_CHILD_LEDGER.yaml remains in the forensic conservation tree with "
            "AUTHORITY NONE. Compatible derived index, not canonical selection."
        ),
        "evidence": [
            "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/conservation/HISTORICAL_CHILD_LEDGER.yaml",
        ],
        "rejected": [
            "Promoting child regions to SSOT_CHILD: UNDERSTAND binds not canonical selection"
        ],
    },
    "RCN-000021": {
        "identity": "Double Play dashboard display JSON route remnant",
        "reason": (
            "The GET-only display JSON route remains present as a read-only remnant kept as a "
            "domain owner in the deletion pack. Compatible non-authorizing display route."
        ),
        "evidence": ["src/webui/double_play_dashboard_display_json_route_v0.py"],
        "rejected": [
            "Treating the route as live Double Play authority: docstring binds display-only"
        ],
    },
    "RCN-000022": {
        "identity": "Temporary Forensic Working Runbook historical_reference source",
        "reason": (
            "The historical_reference tree remains present with AUTHORITY=NONE. Compatible "
            "forensic preservation package."
        ),
        "evidence": ["forensics/historical_reference/"],
        "rejected": ["Importing this tree into runtime: README forbids runtime import"],
    },
    "RCN-000024": {
        "identity": "Supervised graphical market landscape presentation tests",
        "reason": (
            "The presentation-only contract test remains present. Compatible test artifact; "
            "not a product authority."
        ),
        "evidence": [
            "tests/ops/test_supervised_graphical_market_landscape_presentation_only_v1.py",
        ],
        "rejected": ["Dropping tests because they mention Landscape: tests are current contracts"],
    },
    "RCN-000025": {
        "identity": "Gate-Familien F1-F6 forensic heading family",
        "reason": (
            "historical_terminology.yaml remains present as Atlas terminology, not a runtime gate. "
            "Compatible HISTORICAL_ONLY heading family."
        ),
        "evidence": ["docs/system_atlas/census/historical_terminology.yaml"],
        "rejected": [
            "Treating Gate-Familien as a live gate authority: UNDERSTAND binds heading/index only"
        ],
    },
    "RCN-000026": {
        "identity": "NestedStructuralChild forensic structure type",
        "reason": (
            "The post_step32 forensic collection remains present with ARTIFACT_AUTHORITY=NONE. "
            "Compatible forensic type catalog, not SSOT_CHILD."
        ),
        "evidence": ["forensic/post_step32_knowledge_integration_v0/"],
        "rejected": ["Moving NestedStructuralChild into carrier index: finding text forbids that"],
    },
    "RCN-000053": {
        "identity": "src/docs misplaced documentation tree",
        "reason": (
            "src/docs remains present as documentation under src/. Not declared canonical SSOT. "
            "Compatible as non-authority docs; path placement is not a proven safety conflict."
        ),
        "evidence": ["src/docs/Peak_Trade_OVERVIEW.md", "src/docs/CONTRIBUTING.md"],
        "rejected": [
            "HISTORICALLY_VALID_BUT_INCOMPATIBLE solely because the path is under src/: placement is not a proven invariant breach",
            "REJECT because misplaced: taxonomy forbids rejection for inconvenience",
        ],
        "questions": [
            "Whether src/docs should later move is a separate docs-hygiene question, not this disposition."
        ],
    },
}


_LANDSCAPE_V1_META: dict[str, str] = {
    "RCN-000009": "Market dashboard product surface v1",
    "RCN-000010": "Market dashboard readmodels v1",
    "RCN-000011": "Market visual operator surface v1",
    "RCN-000012": "Futures read-only market dashboard runtime v0",
    "RCN-000023": "webui market_surface.py v0",
    "RCN-000027": "Market depth v0 readmodel/runtime",
    "RCN-000028": "Market tape v0 readmodel",
    "RCN-000029": "Market ranking funnel v0",
    "RCN-000030": "Market futures OHLCV v0",
    "RCN-000031": "Market instrument eligibility v0",
    "RCN-000032": "Market active paper run runtime v0",
    "RCN-000033": "Market dashboard current state v0",
    "RCN-000034": "Deleted market dashboard product runbooks",
    "RCN-000035": "Composition Landmark Master Runbook v1.3",
    "RCN-000047": "evidence/market_dashboard_reset pack",
}


def adjudicate_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}

    for rid, meta in _RETAIN_META.items():
        by_id[rid] = _retain(
            rid,
            identity=str(meta["identity"]),
            reason=str(meta["reason"]),
            evidence_refs=list(meta["evidence"]),
            alternatives_rejected=list(meta["rejected"]),
            unresolved_questions=list(meta.get("questions") or []),
        )

    for rid, identity in _LANDSCAPE_V1_META.items():
        by_id[rid] = _open(
            rid,
            identity=identity,
            identity_status="IDENTITY_UNPROVEN_VERSUS_LANDSCAPE_V2",
            reason=(
                f"{identity} is absent on the compared SHA. Landscape V2 is a later GET /market "
                "consumer surface (RCN-000001). Shared consumer surface is not identity and not "
                "proven replacement. Unique remaining value, coverage, and incompatibility are "
                "all unproven. Evaluate overlap LATER_CONSUMER_SURFACE_OVERLAP_IDENTITY_UNPROVEN "
                "is comparison only."
            ),
            evidence_refs=[
                f"docs/system_atlas/reconciliation/evaluate/records/{rid}.yaml",
                "docs/system_atlas/reconciliation/evaluate/records/RCN-000001.yaml",
                "src/webui/market_dashboard_landscape_v2/owner_registry.py",
            ],
            alternatives_rejected=[
                "CAPABILITY_ALREADY_COVERED: replacement by Landscape V2 is not proven",
                "ADAPT_AND_REINTEGRATE: unique current value of the deleted v1 artifact is not proven",
                "REJECT_FOR_CURRENT_SYSTEM: deletion/absence is not a positive rejection reason",
                "RETAIN_AS_IS: historical path is absent; cannot retain an absent artifact",
                "Identity fusion with RCN-000001: POSSIBLE_SAME_AS remains hypothesis",
            ],
            extra_claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Evaluate class is LATER_CONSUMER_SURFACE_OVERLAP_IDENTITY_UNPROVEN.",
                    [f"docs/system_atlas/reconciliation/evaluate/records/{rid}.yaml"],
                ),
                _claim(
                    "HYPOTHESIS",
                    "Landscape V2 may later be shown to cover part of this purpose; that is not proven here.",
                    ["src/webui/market_dashboard_landscape_v2/owner_registry.py"],
                    used_as_fact=False,
                ),
            ],
            unresolved_questions=[
                "Does a current Landscape V2 slot cover this historical purpose, or only share GET /market?"
            ],
        )

    by_id["RCN-000014"] = _open(
        "RCN-000014",
        identity="archive/PeakTradeRepo nested historical tree",
        identity_status="IDENTITY_UNPROVEN",
        reason=(
            "The nested archive tree is absent from origin/main. UNDERSTAND binds a contradiction "
            "between README claims and one-line placeholder .py blobs. No current equivalent is "
            "proven. Archive absence is not obsolete and not rejection."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/understand/records/RCN-000014.yaml",
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000014.yaml",
        ],
        alternatives_rejected=[
            "REJECT because archived/deleted: taxonomy forbids rejection for absence",
            "CAPABILITY_ALREADY_COVERED by current backtest/strategy tree: identity unproven",
        ],
        extra_claims=[
            _claim(
                "CONTRADICTION",
                "UNDERSTAND preserves PeakTradeRepo README-versus-placeholder contradiction; not used as fact.",
                ["docs/system_atlas/reconciliation/understand/records/RCN-000014.yaml"],
                used_as_fact=False,
            ),
        ],
        contradictions=[
            "PeakTradeRepo README describes an implemented stack; recovered nested .py blobs are placeholders."
        ],
        unresolved_questions=[
            "Which recovered blobs, if any, represent the claimed historical stack?"
        ],
    )

    by_id["RCN-000015"] = _open(
        "RCN-000015",
        identity="Master V2 minimal selector policy v1",
        identity_status="IDENTITY_UNPROVEN_VERSUS_CAP_2_3",
        reason=(
            "The historical selector path is absent after revert of #6165 via #6166. Historical "
            "revert is not disposition. Cap 2.3 single_selected_future_policy_v1 is a later "
            "exactly-one selection candidate. EVALUATE class CURRENT_FUNCTION_CANDIDATE_UNPROVEN "
            "does not prove successor, replacement, or identity. Semantic relationship remains open."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/understand/records/RCN-000015.yaml",
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000015.yaml",
            "src/ops/single_selected_future_policy_v1/policy_v1.py",
        ],
        alternatives_rejected=[
            "CAPABILITY_ALREADY_COVERED by Cap 2.3: replacement/identity not proven",
            "REJECT because reverted: revert is not a positive rejection reason",
            "ADAPT_AND_REINTEGRATE: unique uncovered selector semantics versus Cap 2.3 are unproven",
            "Declaring SAME_AS / successor of single_selected_future_policy_v1: forbidden without proof",
        ],
        extra_claims=[
            _claim(
                "CANONICAL_CURRENT_FACT",
                "Cap 2.3 policy encodes SINGLE_SELECTED_FUTURE; that is current-system fact, not identity with RCN-000015.",
                ["src/ops/single_selected_future_policy_v1/policy_v1.py"],
            ),
            _claim(
                "HYPOTHESIS",
                "Cap 2.3 may serve a similar exactly-one purpose; successor relation is not proven.",
                ["src/ops/single_selected_future_policy_v1/policy_v1.py"],
                used_as_fact=False,
            ),
        ],
        unresolved_questions=[
            "Is single_selected_future_policy_v1 a successor of master_v2_minimal_selector_v1, or a distinct later owner?"
        ],
    )

    by_id["RCN-000019"] = _open(
        "RCN-000019",
        identity="risk_layer historical top-level modules",
        identity_status="PARTIAL_FAMILY_IDENTITY_UNPROVEN",
        reason=(
            "The record bundles historical top-level modules. KillSwitch currently exists as "
            "src/risk_layer/kill_switch/ package; that does not prove identity with the missing "
            "historical top-level kill_switch.py, LiquidityGate, StressGate, VaRGate, or metrics "
            "modules. SAME_PATH_FAMILY_PARTIAL is comparison, not identity proof. Coverage of "
            "the missing gate functions by risk_gate.py is unproven. Record-level stronger class "
            "would silently conflate present package with absent modules."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/understand/records/RCN-000019.yaml",
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000019.yaml",
            "src/risk_layer/kill_switch/__init__.py",
            "src/risk_layer/risk_gate.py",
        ],
        alternatives_rejected=[
            "RETAIN_AS_IS for the whole family: missing historical modules are not present as those artifacts",
            "CAPABILITY_ALREADY_COVERED by kill_switch package: does not cover unproven Liquidity/Stress/VaR identity",
            "ADAPT_AND_REINTEGRATE of missing gates: unique current value versus risk_gate.py is unproven",
            "REJECT because modules were deleted: absence is not rejection",
        ],
        extra_claims=[
            _claim(
                "CANONICAL_CURRENT_FACT",
                "KillSwitch public API exists under src/risk_layer/kill_switch/; historical liquidity_gate.py is absent.",
                [
                    "src/risk_layer/kill_switch/__init__.py",
                    "docs/system_atlas/reconciliation/evaluate/records/RCN-000019.yaml",
                ],
            ),
            _claim(
                "HYPOTHESIS",
                "risk_gate.py may overlap some historical gate purposes; that overlap is not proven.",
                ["src/risk_layer/risk_gate.py"],
                used_as_fact=False,
            ),
        ],
        unresolved_questions=[
            "Are LiquidityGate/StressGate/VaRGate purposes covered by current risk_gate.py or elsewhere?",
            "Is src/risk_layer/kill_switch/ the same historical kill_switch.py or a later package?",
        ],
    )

    by_id["RCN-000020"] = _open(
        "RCN-000020",
        identity="docs/observability Grafana runbook family",
        identity_status="IDENTITY_UNPROVEN",
        reason=(
            "The Grafana/OTLP docs/observability family is absent. Later observability docs exist "
            "on other paths. Path/name similarity is not proven identity with the purged family."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000020.yaml",
            "docs/OBSERVABILITY_AND_MONITORING_PLAN.md",
        ],
        alternatives_rejected=[
            "CAPABILITY_ALREADY_COVERED by later observability docs: identity unproven",
            "REJECT because purged: purge is not a positive rejection reason",
        ],
        unresolved_questions=[
            "Does a current Grafana/OTLP stack runbook exist under another path?"
        ],
    )

    by_id["RCN-000036"] = _open(
        "RCN-000036",
        identity="archive/full_files_stand_02.12.2025 export tree",
        identity_status="IDENTITY_UNPROVEN",
        reason=(
            "The dated export is absent. Current src/backtest/engine.py and src/strategies/ma_crossover.py "
            "exist but are not proven to be the 02.12.2025 export blobs."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000036.yaml",
            "src/backtest/engine.py",
            "src/strategies/ma_crossover.py",
        ],
        alternatives_rejected=[
            "CAPABILITY_ALREADY_COVERED by current backtest/ma_crossover: blob identity unproven",
            "REJECT because archived: absence is not rejection",
        ],
    )

    by_id["RCN-000037"] = _open(
        "RCN-000037",
        identity="archive/legacy_docs",
        identity_status="IDENTITY_UNPROVEN",
        reason="The legacy_docs archive path is absent. No current equivalent is proven. Absence is not irrelevance.",
        evidence_refs=["docs/system_atlas/reconciliation/evaluate/records/RCN-000037.yaml"],
        alternatives_rejected=[
            "REJECT because archived",
            "CAPABILITY_ALREADY_COVERED by current overview docs: identity unproven",
        ],
    )

    by_id["RCN-000038"] = _open(
        "RCN-000038",
        identity="archive/legacy_scripts run_regime_experiments",
        identity_status="IDENTITY_UNPROVEN",
        reason="The archived experiment sequencer is absent. No current equivalent script is proven.",
        evidence_refs=["docs/system_atlas/reconciliation/evaluate/records/RCN-000038.yaml"],
        alternatives_rejected=[
            "REJECT because archived",
            "ADAPT_AND_REINTEGRATE: unique current value unproven",
        ],
    )

    by_id["RCN-000039"] = _open(
        "RCN-000039",
        identity="src/infra/health historical package",
        identity_status="IDENTITY_UNPROVEN",
        reason=(
            "src/infra/health is absent. HealthChecker in kill_switch and HealthCheck in "
            "src/core/resilience.py are later namesakes; identity with infra.health is unproven."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000039.yaml",
            "src/risk_layer/kill_switch/health_check.py",
            "src/core/resilience.py",
        ],
        alternatives_rejected=[
            "CAPABILITY_ALREADY_COVERED by kill_switch HealthChecker: identity unproven",
            "CAPABILITY_ALREADY_COVERED by core.resilience HealthCheck: identity unproven",
        ],
        unresolved_questions=[
            "Did src/infra/health migrate into kill_switch health_check, core.resilience, or neither?"
        ],
    )

    by_id["RCN-000040"] = _open(
        "RCN-000040",
        identity="src/infra/backup historical package",
        identity_status="IDENTITY_UNPROVEN",
        reason=(
            "src/infra/backup is absent. EVALUATE found no current BackupManager implementation path. "
            "No equivalent is proven. That is not proof the historical backup purpose is irrelevant."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000040.yaml",
            "src/infra/__init__.py",
        ],
        alternatives_rejected=[
            "REJECT because absent",
            "ADAPT_AND_REINTEGRATE: unique current uncovered backup value is not proven from remaining evidence",
        ],
        unresolved_questions=["Does a later backup/recovery owner exist under another path?"],
    )

    by_id["RCN-000041"] = _open(
        "RCN-000041",
        identity="src/infra/monitoring historical package",
        identity_status="IDENTITY_UNPROVEN",
        reason=(
            "src/infra/monitoring is absent. src/risk_layer/alerting/ exists; identity with "
            "infra.monitoring is unproven."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000041.yaml",
            "src/risk_layer/alerting/__init__.py",
        ],
        alternatives_rejected=[
            "CAPABILITY_ALREADY_COVERED by risk_layer.alerting: identity unproven"
        ],
        unresolved_questions=[
            "Is risk_layer.alerting a successor of src/infra/monitoring, or a distinct later package?"
        ],
    )

    by_id["RCN-000042"] = _open(
        "RCN-000042",
        identity="src/infra/resilience historical package",
        identity_status="IDENTITY_UNPROVEN",
        reason=(
            "src/infra/resilience is absent. src/core/resilience.py documents CircuitBreaker and "
            "retry_with_backoff; different path is not proven identity."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000042.yaml",
            "src/core/resilience.py",
        ],
        alternatives_rejected=[
            "CAPABILITY_ALREADY_COVERED by src/core/resilience.py: identity unproven"
        ],
        unresolved_questions=[
            "Is src/core/resilience.py the same historical package as src/infra/resilience?"
        ],
    )

    by_id["RCN-000043"] = _open(
        "RCN-000043",
        identity="pre_economic_zero_order observer/arming tip modules",
        identity_status="IDENTITY_UNPROVEN",
        reason=(
            "The observer/arming/evidence trio is absent. Later pre_economic_zero_order evidence-session "
            "modules exist; campaign-name similarity is not proven identity with the deleted trio."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000043.yaml",
            "src/ops/pre_economic_zero_order_evidence_session_contract_v1.py",
        ],
        alternatives_rejected=[
            "CAPABILITY_ALREADY_COVERED by evidence-session modules: identity unproven",
            "REJECT because deleted",
        ],
        unresolved_questions=[
            "Do current evidence-session modules replace observer/arming/evidence, or only share a campaign name?"
        ],
    )

    for rid, identity, path, current in (
        (
            "RCN-000044",
            "PeakTradeRepo nested backtest engine",
            "archive/PeakTradeRepo/src/backtest/engine.py",
            "src/backtest/engine.py",
        ),
        (
            "RCN-000045",
            "PeakTradeRepo nested position_sizer",
            "archive/PeakTradeRepo/src/risk/position_sizer.py",
            "src/risk/position_sizer.py",
        ),
        (
            "RCN-000046",
            "PeakTradeRepo nested ma_crossover strategy",
            "archive/PeakTradeRepo/src/strategies/ma_crossover.py",
            "src/strategies/ma_crossover.py",
        ),
    ):
        by_id[rid] = _open(
            rid,
            identity=identity,
            identity_status="IDENTITY_UNPROVEN",
            reason=(
                f"Recovered archive blob for {path} is a one-line placeholder. Current {current} "
                "exists and is not proven to be that placeholder blob. A placeholder is not proof "
                "that the intended historical capability is covered or should be rejected."
            ),
            evidence_refs=[
                f"docs/system_atlas/reconciliation/evaluate/records/{rid}.yaml",
                current,
            ],
            alternatives_rejected=[
                "CAPABILITY_ALREADY_COVERED by the current module: blob identity unproven",
                "REJECT because the recovered blob is a placeholder: intended capability remains a separate question",
                "REJECT because archived",
            ],
        )

    by_id["RCN-000048"] = _open(
        "RCN-000048",
        identity="docs/20_phases historical path family",
        identity_status="IDENTITY_UNPROVEN",
        reason=(
            "docs/20_phases is absent. The Canonical Master Runbook exists as current semantic "
            "authority. Absorption of numbered 20_phases markdowns into Master Runbook sections "
            "is not proven."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000048.yaml",
            "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
        ],
        alternatives_rejected=[
            "CAPABILITY_ALREADY_COVERED by Master Runbook: absorption/identity unproven",
            "REJECT because the path family is gone",
        ],
        unresolved_questions=[
            "Were 20_phases markdowns superseded by Master Runbook sections, or lost without replacement?"
        ],
    )

    by_id["RCN-000049"] = _open(
        "RCN-000049",
        identity="docs/00_overview historical path family",
        identity_status="IDENTITY_UNPROVEN",
        reason=(
            "docs/00_overview is absent. Current overview markdowns exist at different paths. "
            "Relocation versus separately authored docs is unproven."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000049.yaml",
            "docs/PEAK_TRADE_OVERVIEW.md",
            "docs/ARCHITECTURE_OVERVIEW.md",
        ],
        alternatives_rejected=[
            "CAPABILITY_ALREADY_COVERED by current overview docs: identity unproven",
        ],
        unresolved_questions=[
            "Are current overview docs the relocated 00_overview family, or separately authored?"
        ],
    )

    by_id["RCN-000050"] = _open(
        "RCN-000050",
        identity="step29m strategy/research family",
        identity_status="IDENTITY_UNPROVEN",
        reason=(
            "step29m v2 modules are absent. Parent-named strategy modules exist. UNDERSTAND binds "
            "step29m v2 as wrappers around parent v1; that does not prove current bollinger.py / "
            "momentum.py / trend_following.py are those wrappers or cover that family."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/understand/records/RCN-000050.yaml",
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000050.yaml",
            "src/strategies/bollinger.py",
        ],
        alternatives_rejected=[
            "CAPABILITY_ALREADY_COVERED by current strategy modules: identity with step29m v2 unproven",
            "REJECT because research family was removed",
        ],
        unresolved_questions=[
            "Did step29m v2 wrappers retire into parent modules, or was the family removed without replacement?"
        ],
    )

    by_id["RCN-000051"] = _open(
        "RCN-000051",
        identity="archive/noch_einordnen",
        identity_status="IDENTITY_UNPROVEN",
        reason=(
            "The queued archive folder is absent. UNDERSTAND binds recovered README text matching "
            "PeakTradeRepo README. No current equivalent is proven."
        ),
        evidence_refs=["docs/system_atlas/reconciliation/evaluate/records/RCN-000051.yaml"],
        alternatives_rejected=[
            "REJECT because archived",
            "Identity fusion with RCN-000014: not proven",
        ],
    )

    contradiction_052 = (
        "Ledger discovery.current_presence is CURRENTLY_ABSENT while the bound current tree "
        "contains the family."
    )
    by_id["RCN-000052"] = _open(
        "RCN-000052",
        identity="docs/webui/observability deleted family",
        identity_status="CENSUS_TREE_CONTRADICTION",
        reason=(
            "Census discovery.current_presence remains CURRENTLY_ABSENT and is not rewritten. "
            "The compared/current tree contains docs/webui/observability/OBSERVABILITY_HUB_V0.md "
            "as a read-only hub. That mismatch is a preserved contradiction. RETAIN_AS_IS would "
            "silently treat the census-deleted identity as the currently present docs without "
            "resolving lineage. CAPABILITY_ALREADY_COVERED would assume the present docs are the "
            "same family. The contradiction blocks a stronger terminal class."
        ),
        evidence_refs=[
            "docs/system_atlas/reconciliation/ledger.yaml",
            "docs/system_atlas/reconciliation/evaluate/records/RCN-000052.yaml",
            "docs/webui/observability/OBSERVABILITY_HUB_V0.md",
        ],
        alternatives_rejected=[
            "RETAIN_AS_IS: would normalize census CURRENTLY_ABSENT into a currently retained identity",
            "CAPABILITY_ALREADY_COVERED: present hub docs are not proven identical to the census-deleted family",
            "Rewriting discovery.current_presence: forbidden; census field is historical discovery fact",
            "REJECT because census said deleted",
        ],
        extra_claims=[
            _claim(
                "CANONICAL_CURRENT_FACT",
                "docs/webui/observability/OBSERVABILITY_HUB_V0.md exists on the current bound tree.",
                ["docs/webui/observability/OBSERVABILITY_HUB_V0.md"],
            ),
            _claim(
                "CONTRADICTION",
                contradiction_052,
                [
                    "docs/system_atlas/reconciliation/ledger.yaml",
                    "docs/webui/observability/OBSERVABILITY_HUB_V0.md",
                ],
                used_as_fact=False,
            ),
        ],
        contradictions=[contradiction_052],
        unresolved_questions=[
            "Was the family restored after the census SHA, or was census presence bound against a different tree?"
        ],
    )

    for n in range(1, 54):
        rid = f"RCN-{n:06d}"
        if rid not in by_id:
            raise ValueError(f"adjudication_missing:{rid}")
        rows.append(by_id[rid])
    if len(rows) != 53:
        raise ValueError(f"adjudication_count_mismatch:{len(rows)}")
    return rows
