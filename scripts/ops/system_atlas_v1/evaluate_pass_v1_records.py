"""EVALUATE_INDIVIDUALLY pass v1 payloads. Current-system comparison only.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
No disposition. No reintegration. No identity fusion.
"""

from __future__ import annotations

from typing import Any

EVALUATE_BOUND_SHA = "0e6cbb860f716d527873d97556d0968df4a197bf"
EVALUATE_BOUND_REF = "origin/main"

OVERLAP_SAME = "SAME_ARTIFACT_STILL_PRESENT"
OVERLAP_PARTIAL = "SAME_PATH_FAMILY_PARTIAL"
OVERLAP_CENSUS_DRIFT = "CENSUS_ABSENT_BUT_CURRENT_TREE_PRESENT"
OVERLAP_LATER_SURFACE = "LATER_CONSUMER_SURFACE_OVERLAP_IDENTITY_UNPROVEN"
OVERLAP_CANDIDATE = "CURRENT_FUNCTION_CANDIDATE_UNPROVEN"
OVERLAP_NONE = "NO_CURRENT_EQUIVALENT_PROVEN"

ALLOWED_OVERLAP = frozenset(
    {
        OVERLAP_SAME,
        OVERLAP_PARTIAL,
        OVERLAP_CENSUS_DRIFT,
        OVERLAP_LATER_SURFACE,
        OVERLAP_CANDIDATE,
        OVERLAP_NONE,
    }
)

COMPATIBLE = "COMPATIBLE"
PARTIAL = "PARTIAL"
UNPROVEN = "UNPROVEN"
INCOMPATIBLE = "INCOMPATIBLE"
NONE_AUTH = "COMPATIBLE_NONE_AUTHORITY"
NOT_RUNTIME = "NOT_RUNTIME"
ABSENT_RUNTIME = "ABSENT_FROM_CURRENT_RUNTIME"

LANDSCAPE_V2_PATHS = [
    "src/webui/market_dashboard_landscape_v2/",
    "src/webui/market_dashboard_landscape_shell_router_v2.py",
    "src/webui/market_dashboard_landscape_producer_binding_v2.py",
    "src/webui/market_dashboard_landscape_v2/owner_registry.py",
    "templates/peak_trade_dashboard/market_landscape_v2.html",
]
MASTER_V2_PATHS = ["src/trading/master_v2/"]
DOUBLE_PLAY_PATHS = [
    "src/trading/master_v2/double_play_composition.py",
    "src/trading/master_v2/double_play_survival.py",
    "src/trading/master_v2/double_play_capital_slot.py",
    "src/trading/master_v2/double_play_core_wiring_v1.py",
]
FORENSIC_ROOT = (
    "forensics/historical_reference/"
    "sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/"
)
SESSION_ZERO_ORDER_PATHS = [
    "src/ops/pre_economic_zero_order_evidence_session_contract_v1.py",
    "src/ops/pre_economic_zero_order_evidence_session_okx_readonly_telemetry_v1.py",
]
OBSERVABILITY_HUB_PATHS = [
    "docs/webui/observability/OBSERVABILITY_HUB_V0.md",
    "docs/webui/observability/PAPER_SHADOW_ARTIFACT_READ_MODEL_V0.md",
    "docs/webui/observability/PROMETHEUS_LOCAL_SCRAPE.yml",
]
SELECTOR_CURRENT_PATHS = [
    "src/ops/single_selected_future_policy_v1/",
    "src/ops/single_selected_future_policy_v1/policy_v1.py",
    "src/ops/single_selected_future_runtime_binding_v1/",
]
RISK_LAYER_CURRENT_PATHS = [
    "src/risk_layer/kill_switch/",
    "src/risk_layer/kill_switch/core.py",
    "src/risk_layer/risk_gate.py",
    "src/risk_layer/alerting/",
    "src/risk_layer/var_backtest/",
]


def _claim(
    cls: str,
    text: str,
    evidence: list[str],
    *,
    used_as_fact: bool = True,
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
    current_equivalent: str,
    current_paths: list[str],
    capability_overlap: str,
    semantic_compatibility: str,
    authority_compatibility: str,
    safety_compatibility: str,
    runtime_compatibility: str,
    conflicts: list[str],
    gaps: list[str],
    claims: list[dict[str, Any]],
    open_questions: list[str] | None = None,
) -> dict[str, Any]:
    if capability_overlap not in ALLOWED_OVERLAP:
        raise ValueError(f"overlap_unknown:{record_id}:{capability_overlap}")
    return {
        "record_id": record_id,
        "comparison_status": "CURRENT_SYSTEM_COMPARED",
        "compared_against_ref": EVALUATE_BOUND_REF,
        "compared_against_sha": EVALUATE_BOUND_SHA,
        "current_equivalent": current_equivalent,
        "current_paths": list(current_paths),
        "capability_overlap": capability_overlap,
        "semantic_compatibility": semantic_compatibility,
        "authority_compatibility": authority_compatibility,
        "safety_compatibility": safety_compatibility,
        "runtime_compatibility": runtime_compatibility,
        "conflicts": list(conflicts),
        "gaps": list(gaps),
        "claims": list(claims),
        "open_questions": list(open_questions or []),
        "disposition_performed": False,
        "identity_fusion_forbidden": True,
        "reintegration_performed": False,
    }


def _present(
    record_id: str,
    equivalent: str,
    paths: list[str],
    *,
    runtime: str,
    authority: str,
    safety: str,
    claims: list[dict[str, Any]],
    gaps: list[str] | None = None,
    conflicts: list[str] | None = None,
    open_questions: list[str] | None = None,
    semantic: str = COMPATIBLE,
) -> dict[str, Any]:
    return _row(
        record_id,
        current_equivalent=equivalent,
        current_paths=paths,
        capability_overlap=OVERLAP_SAME,
        semantic_compatibility=semantic,
        authority_compatibility=authority,
        safety_compatibility=safety,
        runtime_compatibility=runtime,
        conflicts=conflicts or [],
        gaps=gaps or [],
        claims=claims,
        open_questions=open_questions,
    )


def _later_landscape(
    record_id: str,
    historical_path: str,
    *,
    extra_gaps: list[str] | None = None,
    extra_claims: list[dict[str, Any]] | None = None,
    open_questions: list[str] | None = None,
) -> dict[str, Any]:
    gaps = [
        f"historical path {historical_path} is absent on {EVALUATE_BOUND_REF}@{EVALUATE_BOUND_SHA[:12]}",
        "identity versus Landscape V2 remains unproven; POSSIBLE_SAME_AS stays hypothesis",
        "current absence does not prove historical irrelevance",
    ]
    gaps.extend(extra_gaps or [])
    claims = [
        _claim(
            "CANONICAL_CURRENT_FACT",
            "GET /market read-only consumer currently exists as Landscape V2; this is not a proven identity match.",
            LANDSCAPE_V2_PATHS[:3],
        ),
        _claim(
            "FORENSIC_RAW_FACT",
            "Landscape V2 owner registry maps projection slots; it does not declare itself as product_surface_v1.",
            ["src/webui/market_dashboard_landscape_v2/owner_registry.py"],
        ),
        _claim(
            "HYPOTHESIS",
            "A later GET /market consumer may cover part of this historical purpose; replacement is not proven.",
            LANDSCAPE_V2_PATHS[:2],
            used_as_fact=False,
        ),
    ]
    claims.extend(extra_claims or [])
    return _row(
        record_id,
        current_equivalent="",
        current_paths=list(LANDSCAPE_V2_PATHS),
        capability_overlap=OVERLAP_LATER_SURFACE,
        semantic_compatibility=UNPROVEN,
        authority_compatibility=UNPROVEN,
        safety_compatibility=UNPROVEN,
        runtime_compatibility=ABSENT_RUNTIME,
        conflicts=[],
        gaps=gaps,
        claims=claims,
        open_questions=open_questions
        or [
            "Does a current Landscape V2 slot cover this historical purpose, or only share the GET /market surface?"
        ],
    )


def _archive_absent(
    record_id: str,
    historical_path: str,
    *,
    candidate_paths: list[str] | None = None,
    overlap: str = OVERLAP_NONE,
    extra_claims: list[dict[str, Any]] | None = None,
    extra_gaps: list[str] | None = None,
    open_questions: list[str] | None = None,
) -> dict[str, Any]:
    paths = list(candidate_paths or [])
    gaps = [
        f"historical archive path {historical_path} is absent on {EVALUATE_BOUND_REF}@{EVALUATE_BOUND_SHA[:12]}",
        "archive presence is not obsolete; current absence is not rejection",
    ]
    gaps.extend(extra_gaps or [])
    claims = [
        _claim(
            "CANONICAL_CURRENT_FACT",
            f"Bound current tree {EVALUATE_BOUND_SHA} does not contain {historical_path}.",
            [
                f"docs/system_atlas/reconciliation/understand/records/{record_id}.yaml",
                "docs/system_atlas/reconciliation/ledger.yaml",
            ],
        ),
    ]
    if paths:
        claims.append(
            _claim(
                "CANONICAL_CURRENT_FACT",
                "Named current paths exist; they are not proven to be the historical archive artifact.",
                paths,
            )
        )
        claims.append(
            _claim(
                "HYPOTHESIS",
                "Current modules with similar names may be later implementations; identity remains unproven.",
                paths,
                used_as_fact=False,
            )
        )
    else:
        claims.append(
            _claim(
                "CANONICAL_CURRENT_FACT",
                "No current equivalent path was proven for this archive artifact on the bound SHA.",
                ["docs/system_atlas/reconciliation/ledger.yaml"],
            )
        )
    claims.extend(extra_claims or [])
    return _row(
        record_id,
        current_equivalent="",
        current_paths=paths,
        capability_overlap=overlap,
        semantic_compatibility=UNPROVEN,
        authority_compatibility=UNPROVEN,
        safety_compatibility=NOT_RUNTIME,
        runtime_compatibility=ABSENT_RUNTIME,
        conflicts=[],
        gaps=gaps,
        claims=claims,
        open_questions=open_questions
        or ["Is there a proven current replacement, or only a later namesake?"],
    )


def evaluate_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        _present(
            "RCN-000001",
            "src/webui/market_dashboard_landscape_v2/",
            LANDSCAPE_V2_PATHS,
            runtime=COMPATIBLE,
            authority=COMPATIBLE,
            safety=COMPATIBLE,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Landscape V2 package still exists on the bound origin/main SHA as a read-only consumer.",
                    LANDSCAPE_V2_PATHS[:3],
                ),
                _claim(
                    "FORENSIC_RAW_FACT",
                    "Owner registry remains consumer-boundary mapping; AUTHORITY_EFFECT=NONE in slot notes.",
                    ["src/webui/market_dashboard_landscape_v2/owner_registry.py"],
                ),
            ],
            open_questions=[
                "Identity versus deleted product_surface_v1 remains unproven and is not decided here."
            ],
        ),
        _present(
            "RCN-000002",
            "docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md",
            [
                "docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md"
            ],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Landscape V2 Master Runbook file still exists on the bound SHA.",
                    [
                        "docs/ops/market_dashboard/"
                        "PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md"
                    ],
                ),
            ],
        ),
        _present(
            "RCN-000003",
            "docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md",
            ["docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md"],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Runbooks Landscape 2026-ready index still exists; Landscape here names a catalog.",
                    ["docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md"],
                ),
            ],
        ),
        _present(
            "RCN-000004",
            "src/trading/master_v2/",
            MASTER_V2_PATHS,
            runtime=COMPATIBLE,
            authority=COMPATIBLE,
            safety=COMPATIBLE,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "src/trading/master_v2/ remains the current Master V2 trading package path.",
                    MASTER_V2_PATHS,
                ),
            ],
        ),
        _present(
            "RCN-000005",
            "src/trading/master_v2/double_play_composition.py",
            DOUBLE_PLAY_PATHS,
            runtime=COMPATIBLE,
            authority=COMPATIBLE,
            safety=COMPATIBLE,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Double Play composition stack files still exist under src/trading/master_v2/.",
                    DOUBLE_PLAY_PATHS,
                ),
            ],
        ),
        _present(
            "RCN-000006",
            "src/ops/double_play/",
            ["src/ops/double_play/__init__.py", "src/ops/double_play/specialists.py"],
            runtime=COMPATIBLE,
            authority=COMPATIBLE,
            safety=COMPATIBLE,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "ops.double_play scaffold still exists as a projection/diagnostic consumer path.",
                    ["src/ops/double_play/__init__.py", "src/ops/double_play/specialists.py"],
                ),
            ],
        ),
        _present(
            "RCN-000007",
            FORENSIC_ROOT + "master_v2/",
            [FORENSIC_ROOT + "master_v2/"],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Forensic Master V2 extract directory still exists under historical_reference.",
                    [FORENSIC_ROOT + "master_v2/"],
                ),
            ],
        ),
        _present(
            "RCN-000008",
            FORENSIC_ROOT + "double_play/",
            [FORENSIC_ROOT + "double_play/"],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Forensic Double Play extract directory still exists under historical_reference.",
                    [FORENSIC_ROOT + "double_play/"],
                ),
            ],
        ),
        _later_landscape("RCN-000009", "src/webui/market_dashboard_product_surface_v1"),
        _later_landscape("RCN-000010", "src/webui/market_dashboard_readmodels_v1"),
        _later_landscape(
            "RCN-000011",
            "src/webui/market_visual_operator_surface_v1",
            extra_gaps=["diagnostics_summary Landscape V2 slot remains NOT_BOUND on the bound SHA"],
            extra_claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Landscape V2 diagnostics_summary slot is NOT_BOUND; visual-operator diagnostics are not proven covered.",
                    ["src/webui/market_dashboard_landscape_v2/owner_registry.py"],
                ),
            ],
        ),
        _later_landscape(
            "RCN-000012",
            "src/webui/futures_read_only_market_dashboard_runtime_v0.py",
        ),
        _present(
            "RCN-000013",
            "evidence/market_dashboard_deletion/",
            ["evidence/market_dashboard_deletion/"],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Market dashboard deletion evidence pack directory still exists.",
                    ["evidence/market_dashboard_deletion/"],
                ),
            ],
        ),
        _archive_absent("RCN-000014", "archive/PeakTradeRepo"),
        _row(
            "RCN-000015",
            current_equivalent="",
            current_paths=SELECTOR_CURRENT_PATHS,
            capability_overlap=OVERLAP_CANDIDATE,
            semantic_compatibility=UNPROVEN,
            authority_compatibility=UNPROVEN,
            safety_compatibility=UNPROVEN,
            runtime_compatibility=ABSENT_RUNTIME,
            conflicts=[],
            gaps=[
                "src/ops/master_v2_minimal_selector_v1 is absent after revert of #6165 via #6166",
                "current Single Selected Future policy is a later capability path, not a proven identity",
                "historical revert is not disposition",
            ],
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Historical master_v2_minimal_selector_v1 path is absent on the bound SHA.",
                    ["docs/system_atlas/reconciliation/understand/records/RCN-000015.yaml"],
                ),
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "src/ops/single_selected_future_policy_v1 exists and encodes SINGLE_SELECTED_FUTURE.",
                    SELECTOR_CURRENT_PATHS[:2],
                ),
                _claim(
                    "HYPOTHESIS",
                    "Cap 2.3 policy may serve a similar exactly-one selection purpose; replacement is not proven.",
                    SELECTOR_CURRENT_PATHS,
                    used_as_fact=False,
                ),
            ],
            open_questions=[
                "Is single_selected_future_policy_v1 a successor of master_v2_minimal_selector_v1, or a distinct later owner?"
            ],
        ),
        _present(
            "RCN-000016",
            "docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md",
            [
                "docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md",
                "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
            ],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "v4.4.12 file still exists on the bound SHA as a historical superseded document.",
                    ["docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md"],
                ),
                _claim(
                    "FORENSIC_RAW_FACT",
                    "Map of Truth names the Canonical Master Runbook as current working authority and v4.4.12 as SUPERSEDED.",
                    ["docs/governance/PEAK_TRADE_MAP_OF_TRUTH.md"],
                ),
            ],
            gaps=[
                "successor Master Runbook presence is documented; this is comparison, not disposition"
            ],
        ),
        _present(
            "RCN-000017",
            "docs/forensics/persistence/PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md",
            ["docs/forensics/persistence/PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md"],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Information Corpus Persistence Base markdown still exists.",
                    [
                        "docs/forensics/persistence/"
                        "PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md"
                    ],
                ),
            ],
        ),
        _present(
            "RCN-000018",
            FORENSIC_ROOT + "conservation/HISTORICAL_CHILD_LEDGER.yaml",
            [FORENSIC_ROOT + "conservation/HISTORICAL_CHILD_LEDGER.yaml"],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "HISTORICAL_CHILD_LEDGER.yaml still exists in the forensic conservation tree.",
                    [FORENSIC_ROOT + "conservation/HISTORICAL_CHILD_LEDGER.yaml"],
                ),
            ],
        ),
        _row(
            "RCN-000019",
            current_equivalent="src/risk_layer/kill_switch/",
            current_paths=RISK_LAYER_CURRENT_PATHS,
            capability_overlap=OVERLAP_PARTIAL,
            semantic_compatibility=PARTIAL,
            authority_compatibility=PARTIAL,
            safety_compatibility=PARTIAL,
            runtime_compatibility=PARTIAL,
            conflicts=[],
            gaps=[
                "historical top-level src/risk_layer/kill_switch.py is absent",
                "historical liquidity_gate.py, metrics.py, micro_metrics.py, stress_gate.py, var_gate.py are absent",
                "current package uses kill_switch/ package plus risk_gate.py; identity of each missing module is unproven",
            ],
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "src/risk_layer/kill_switch/ package exists with KillSwitch public API.",
                    [
                        "src/risk_layer/kill_switch/__init__.py",
                        "src/risk_layer/kill_switch/core.py",
                    ],
                ),
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Landscape V2 safety_authority slot names src.risk_layer.kill_switch as owner.",
                    ["src/webui/market_dashboard_landscape_v2/owner_registry.py"],
                ),
                _claim(
                    "FORENSIC_RAW_FACT",
                    "src/risk_layer/liquidity_gate.py is absent on the bound SHA.",
                    ["docs/system_atlas/reconciliation/understand/records/RCN-000019.yaml"],
                ),
            ],
            open_questions=[
                "Are LiquidityGate/StressGate/VaRGate purposes covered by current risk_gate.py or elsewhere?"
            ],
        ),
        _row(
            "RCN-000020",
            current_equivalent="",
            current_paths=[
                "docs/OBSERVABILITY_AND_MONITORING_PLAN.md",
                "docs/webui/observability/PROMETHEUS_LOCAL_SCRAPE.yml",
                "docs/ops/runbooks/finish_c/RUNBOOK_FINISH_C4_OBSERVABILITY_OPERATOR_DRYRUN.md",
            ],
            capability_overlap=OVERLAP_CANDIDATE,
            semantic_compatibility=UNPROVEN,
            authority_compatibility=UNPROVEN,
            safety_compatibility=NOT_RUNTIME,
            runtime_compatibility=NOT_RUNTIME,
            conflicts=[],
            gaps=[
                "docs/observability Grafana/OTLP runbook family is absent on the bound SHA",
                "later observability docs exist under other paths; Grafana-stack identity is unproven",
            ],
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "docs/observability/ path family is absent on the bound SHA.",
                    ["docs/system_atlas/reconciliation/understand/records/RCN-000020.yaml"],
                ),
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Later observability docs exist (plan, Prometheus scrape YAML, operator dry-run).",
                    [
                        "docs/OBSERVABILITY_AND_MONITORING_PLAN.md",
                        "docs/webui/observability/PROMETHEUS_LOCAL_SCRAPE.yml",
                    ],
                ),
                _claim(
                    "HYPOTHESIS",
                    "Later docs may cover local observability; they are not proven to be the purged Grafana family.",
                    ["docs/OBSERVABILITY_AND_MONITORING_PLAN.md"],
                    used_as_fact=False,
                ),
            ],
            open_questions=["Does a current Grafana/OTLP stack runbook exist under another path?"],
        ),
        _present(
            "RCN-000021",
            "src/webui/double_play_dashboard_display_json_route_v0.py",
            ["src/webui/double_play_dashboard_display_json_route_v0.py"],
            runtime=COMPATIBLE,
            authority=COMPATIBLE,
            safety=COMPATIBLE,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Double Play dashboard display JSON route remnant still exists.",
                    ["src/webui/double_play_dashboard_display_json_route_v0.py"],
                ),
            ],
        ),
        _present(
            "RCN-000022",
            "forensics/historical_reference/",
            ["forensics/historical_reference/"],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "forensics/historical_reference/ tree still exists on the bound SHA.",
                    ["forensics/historical_reference/"],
                ),
            ],
        ),
        _later_landscape("RCN-000023", "src/webui/market_surface.py"),
        _present(
            "RCN-000024",
            "tests/ops/test_supervised_graphical_market_landscape_presentation_only_v1.py",
            ["tests/ops/test_supervised_graphical_market_landscape_presentation_only_v1.py"],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Supervised graphical market landscape presentation contract test still exists.",
                    [
                        "tests/ops/"
                        "test_supervised_graphical_market_landscape_presentation_only_v1.py"
                    ],
                ),
            ],
        ),
        _present(
            "RCN-000025",
            "docs/system_atlas/census/historical_terminology.yaml",
            ["docs/system_atlas/census/historical_terminology.yaml"],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Atlas historical_terminology.yaml still exists and remains Atlas-authority NONE.",
                    ["docs/system_atlas/census/historical_terminology.yaml"],
                ),
            ],
        ),
        _present(
            "RCN-000026",
            "forensic/post_step32_knowledge_integration_v0/",
            ["forensic/post_step32_knowledge_integration_v0/"],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "post_step32 knowledge integration forensic tree still exists.",
                    ["forensic/post_step32_knowledge_integration_v0/"],
                ),
            ],
        ),
        _later_landscape(
            "RCN-000027",
            "src/webui/market_depth_runtime_v0.py",
            extra_gaps=["Landscape V2 owner registry has no market_depth slot on the bound SHA"],
        ),
        _later_landscape(
            "RCN-000028",
            "src/webui/market_tape_readmodel_v0",
            extra_gaps=["Landscape V2 owner registry has no market_tape slot on the bound SHA"],
        ),
        _later_landscape(
            "RCN-000029",
            "src/webui/market_ranking_funnel_runtime_v0.py",
            extra_gaps=[
                "universe_ranking Landscape slot exists; funnel-stage identity with v0 is unproven"
            ],
            extra_claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Landscape V2 universe_ranking slot binds universe_selection_readmodel.v1.",
                    ["src/webui/market_dashboard_landscape_v2/owner_registry.py"],
                ),
            ],
        ),
        _later_landscape(
            "RCN-000030",
            "src/webui/market_futures_ohlcv_runtime_v0.py",
            extra_gaps=[
                "current OHLCV bind is okx_selected_instrument_ohlcv_readmodel.v1; identity with v0 runtime is unproven"
            ],
            extra_claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "okx_selected_instrument_ohlcv_readmodel_v1 exists as a later OHLCV readmodel.",
                    ["src/ops/okx_selected_instrument_ohlcv_readmodel_v1.py"],
                ),
            ],
        ),
        _later_landscape(
            "RCN-000031",
            "src/webui/market_instrument_eligibility_v0.py",
            extra_gaps=[
                "current selection eligibility lives under single_selected_future_policy_v1; identity unproven"
            ],
        ),
        _later_landscape("RCN-000032", "src/webui/market_active_paper_run_runtime_v0.py"),
        _later_landscape("RCN-000033", "src/webui/market_dashboard_current_state_runtime_v0.py"),
        _later_landscape(
            "RCN-000034",
            "docs/product/Peak_Trade_Market_Dashboard_Architecture_Reset_and_Rebuild_Master_Runbook_v1.0.md",
            extra_gaps=[
                "current Landscape V2 runbook is a later document; identity with deleted product runbooks is unproven"
            ],
            extra_claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Current Landscape V2 Master Runbook exists; it is not proven to be these deleted product docs.",
                    [
                        "docs/ops/market_dashboard/"
                        "PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md"
                    ],
                ),
            ],
        ),
        _later_landscape(
            "RCN-000035",
            "docs/product/Peak_Trade_Runbook_v1.3_Composition_Landmark_Master_Runbook.md",
        ),
        _archive_absent(
            "RCN-000036",
            "archive/full_files_stand_02.12.2025/peak_trade_export",
            candidate_paths=["src/backtest/engine.py", "src/strategies/ma_crossover.py"],
            overlap=OVERLAP_CANDIDATE,
            extra_gaps=[
                "current backtest engine and ma_crossover exist; they are not proven to be the 02.12.2025 export blobs"
            ],
        ),
        _archive_absent("RCN-000037", "archive/legacy_docs/README.before_phase58.md"),
        _archive_absent("RCN-000038", "archive/legacy_scripts/run_regime_experiments.sh"),
        _row(
            "RCN-000039",
            current_equivalent="",
            current_paths=[
                "src/risk_layer/kill_switch/health_check.py",
                "src/core/resilience.py",
            ],
            capability_overlap=OVERLAP_CANDIDATE,
            semantic_compatibility=UNPROVEN,
            authority_compatibility=UNPROVEN,
            safety_compatibility=UNPROVEN,
            runtime_compatibility=ABSENT_RUNTIME,
            conflicts=[],
            gaps=[
                "src/infra/health package is absent on the bound SHA",
                "HealthChecker exists inside kill_switch; HealthCheck exists in src/core/resilience.py; identity with infra.health is unproven",
            ],
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "src/infra currently contains escalation and runbooks packages, not health.",
                    ["src/infra/__init__.py", "src/infra/escalation/__init__.py"],
                ),
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "A HealthChecker class exists in src/risk_layer/kill_switch/health_check.py.",
                    ["src/risk_layer/kill_switch/health_check.py"],
                ),
                _claim(
                    "HYPOTHESIS",
                    "Current health helpers may overlap historically; they are not proven to be src/infra/health.",
                    ["src/risk_layer/kill_switch/health_check.py"],
                    used_as_fact=False,
                ),
            ],
            open_questions=[
                "Did src/infra/health migrate into kill_switch health_check, core.resilience, or neither?"
            ],
        ),
        _row(
            "RCN-000040",
            current_equivalent="",
            current_paths=[],
            capability_overlap=OVERLAP_NONE,
            semantic_compatibility=UNPROVEN,
            authority_compatibility=UNPROVEN,
            safety_compatibility=UNPROVEN,
            runtime_compatibility=ABSENT_RUNTIME,
            conflicts=[],
            gaps=[
                "src/infra/backup is absent on the bound SHA",
                "no current BackupManager implementation path was proven",
            ],
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "src/infra/backup is absent; src/infra holds escalation and runbooks only.",
                    ["src/infra/__init__.py"],
                ),
            ],
            open_questions=["Does a later backup/recovery owner exist under another path?"],
        ),
        _row(
            "RCN-000041",
            current_equivalent="",
            current_paths=["src/risk_layer/alerting/"],
            capability_overlap=OVERLAP_CANDIDATE,
            semantic_compatibility=UNPROVEN,
            authority_compatibility=UNPROVEN,
            safety_compatibility=UNPROVEN,
            runtime_compatibility=ABSENT_RUNTIME,
            conflicts=[],
            gaps=[
                "src/infra/monitoring is absent on the bound SHA",
                "current risk_layer alerting exists; identity with infra.monitoring is unproven",
            ],
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "src/infra/monitoring is absent; src/risk_layer/alerting/ exists.",
                    ["src/risk_layer/alerting/__init__.py", "src/infra/__init__.py"],
                ),
                _claim(
                    "HYPOTHESIS",
                    "AlertManager in risk_layer may overlap historical infra.monitoring; replacement is not proven.",
                    ["src/risk_layer/alerting/alert_manager.py"],
                    used_as_fact=False,
                ),
            ],
            open_questions=[
                "Is risk_layer.alerting a successor of src/infra/monitoring, or a distinct later package?"
            ],
        ),
        _row(
            "RCN-000042",
            current_equivalent="",
            current_paths=["src/core/resilience.py", "src/core/resilience_helpers.py"],
            capability_overlap=OVERLAP_CANDIDATE,
            semantic_compatibility=UNPROVEN,
            authority_compatibility=UNPROVEN,
            safety_compatibility=UNPROVEN,
            runtime_compatibility=UNPROVEN,
            conflicts=[],
            gaps=[
                "src/infra/resilience is absent on the bound SHA",
                "src/core/resilience.py names CircuitBreaker and retry_with_backoff; path/identity unproven",
            ],
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "src/core/resilience.py exists and documents CircuitBreaker and retry_with_backoff.",
                    ["src/core/resilience.py"],
                ),
                _claim(
                    "HYPOTHESIS",
                    "core.resilience may be a moved successor of infra.resilience; identity is not proven.",
                    ["src/core/resilience.py"],
                    used_as_fact=False,
                ),
            ],
            open_questions=[
                "Is src/core/resilience.py the same historical package as src/infra/resilience?"
            ],
        ),
        _row(
            "RCN-000043",
            current_equivalent="",
            current_paths=SESSION_ZERO_ORDER_PATHS,
            capability_overlap=OVERLAP_CANDIDATE,
            semantic_compatibility=UNPROVEN,
            authority_compatibility=UNPROVEN,
            safety_compatibility=UNPROVEN,
            runtime_compatibility=ABSENT_RUNTIME,
            conflicts=[],
            gaps=[
                "observer/arming/evidence trio modules are absent on the bound SHA",
                "later pre_economic_zero_order evidence-session modules exist; they are not proven to be that trio",
            ],
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "pre_economic_zero_order_decision_cycle_observer_v1.py is absent on the bound SHA.",
                    ["docs/system_atlas/reconciliation/understand/records/RCN-000043.yaml"],
                ),
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "Later zero-order evidence-session contract/telemetry modules exist.",
                    SESSION_ZERO_ORDER_PATHS,
                ),
                _claim(
                    "HYPOTHESIS",
                    "Evidence-session modules may continue a related zero-order campaign; identity with the deleted trio is unproven.",
                    SESSION_ZERO_ORDER_PATHS,
                    used_as_fact=False,
                ),
            ],
            open_questions=[
                "Do current evidence-session modules replace observer/arming/evidence, or only share a campaign name?"
            ],
        ),
        _archive_absent(
            "RCN-000044",
            "archive/PeakTradeRepo/src/backtest/engine.py",
            candidate_paths=["src/backtest/engine.py"],
            overlap=OVERLAP_CANDIDATE,
            extra_gaps=[
                "current src/backtest/engine.py exists; recovered archive blob was a one-line placeholder"
            ],
        ),
        _archive_absent(
            "RCN-000045",
            "archive/PeakTradeRepo/src/risk/position_sizer.py",
            candidate_paths=["src/risk/position_sizer.py"],
            overlap=OVERLAP_CANDIDATE,
            extra_gaps=[
                "current src/risk/position_sizer.py exists; recovered archive blob was a placeholder"
            ],
        ),
        _archive_absent(
            "RCN-000046",
            "archive/PeakTradeRepo/src/strategies/ma_crossover.py",
            candidate_paths=["src/strategies/ma_crossover.py"],
            overlap=OVERLAP_CANDIDATE,
            extra_gaps=[
                "current src/strategies/ma_crossover.py exists; recovered archive blob was a placeholder"
            ],
        ),
        _later_landscape("RCN-000047", "evidence/market_dashboard_reset/pr_a"),
        _row(
            "RCN-000048",
            current_equivalent="",
            current_paths=["docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"],
            capability_overlap=OVERLAP_CANDIDATE,
            semantic_compatibility=UNPROVEN,
            authority_compatibility=UNPROVEN,
            safety_compatibility=NOT_RUNTIME,
            runtime_compatibility=NOT_RUNTIME,
            conflicts=[],
            gaps=[
                "docs/20_phases path family is absent on the bound SHA",
                "Master Runbook capability sequence exists; identity with numbered 20_phases docs is unproven",
            ],
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "docs/20_phases is absent; Canonical Master Runbook remains the current semantic authority document.",
                    ["docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"],
                ),
                _claim(
                    "HYPOTHESIS",
                    "Phase documentation may have been absorbed into the Master Runbook; that absorption is not proven here.",
                    ["docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"],
                    used_as_fact=False,
                ),
            ],
            open_questions=[
                "Were 20_phases markdowns superseded by Master Runbook sections, or lost without replacement?"
            ],
        ),
        _row(
            "RCN-000049",
            current_equivalent="",
            current_paths=["docs/PEAK_TRADE_OVERVIEW.md", "docs/ARCHITECTURE_OVERVIEW.md"],
            capability_overlap=OVERLAP_CANDIDATE,
            semantic_compatibility=UNPROVEN,
            authority_compatibility=UNPROVEN,
            safety_compatibility=NOT_RUNTIME,
            runtime_compatibility=NOT_RUNTIME,
            conflicts=[],
            gaps=[
                "docs/00_overview path family is absent on the bound SHA",
                "current overview markdowns exist at different paths; identity unproven",
            ],
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "docs/00_overview is absent; docs/PEAK_TRADE_OVERVIEW.md and docs/ARCHITECTURE_OVERVIEW.md exist.",
                    ["docs/PEAK_TRADE_OVERVIEW.md", "docs/ARCHITECTURE_OVERVIEW.md"],
                ),
            ],
            open_questions=[
                "Are current overview docs the relocated 00_overview family, or separately authored?"
            ],
        ),
        _row(
            "RCN-000050",
            current_equivalent="",
            current_paths=[
                "src/strategies/bollinger.py",
                "src/strategies/momentum.py",
                "src/strategies/trend_following.py",
            ],
            capability_overlap=OVERLAP_CANDIDATE,
            semantic_compatibility=UNPROVEN,
            authority_compatibility=UNPROVEN,
            safety_compatibility=UNPROVEN,
            runtime_compatibility=ABSENT_RUNTIME,
            conflicts=[],
            gaps=[
                "step29m v2 strategy/research modules are absent on the bound SHA",
                "parent-named strategy modules exist; they are not proven to be the step29m v2 family",
            ],
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "step29m_bollinger_bands_v2.py and sibling step29m modules are absent.",
                    ["docs/system_atlas/reconciliation/understand/records/RCN-000050.yaml"],
                ),
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "src/strategies/bollinger.py, momentum.py, and trend_following.py exist.",
                    [
                        "src/strategies/bollinger.py",
                        "src/strategies/momentum.py",
                        "src/strategies/trend_following.py",
                    ],
                ),
                _claim(
                    "HYPOTHESIS",
                    "Current strategy modules may be the parent v1 lineage step29m wrapped; identity is unproven.",
                    ["src/strategies/bollinger.py"],
                    used_as_fact=False,
                ),
            ],
            open_questions=[
                "Did step29m v2 wrappers retire into parent modules, or was the family removed without replacement?"
            ],
        ),
        _archive_absent("RCN-000051", "archive/noch_einordnen/README.md"),
        _row(
            "RCN-000052",
            current_equivalent="docs/webui/observability/OBSERVABILITY_HUB_V0.md",
            current_paths=OBSERVABILITY_HUB_PATHS,
            capability_overlap=OVERLAP_CENSUS_DRIFT,
            semantic_compatibility=COMPATIBLE,
            authority_compatibility=NONE_AUTH,
            safety_compatibility=COMPATIBLE,
            runtime_compatibility=NOT_RUNTIME,
            conflicts=[
                "census current_presence=CURRENTLY_ABSENT but origin/main@0e6cbb86 contains docs/webui/observability/"
            ],
            gaps=[
                "census presence is a historical discovery snapshot and is not rewritten here",
                "runtime GET /observability wiring is not proven by docs presence alone",
            ],
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "docs/webui/observability/OBSERVABILITY_HUB_V0.md exists on the bound SHA.",
                    ["docs/webui/observability/OBSERVABILITY_HUB_V0.md"],
                ),
                _claim(
                    "CONTRADICTION",
                    "Ledger discovery.current_presence is CURRENTLY_ABSENT while the bound current tree contains the family.",
                    [
                        "docs/system_atlas/reconciliation/ledger.yaml",
                        "docs/webui/observability/OBSERVABILITY_HUB_V0.md",
                    ],
                    used_as_fact=False,
                ),
                _claim(
                    "FORENSIC_RAW_FACT",
                    "Hub document states read-only / display-only GET /observability with no orders or activation.",
                    ["docs/webui/observability/OBSERVABILITY_HUB_V0.md"],
                ),
            ],
            open_questions=[
                "Was the family restored after the census SHA, or was census presence bound against a different tree?"
            ],
        ),
        _present(
            "RCN-000053",
            "src/docs",
            ["src/docs", "src/docs/Peak_Trade_OVERVIEW.md"],
            runtime=NOT_RUNTIME,
            authority=NONE_AUTH,
            safety=NOT_RUNTIME,
            claims=[
                _claim(
                    "CANONICAL_CURRENT_FACT",
                    "src/docs documentation tree still exists on the bound SHA.",
                    ["src/docs/Peak_Trade_OVERVIEW.md", "src/docs/CONTRIBUTING.md"],
                ),
            ],
            gaps=[
                "path remains under src/; this is comparison of presence, not a move/disposition decision"
            ],
        ),
    ]
    ids = [row["record_id"] for row in rows]
    expected = [f"RCN-{n:06d}" for n in range(1, 54)]
    if ids != expected:
        raise ValueError(f"evaluate_id_order_mismatch:{ids}")
    return rows
