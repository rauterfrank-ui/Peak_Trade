"""UNDERSTAND pass v1 record payloads. Historical evidence binding only.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
No EVALUATE. No disposition. No identity fusion.
"""

from __future__ import annotations

from typing import Any

UNDERSTAND_BOUND_SHA = "a70bed0dc1586bedb58642fe7f6c6fef760b2478"
DELETION_COMMIT = "b5b8172806eae55d8639f964fcb2ad036337a0f3"
DELETION_PARENT = "987e020378d1767fbd6fb1f0914d475f9a485f51"
SELECTOR_ADD_COMMIT = "75eee7bdc501ab4b0ec93812675cd074acb9e2ee"

LANDSCAPE_CLUSTER_IDS = (
    "RCN-000001",
    "RCN-000002",
    "RCN-000003",
    "RCN-000009",
    "RCN-000010",
    "RCN-000011",
    "RCN-000012",
    "RCN-000013",
    "RCN-000021",
    "RCN-000023",
    "RCN-000024",
    "RCN-000027",
    "RCN-000028",
    "RCN-000029",
    "RCN-000030",
    "RCN-000031",
    "RCN-000032",
    "RCN-000033",
    "RCN-000034",
    "RCN-000047",
)

MASTER_V2_CLUSTER_IDS = (
    "RCN-000004",
    "RCN-000005",
    "RCN-000006",
    "RCN-000007",
    "RCN-000008",
    "RCN-000015",
    "RCN-000021",
    "RCN-000022",
)


def _claim(cls: str, text: str, *evidence: str, used_as_fact: bool | None = None) -> dict[str, Any]:
    fact_classes = {
        "CANONICAL_CURRENT_FACT",
        "FORENSIC_RAW_FACT",
        "HISTORICAL_FACT",
        "ADJUDICATED_CONCLUSION",
    }
    if used_as_fact is None:
        used_as_fact = cls in fact_classes
    return {
        "claim_class": cls,
        "text": text,
        "evidence": list(evidence),
        "used_as_fact": used_as_fact,
    }


def _raw(text: str, *evidence: str) -> dict[str, Any]:
    return _claim("FORENSIC_RAW_FACT", text, *evidence)


def _hist(text: str, *evidence: str) -> dict[str, Any]:
    return _claim("HISTORICAL_FACT", text, *evidence)


def _open(text: str, *evidence: str) -> dict[str, Any]:
    return _claim("OPEN_QUESTION", text, *evidence, used_as_fact=False)


def _rel(
    relation_type: str,
    target_id: str,
    *evidence: str,
    epistemic_status: str = "FORENSIC_RAW_FACT",
) -> dict[str, Any]:
    return {
        "relation_type": relation_type,
        "target_id": target_id,
        "unresolved_target": "",
        "evidence": list(evidence),
        "epistemic_status": epistemic_status,
    }


def understood(
    *,
    rid: str,
    historical_purpose: str,
    problem: str,
    inputs: list[str],
    outputs: list[str],
    dependencies: list[str],
    consumers: list[str],
    authority_role: str,
    safety_role: str,
    runtime_role: str,
    invariants: list[str],
    claims: list[dict[str, Any]],
    open_questions: list[str],
    extra_relations: list[dict[str, Any]],
    historical_blobs: list[str],
    historical_commits: list[str],
    evidence_refs: list[str],
    clusters: list[str],
) -> dict[str, Any]:
    return {
        "record_id": rid,
        "understand_status": "PURPOSE_UNDERSTOOD",
        "purpose_understood": True,
        "historical_purpose": historical_purpose,
        "historical_problem_statement": problem,
        "historical_inputs": inputs,
        "historical_outputs": outputs,
        "historical_dependencies": dependencies,
        "historical_dependents": consumers,
        "authority_role": authority_role,
        "safety_role": safety_role,
        "runtime_role": runtime_role,
        "invariants": invariants,
        "open_questions": open_questions,
        "evidence_refs": evidence_refs,
        "historical_blobs": historical_blobs,
        "historical_commits": historical_commits,
        "clusters": clusters,
        "epistemic_class": "HISTORICAL_FACT",
        "claims": claims,
        "extra_relations": extra_relations,
        "identity_merge_performed": False,
        "current_system_compared": False,
        "disposition_decided": False,
    }


def purpose_understood_records() -> list[dict[str, Any]]:
    return [
        understood(
            rid="RCN-000001",
            historical_purpose=(
                "Read-only Market Dashboard Landscape V2 projection contracts, page "
                "aggregate/presenter, and GET /market shell. Consumer foundation only; "
                "no runtime activation, orders, or domain recomputation."
            ),
            problem=(
                "Provide a single Landscape market workspace as a strictly read-only "
                "consumer of already-produced Peak_Trade snapshots."
            ),
            inputs=[
                "Durable presentation projections / injected snapshots for bound slots",
                "okx_selected_instrument_ohlcv_readmodel.v1 for OHLCV poll",
                "Workflow Dashboard archive root for fail-closed producer binding",
            ],
            outputs=[
                "GET /market HTML via present_market_landscape_v2",
                "GET /api/market/landscape/ohlcv JSON poll payload",
                "Availability-tagged projection snapshots (never silent defaults)",
            ],
            dependencies=[
                "RCN-000002 documents this package",
                "producer binding lives in market_dashboard_landscape_producer_binding_v2",
            ],
            consumers=["RCN-000024 contract tests", "browser GET /market"],
            authority_role="DASHBOARD_AUTHORITY_EFFECT=NONE; consumer snapshots only",
            safety_role="Fail-closed unavailable/STALE; never fabricate producer outputs",
            runtime_role="Read-only SSR/JSON consumer; no order/runtime-activation imports",
            invariants=[
                "Unbound slots use explicit Availability states",
                "Package stays free of trading producer imports (binding lives outside)",
            ],
            claims=[
                _raw(
                    "Package docstring states read-only projection contracts + page shell; "
                    "no runtime activation, orders, or domain recomputation.",
                    "src/webui/market_dashboard_landscape_v2/__init__.py",
                ),
                _raw(
                    "contracts.py: consumer snapshots only; do not recompute decision, "
                    "risk, sizing, scope, or Double Play authority.",
                    "src/webui/market_dashboard_landscape_v2/contracts.py",
                ),
                _raw(
                    "Shell router: GET /market read-only SSR; no POST/PUT/PATCH/DELETE; "
                    "no execution/order/runtime-activation imports.",
                    "src/webui/market_dashboard_landscape_shell_router_v2.py",
                ),
                _raw(
                    "Producer binding lives outside the package so the package stays free "
                    "of trading/webui producer imports.",
                    "src/webui/market_dashboard_landscape_producer_binding_v2.py",
                ),
                _raw(
                    "Owner registry maps projection slots to existing canonical producer "
                    "modules; consumer boundary only.",
                    "src/webui/market_dashboard_landscape_v2/owner_registry.py",
                ),
                _open(
                    "Identity versus deleted product_surface_v1 (RCN-000009) remains "
                    "unproven; POSSIBLE_SAME_AS stays hypothesis.",
                    "docs/system_atlas/reconciliation/relations.yaml",
                ),
            ],
            open_questions=[
                "Is Landscape V2 a later generation of product_surface_v1, or a distinct package that reused dashboard naming?",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[
                "82f71bbef835e6a63453190b5eb1e3d4c2ef1884",
                "2ae6db83c45ecec9d18c2d989925103ba37fbc2d",
            ],
            evidence_refs=[
                "src/webui/market_dashboard_landscape_v2/__init__.py",
                "src/webui/market_dashboard_landscape_v2/contracts.py",
                "src/webui/market_dashboard_landscape_shell_router_v2.py",
                "src/webui/market_dashboard_landscape_producer_binding_v2.py",
                "src/webui/market_dashboard_landscape_v2/owner_registry.py",
                "templates/peak_trade_dashboard/market_landscape_v2.html",
                "static/js/market_dashboard_landscape_v2.js",
            ],
            clusters=["landscape_dashboard", "master_v2_double_play"],
        ),
        understood(
            rid="RCN-000002",
            historical_purpose=(
                "Canonical planning/handover/execution runbook for Market Dashboard "
                "Landscape V2 as a strictly read-only consumer. Documentary index; "
                "not a second technical SSOT."
            ),
            problem=(
                "Bind Landscape V2 workstream status, route, and consumer-closeout "
                "semantics for operators without raising dashboard authority."
            ),
            inputs=["Workstream phase evidence and merged capability PRs named in the runbook"],
            outputs=["Operator/planning document MARKET_DASHBOARD_V2_WORKSTREAM_COMPLETE"],
            dependencies=["RCN-000001 implementation package named as the consumer surface"],
            consumers=["Operator/agent handover for Landscape V2"],
            authority_role="Documentation Anchor role only; DASHBOARD_AUTHORITY_EFFECT=NONE",
            safety_role="LIVE_AUTHORIZED=false; ORDERS=false stated in header",
            runtime_role="Not a runtime module; documents BOUND_NOT_ACTIVATED",
            invariants=[
                "LANDSCAPE_COMPLETE_MEANS_CONSUMER_CLOSEOUT_ONLY=true",
                "LANDSCAPE_COMPLETE_DOES_NOT_MEAN_TRADING_RUNTIME_ACTIVATED=true",
            ],
            claims=[
                _raw(
                    "Header: Ziel = Neuer Market-Workspace als strikt read-only Consumer.",
                    "docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md",
                ),
                _raw(
                    "DASHBOARD_AUTHORITY_EFFECT=NONE; DASHBOARD_TRADING_INPUT=false; "
                    "DASHBOARD_SSOT=false.",
                    "docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md",
                ),
                _hist(
                    "Added 2026-07-23 as Landscape V2 master runbook (#5500).",
                    "e18a16e138d643cac5748c8ccafaea0b871a80c8",
                ),
                _open(
                    "Whether this document is a distinct component from RCN-000001 "
                    "or only its documentation remains a navigation distinction; "
                    "records are not fused.",
                ),
            ],
            open_questions=[
                "Document versus package: same Landscape V2 workstream, not proven same identity.",
            ],
            extra_relations=[
                _rel(
                    "DOCUMENTS",
                    "RCN-000001",
                    "docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md",
                ),
            ],
            historical_blobs=[],
            historical_commits=["e18a16e138d643cac5748c8ccafaea0b871a80c8"],
            evidence_refs=[
                "docs/ops/market_dashboard/PEAK_TRADE_MARKET_DASHBOARD_LANDSCAPE_MASTER_RUNBOOK_V2.md",
            ],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000003",
            historical_purpose=(
                "Central entry index of Peak_Trade runbooks and operator guides "
                "(execution, live-risk, alerts, governance, R&D). The word Landscape "
                "here names a runbook catalog, not the Market Dashboard Landscape V2 package."
            ),
            problem=(
                "Give operators/on-call/risk owners a single table to find the matching "
                "runbook in an incident or before critical actions."
            ),
            inputs=["Paths of runbooks under docs/ and docs/runbooks/"],
            outputs=["Markdown index table with scope/cluster/layer/2026-ready status"],
            dependencies=[],
            consumers=["Operators, on-call, risk owners (stated audience)"],
            authority_role="Index/navigation; not stated as SSOT",
            safety_role="R&D rows marked not live-released",
            runtime_role="Documentation only",
            invariants=["Name collision with Market Landscape is unresolved; no POSSIBLE_SAME_AS"],
            claims=[
                _raw(
                    "Title: Peak_Trade – Runbooks Landscape (2026-ready). Central entry "
                    "for all runbooks and operator guides.",
                    "docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md",
                ),
                _hist(
                    "Added 2025-12-09 as Runbooks Landscape overview.",
                    "40c057a5fe0795a3a8595e9a873628c05d3ac945",
                ),
                _open(
                    "No evidence this index is the same component as Market Dashboard "
                    "Landscape V2; records remain unfused.",
                    "docs/system_atlas/reconciliation/ledger.yaml",
                ),
            ],
            open_questions=[
                "Shared token Landscape is a naming collision, not an identity proof.",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=["40c057a5fe0795a3a8595e9a873628c05d3ac945"],
            evidence_refs=["docs/runbooks/RUNBOOKS_LANDSCAPE_2026_READY.md"],
            clusters=["landscape_dashboard", "governance_gates"],
        ),
        understood(
            rid="RCN-000004",
            historical_purpose=(
                "Direction-locked Master V2 trading package: upstream handoff-only "
                "decision-packet, local evaluator, and Double Play model modules. "
                "Package marker: no live authority."
            ),
            problem=(
                "Hold Master V2 decision-packet/local-flow/Double Play model logic "
                "without conferring live trading authority from the package itself."
            ),
            inputs=["Adapted Master V2 flow inputs / decision packet snapshots"],
            outputs=[
                "MasterV2DecisionPacketV1 and related handoff types",
                "Local flow evaluation results",
                "Double Play composition/state/survival/suitability model outputs",
            ],
            dependencies=[],
            consumers=["RCN-000005 composition stack", "RCN-000006 ops.double_play", "RCN-000021"],
            authority_role="Upstream handoff-only; no live authority (package docstring)",
            safety_role="Contains safety/kill-switch handoff types; not a live arming path",
            runtime_role="Model/local-eval package under src/trading/master_v2/",
            invariants=["__init__.py: Direction-locked Master V2: upstream handoff-only"],
            claims=[
                _raw(
                    "src/trading/master_v2/__init__.py: Direction-locked Master V2: "
                    "upstream handoff-only (no live authority).",
                    "src/trading/master_v2/__init__.py",
                ),
                _hist(
                    "Canonical dry-flow tree introduced 2026-04-23 commit c47b8907 PR #2822.",
                    "c47b89077b48a48c5f11b7c53cf8edc3b7ccd751",
                ),
                _open(
                    "Forensic extract RCN-000007 shares the Master V2 label but is a "
                    "derived index over a working-runbook blob, not this package.",
                    "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/master_v2/STRUCTURE.md",
                ),
            ],
            open_questions=[
                "POSSIBLE_SAME_AS RCN-000007 remains hypothesis; extract is derived index.",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[
                "c47b89077b48a48c5f11b7c53cf8edc3b7ccd751",
                "be0320920a772f1c8201dd321bcac8404a9cd46f",
            ],
            evidence_refs=["src/trading/master_v2/__init__.py"],
            clusters=["master_v2_double_play"],
        ),
        understood(
            rid="RCN-000005",
            historical_purpose=(
                "Pure composition of Double Play transition, survival envelope, and "
                "suitability decisions into a data-only eligibility/blocked/observe "
                "status. Not trading permission. No I/O, no execution, no registry, "
                "no live authority."
            ),
            problem=(
                "Combine Double Play model outputs for one composition step without "
                "issuing execution or live go."
            ),
            inputs=[
                "TransitionDecision + resulting SideState",
                "SurvivalEnvelopeDecision",
                "SuitabilityProjectionDecision",
                "RequestedSide",
                "optional capital-slot ratchet/release decisions",
            ],
            outputs=["DoublePlayCompositionDecision / DoublePlayCompositionStatus"],
            dependencies=["RCN-000004 modules double_play_state/survival/suitability/capital_slot"],
            consumers=[
                "RCN-000021 build_dashboard_display_snapshot / compose_double_play_decision"
            ],
            authority_role="Model-level composition; not execution or live go",
            safety_role="Can emit KILL_ALL / CHOP_GUARD / LIVE_NOT_AUTHORIZED block reasons",
            runtime_role="Pure in-process composition; no I/O",
            invariants=["ELIGIBLE_MODEL_ONLY is not trading permission"],
            claims=[
                _raw(
                    "double_play_composition.py module docstring: Pure composition; "
                    "data-only eligibility/blocked/observe; not trading permission.",
                    "src/trading/master_v2/double_play_composition.py",
                ),
                _raw(
                    "double_play_state.py: Pure, dependency-light state model; no I/O, "
                    "no exchange, no risk layer wiring.",
                    "src/trading/master_v2/double_play_state.py",
                ),
            ],
            open_questions=[
                "ops.double_play (RCN-000006) shares the Double Play name but is a "
                "quarantined projection path; POSSIBLE_SAME_AS remains hypothesis.",
            ],
            extra_relations=[
                _rel(
                    "IMPORTS",
                    "RCN-000004",
                    "src/trading/master_v2/double_play_composition.py",
                ),
            ],
            historical_blobs=[],
            historical_commits=[],
            evidence_refs=[
                "src/trading/master_v2/double_play_composition.py",
                "src/trading/master_v2/double_play_state.py",
                "src/trading/master_v2/double_play_survival.py",
                "src/trading/master_v2/double_play_capital_slot.py",
            ],
            clusters=["master_v2_double_play"],
        ),
        understood(
            rid="RCN-000006",
            historical_purpose=(
                "ops.double_play.evaluate_double_play is a SAFE DEFAULT OFF projection/"
                "diagnostic consumer. Competing SwitchGate authority is fail-closed "
                "disabled. Canonical Bull/Bear switch remains "
                "trading.master_v2.double_play_state.transition_state."
            ),
            problem=(
                "Keep a legacy ops Double Play callable from escalating to compute "
                "owner or writing SideState."
            ),
            inputs=["context dict including switch_gate state projection and flags"],
            outputs=["DoublePlayDecision frozen projection (enabled, active_specialist, reasons)"],
            dependencies=["RCN-000004 quarantine/authority-boundary modules"],
            consumers=[],
            authority_role="OPS_EVALUATE_DOUBLE_PLAY_AUTHORITY; projection only",
            safety_role="assert_path_cannot_write_side_state; switch authority disabled",
            runtime_role="ops scaffold callable; not canonical switch owner",
            invariants=["never calls step_switch_gate; never writes SideState"],
            claims=[
                _raw(
                    "evaluate_double_play docstring: SAFE DEFAULT OFF; projection/"
                    "diagnostic consumer only; never authorizes Bull/Bear switch.",
                    "src/ops/double_play/specialists.py",
                ),
                _raw(
                    "Canonical Bull/Bear / Switch authority remains "
                    "trading.master_v2.double_play_state.transition_state.",
                    "src/ops/double_play/specialists.py",
                ),
            ],
            open_questions=[
                "Whether this scaffold historically computed switches before quarantine "
                "is not reconstructed in this pass; current blob is projection-only.",
            ],
            extra_relations=[
                _rel(
                    "IMPORTS",
                    "RCN-000004",
                    "src/ops/double_play/specialists.py",
                ),
            ],
            historical_blobs=[],
            historical_commits=[],
            evidence_refs=[
                "src/ops/double_play/__init__.py",
                "src/ops/double_play/specialists.py",
            ],
            clusters=["master_v2_double_play"],
        ),
        understood(
            rid="RCN-000007",
            historical_purpose=(
                "Derived forensic index of Master V2 heading ranges inside the "
                "SHA-256-bound Temporary Forensic Working Runbook extract. Not raw "
                "evidence, not current authority, not the src/trading/master_v2 package."
            ),
            problem="Navigate Master V2 mentions in the preserved forensic working runbook blob.",
            inputs=["SOURCE_ANCHORS / source blob SHA-256 a5a468f7…"],
            outputs=["STRUCTURE.md covering heading ranges; hit count 63"],
            dependencies=["RCN-000022 historical_reference tree"],
            consumers=["Forensic navigation"],
            authority_role="AUTHORITY=NONE; CANONICAL_SELECTION=false; TRADING_AUTHORITY=false",
            safety_role="Preservation class DERIVED_INDEX",
            runtime_role="Not importable as runtime",
            invariants=["Resolve every row against the committed source blob"],
            claims=[
                _raw(
                    "master_v2/STRUCTURE.md: derived index; not raw evidence; not current "
                    "authority; Model master_v2; hit count 63.",
                    "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/master_v2/STRUCTURE.md",
                ),
                _raw(
                    "Parent README: storing the package in git does not make it canonical "
                    "working authority.",
                    "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/README.md",
                ),
            ],
            open_questions=[
                "Label overlap with RCN-000004 is not identity; POSSIBLE_SAME_AS stays hypothesis.",
            ],
            extra_relations=[
                _rel(
                    "REFERENCES",
                    "RCN-000022",
                    "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/README.md",
                ),
            ],
            historical_blobs=["a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212"],
            historical_commits=[],
            evidence_refs=[
                "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/master_v2/STRUCTURE.md",
                "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/README.md",
            ],
            clusters=["master_v2_double_play", "archives_legacy"],
        ),
        understood(
            rid="RCN-000008",
            historical_purpose=(
                "Derived forensic index of Double Play heading ranges in the same "
                "SHA-256-bound working-runbook extract. Not the src/trading/master_v2 "
                "Double Play composition stack and not ops.double_play."
            ),
            problem="Navigate Double Play mentions in the preserved forensic working runbook blob.",
            inputs=["SOURCE_ANCHORS / source blob SHA-256 a5a468f7…"],
            outputs=["STRUCTURE.md covering heading ranges; hit count 74"],
            dependencies=["RCN-000022 historical_reference tree"],
            consumers=["Forensic navigation"],
            authority_role="AUTHORITY=NONE",
            safety_role="DERIVED_INDEX",
            runtime_role="Not runtime",
            invariants=["Not raw evidence; resolve against source blob"],
            claims=[
                _raw(
                    "double_play/STRUCTURE.md: derived index; Model double_play; hit count 74.",
                    "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/double_play/STRUCTURE.md",
                ),
            ],
            open_questions=[
                "POSSIBLE_SAME_AS RCN-000005/RCN-000006 remains hypothesis.",
            ],
            extra_relations=[
                _rel(
                    "REFERENCES",
                    "RCN-000022",
                    "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/README.md",
                ),
            ],
            historical_blobs=["a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212"],
            historical_commits=[],
            evidence_refs=[
                "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/double_play/STRUCTURE.md",
            ],
            clusters=["master_v2_double_play", "archives_legacy"],
        ),
        understood(
            rid="RCN-000009",
            historical_purpose=(
                "Market Dashboard product surface v1 (PR-D): read-only presentation "
                "path source loader → page aggregate → presenter → template for GET /market."
            ),
            problem="Bind /market to a product presenter without producer I/O in the presenter.",
            inputs=["MarketDashboardPageSnapshotV1 from readmodels_v1"],
            outputs=["MarketDashboardPageContextV1 / product template context"],
            dependencies=["RCN-000010 readmodels_v1 (presenter imports)"],
            consumers=["RCN-000023 market_surface.py GET /market handler (historical)"],
            authority_role="Presentation-only; no producer I/O, no domain imports in presenter",
            safety_role="Display-only view model",
            runtime_role="Historical SSR product surface; deleted from current origin/main",
            invariants=["PRESENTER_OWNER bound to build_market_dashboard_page_context_v1"],
            claims=[
                _raw(
                    "Parent blob of deletion commit: product surface v1 read-only "
                    "presentation path source loader → page aggregate → presenter → template.",
                    f"{DELETION_PARENT}:src/webui/market_dashboard_product_surface_v1/__init__.py",
                ),
                _raw(
                    "presenter.py: Maps MarketDashboardPageSnapshotV1 to a deterministic "
                    "template view model. No producer I/O, no domain imports.",
                    f"{DELETION_PARENT}:src/webui/market_dashboard_product_surface_v1/presenter.py",
                ),
                _hist(
                    "Deleted on origin/main by commit b5b81728 "
                    "(delete(webui): remove market dashboard product stack).",
                    DELETION_COMMIT,
                ),
                _hist(
                    "Package added 2026-07-17 commit 1d61ec0d PR #5287.",
                    "1d61ec0deba49ca38a11f1a16ac53679a48608a0",
                ),
            ],
            open_questions=[
                "Not proven SAME_AS Landscape V2 (RCN-000001); deletion is not absorption proof.",
            ],
            extra_relations=[
                _rel(
                    "IMPORTS",
                    "RCN-000010",
                    f"{DELETION_PARENT}:src/webui/market_dashboard_product_surface_v1/presenter.py",
                ),
            ],
            historical_blobs=[],
            historical_commits=[
                DELETION_COMMIT,
                DELETION_PARENT,
                "1d61ec0deba49ca38a11f1a16ac53679a48608a0",
            ],
            evidence_refs=[
                f"{DELETION_PARENT}:src/webui/market_dashboard_product_surface_v1/__init__.py",
                f"{DELETION_PARENT}:src/webui/market_dashboard_product_surface_v1/presenter.py",
                "evidence/market_dashboard_deletion/deletion_manifest.txt",
            ],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000010",
            historical_purpose=(
                "Market Dashboard ReadModel contracts v1: typed, immutable, versioned, "
                "fail-closed consumer contracts for the Market Dashboard architecture "
                "reset. Producer binding was PR-C; UI/page binding was PR-D."
            ),
            problem="Give the dashboard typed consumer snapshots without owning producer truth.",
            inputs=["PR-C adapters / page source inputs (historical)"],
            outputs=["MarketDashboardPageSnapshotV1 and slot snapshot types"],
            dependencies=[],
            consumers=["RCN-000009 presenter imported these contracts"],
            authority_role="Consumer contracts; producer binding out of package (PR-C)",
            safety_role="Fail-closed availability states in contracts",
            runtime_role="Historical readmodel package; deleted with product stack",
            invariants=[
                "Package documentation path MARKET_DASHBOARD_READMODELS_V1.md named in docstring"
            ],
            claims=[
                _raw(
                    "Parent blob __init__.py: typed, immutable, versioned, fail-closed "
                    "consumer contracts for the Market Dashboard architecture reset.",
                    f"{DELETION_PARENT}:src/webui/market_dashboard_readmodels_v1/__init__.py",
                ),
                _hist(
                    "Deleted by b5b81728 with the market dashboard product stack.", DELETION_COMMIT
                ),
            ],
            open_questions=[
                "Adjacent to product_surface_v1 but a separate package; not fused.",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[
                f"{DELETION_PARENT}:src/webui/market_dashboard_readmodels_v1/__init__.py",
            ],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000011",
            historical_purpose=(
                "Market visual operator surface v1: read-only, non-authorizing SSR "
                "display for the /market dashboard visual operator zone (decision funnel, "
                "economic observability, AI linear diagnostics, compact operator header)."
            ),
            problem="Show operator-zone view models without inventing data or carrying order authority.",
            inputs=["Offline evidence bundles; ENV_EVIDENCE_ROOT / ENV_LINEAR_DIAGNOSTICS_ROOT"],
            outputs=["build_market_visual_operator_surface_context display view models"],
            dependencies=[],
            consumers=["Historical /market visual operator zone"],
            authority_role="Non-authorizing SSR display",
            safety_role="Fails closed when offline evidence bundles unconfigured or missing",
            runtime_role="Historical display package; deleted with product stack",
            invariants=["never invents data; never carries trading/runtime/order authority"],
            claims=[
                _raw(
                    "Parent blob __init__.py states read-only non-authorizing SSR display "
                    "and fail-closed missing evidence.",
                    f"{DELETION_PARENT}:src/webui/market_visual_operator_surface_v1/__init__.py",
                ),
                _hist("Deleted by b5b81728.", DELETION_COMMIT),
            ],
            open_questions=["Relation to Landscape V2 operator chrome is unproven identity."],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[
                f"{DELETION_PARENT}:src/webui/market_visual_operator_surface_v1/__init__.py",
            ],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000012",
            historical_purpose=(
                "F5 Futures Read-only Market Dashboard runtime (SSR-only, offline/fixture) "
                "behind PEAK_TRADE_F5_MARKET_DASHBOARD_ENABLED."
            ),
            problem="Render an offline/fixture futures read-only market dashboard for F5.",
            inputs=["ENV_BUNDLE_ROOT fixture bundle; env enable flag"],
            outputs=["SSR dashboard for READMODEL_ID futures_read_only_market_dashboard_v0"],
            dependencies=[],
            consumers=["Historical F5 /market fixture path"],
            authority_role="Read-only SSR; fixture/offline",
            safety_role="Env-gated enable; status model includes unsupported_for_live",
            runtime_role="Historical SSR runtime module; deleted with product stack",
            invariants=["SSR-only, offline/fixture (module docstring)"],
            claims=[
                _raw(
                    "Parent blob: F5 Futures Read-only Market Dashboard runtime "
                    "(SSR-only, offline/fixture).",
                    f"{DELETION_PARENT}:src/webui/futures_read_only_market_dashboard_runtime_v0.py",
                ),
                _hist("Deleted by b5b81728.", DELETION_COMMIT),
            ],
            open_questions=[
                "Not proven SAME_AS product_surface_v1; POSSIBLE_SAME_AS stays hypothesis."
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[
                f"{DELETION_PARENT}:src/webui/futures_read_only_market_dashboard_runtime_v0.py",
            ],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000013",
            historical_purpose=(
                "Evidence pack recording complete deletion of the market dashboard "
                "product stack (777 deleted tracked paths) while listing domain owners "
                "to keep, including src/trading/master_v2/** and "
                "double_play_dashboard_display_json_route_v0.py."
            ),
            problem="Persist forensic proof of the dashboard deletion scope and preserved domain owners.",
            inputs=["Worktree deletion diff / intended file lists"],
            outputs=["deletion_manifest.txt, preserved_domain_components.txt, inventories"],
            dependencies=[],
            consumers=["Later forensic reconstruction of deleted dashboard paths"],
            authority_role="Evidence pack; not runtime",
            safety_role="Lists KEEP_DOMAIN_OWNER for trading/master_v2 and related owners",
            runtime_role="Not a runtime component",
            invariants=["DELETED_TRACKED=777 stated in deletion_manifest.txt"],
            claims=[
                _raw(
                    "deletion_manifest.txt header: Market Dashboard complete deletion "
                    "manifest; DELETED_TRACKED=777.",
                    "evidence/market_dashboard_deletion/deletion_manifest.txt",
                ),
                _raw(
                    "preserved_domain_components.txt KEEP_DOMAIN_OWNER includes "
                    "src/trading/master_v2/** and "
                    "src/webui/double_play_dashboard_display_json_route_v0.py.",
                    "evidence/market_dashboard_deletion/preserved_domain_components.txt",
                ),
            ],
            open_questions=[
                "Pack documents deletion; it does not prove Landscape V2 identity with v1."
            ],
            extra_relations=[
                _rel(
                    "REFERENCES",
                    "RCN-000009",
                    "evidence/market_dashboard_deletion/deletion_manifest.txt",
                ),
                _rel(
                    "REFERENCES",
                    "RCN-000004",
                    "evidence/market_dashboard_deletion/preserved_domain_components.txt",
                ),
                _rel(
                    "REFERENCES",
                    "RCN-000021",
                    "evidence/market_dashboard_deletion/preserved_domain_components.txt",
                ),
            ],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT],
            evidence_refs=[
                "evidence/market_dashboard_deletion/deletion_manifest.txt",
                "evidence/market_dashboard_deletion/preserved_domain_components.txt",
            ],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000015",
            historical_purpose=(
                "Master V2 minimal selector V1 owner policy: census → structural "
                "eligibility → exactly-one-or-none → durable artifact → narrowed "
                "runtime-binding adapter. Ranking is not a selection authority. "
                "HISTORICAL_CLAIM=false on the package."
            ),
            problem="Select exactly one or none Master V2 instrument under an owner policy, not GFU ranking.",
            inputs=["Census/eligibility inputs to decide_master_v2_minimal_selection_v1"],
            outputs=["MasterV2SelectionDecisionV1 durable artifact"],
            dependencies=["RCN-000004 (name/path refer to Master V2)"],
            consumers=["runtime_binding_adapter_v1 (historical package)"],
            authority_role="Owner policy selector; ranking is not selection authority",
            safety_role="exactly-one-or-none",
            runtime_role="Historical ops package; currently absent after revert of #6165 via #6166",
            invariants=["OWNER_POLICY_VERSION=V1; HISTORICAL_CLAIM=false"],
            claims=[
                _raw(
                    "Add-commit blob: Master V2 minimal selector V1 (Owner policy; not "
                    "historical GFU semantics). Ranking is not a selection authority.",
                    f"{SELECTOR_ADD_COMMIT}:src/ops/master_v2_minimal_selector_v1/__init__.py",
                ),
                _hist(
                    "Added in feat(ops): add Master V2 minimal selector policy V1 (#6165).",
                    SELECTOR_ADD_COMMIT,
                ),
            ],
            open_questions=[
                "Current absence after revert is not a disposition of the historical purpose.",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[SELECTOR_ADD_COMMIT],
            evidence_refs=[
                f"{SELECTOR_ADD_COMMIT}:src/ops/master_v2_minimal_selector_v1/__init__.py",
            ],
            clusters=["master_v2_double_play", "governance_gates"],
        ),
        understood(
            rid="RCN-000016",
            historical_purpose=(
                "Historical predecessor strategic/operational implementation runbook "
                "(v4.4.12). File header: DOCUMENT_CLASS=HISTORICAL; STATUS=SUPERSEDED; "
                "SUPERSEDED_BY canonical Master Runbook; AUTHORITY_EFFECT=NONE."
            ),
            problem=(
                "Preserve the superseded Vollautonomie runbook as historical predecessor "
                "reference without remaining current implementation authority."
            ),
            inputs=[],
            outputs=["Historical markdown runbook body"],
            dependencies=[],
            consumers=["Historical predecessor reference (stated in header)"],
            authority_role="NONE; superseded; must not be used as current authority",
            safety_role="Header: PHASE_1_SAFETY_BOUNDS_REMAIN_CURRENTLY_BINDING is a "
            "document claim, not evaluated here",
            runtime_role="Documentation only",
            invariants=["NON_CURRENT_RUNTIME_TRUTH=true"],
            claims=[
                _raw(
                    "Header STATUS=SUPERSEDED; SUPERSEDED_BY="
                    "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md; "
                    "AUTHORITY_EFFECT=NONE.",
                    "docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md",
                ),
            ],
            open_questions=[
                "Whether any body sections remain binding is not adjudicated in UNDERSTAND.",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[],
            evidence_refs=[
                "docs/governance/Peak_Trade_Kanonisches_Vollautonomie_Runbook_v4.4.12.md",
            ],
            clusters=["governance_gates"],
        ),
        understood(
            rid="RCN-000017",
            historical_purpose=(
                "Non-authoritative information-corpus persistence base: registry and "
                "navigation only so a later agent can continue without chat memory. "
                "Must not override Master Runbook or Map of Truth."
            ),
            problem="Persist discovery/identity/provenance registration for corpus work.",
            inputs=["Repo locators and authorized external read-only surfaces (stated)"],
            outputs=["Registry/navigation markdown under docs/forensics/persistence/"],
            dependencies=[],
            consumers=["Later main agent continuation (stated)"],
            authority_role="AUTHORITY=NONE; NAVIGATION_ONLY=true; CANONICAL=false",
            safety_role="Must not activate live/testnet/orders/credentials",
            runtime_role="Documentation/registry only",
            invariants=["INDEX_ENTRY_IS_NOT_ADJUDICATION=true"],
            claims=[
                _raw(
                    "DOCUMENT_CLASS=NON_AUTHORITATIVE_INFORMATION_CORPUS_PERSISTENCE_BASE; "
                    "DOCUMENT_ROLE=REGISTRY_AND_NAVIGATION_ONLY.",
                    "docs/forensics/persistence/PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md",
                ),
            ],
            open_questions=[],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[],
            evidence_refs=[
                "docs/forensics/persistence/PEAK_TRADE_INFORMATION_CORPUS_PERSISTENCE_BASE.md",
            ],
            clusters=["archives_legacy"],
        ),
        understood(
            rid="RCN-000021",
            historical_purpose=(
                "Master V2 Double Play read-only dashboard display JSON route v0: "
                "GET-only snapshot from pure build_dashboard_display_snapshot using a "
                "static in-memory long/bull + capital-slot fixture (no scanner, exchange, "
                "session, or market-data)."
            ),
            problem="Expose Double Play composition as read-only JSON without live inputs.",
            inputs=["Static in-memory fixture SideState/capital-slot/survival/suitability"],
            outputs=["JSONResponse under prefix /api/master-v2/double-play"],
            dependencies=["RCN-000005 compose_double_play_decision", "RCN-000004 modules"],
            consumers=["Read-only dashboard JSON clients"],
            authority_role="Read-only display route; tags include dashboard-display-readonly",
            safety_role="No scanner/exchange/session/market-data (module docstring)",
            runtime_role="FastAPI GET route remnant; kept as domain owner in deletion pack",
            invariants=["GET-only; fixture-driven"],
            claims=[
                _raw(
                    "Module docstring: GET-only snapshot from pure "
                    "build_dashboard_display_snapshot; static in-memory fixture.",
                    "src/webui/double_play_dashboard_display_json_route_v0.py",
                ),
                _raw(
                    "Imports compose_double_play_decision and transition_state from "
                    "trading.master_v2.",
                    "src/webui/double_play_dashboard_display_json_route_v0.py",
                ),
            ],
            open_questions=[
                "POSSIBLE_SAME_AS RCN-000005 is naming/use, not identity of the route vs composition module.",
            ],
            extra_relations=[
                _rel(
                    "IMPORTS",
                    "RCN-000004",
                    "src/webui/double_play_dashboard_display_json_route_v0.py",
                ),
                _rel(
                    "CALLS",
                    "RCN-000005",
                    "src/webui/double_play_dashboard_display_json_route_v0.py",
                ),
            ],
            historical_blobs=[],
            historical_commits=[],
            evidence_refs=[
                "src/webui/double_play_dashboard_display_json_route_v0.py",
                "docs/ops/specs/MASTER_V2_DOUBLE_PLAY_WEBUI_READONLY_ROUTE_CONTRACT_V0.md",
            ],
            clusters=["landscape_dashboard", "master_v2_double_play"],
        ),
        understood(
            rid="RCN-000022",
            historical_purpose=(
                "Immutable historical forensic reference package bound to SHA-256 "
                "a5a468f7… of PEAK_TRADE_TEMPORARY_FORENSIC_WORKING_RUNBOOK.md. "
                "Git storage does not make it canonical working authority."
            ),
            problem="Preserve a forensic working-runbook blob with derived indexes without promoting it.",
            inputs=["Source blob via gated ingress path named in README"],
            outputs=["provenance/, master_v2/, double_play/, conservation/, schemas/ trees"],
            dependencies=[],
            consumers=["RCN-000007", "RCN-000008", "RCN-000018 conservation child ledger"],
            authority_role="AUTHORITY=NONE; CANONICAL_SELECTION=false",
            safety_role="Do not import this tree from runtime code (README)",
            runtime_role="Forensic preservation tree",
            invariants=["REPO_PRESERVATION != CANONICAL_PROMOTION"],
            claims=[
                _raw(
                    "README: immutable historical forensic reference; storing it in git "
                    "does not make it canonical working authority.",
                    "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/README.md",
                ),
            ],
            open_questions=[],
            extra_relations=[],
            historical_blobs=["a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212"],
            historical_commits=[],
            evidence_refs=[
                "forensics/historical_reference/sha256-a5a468f761e24e17fc0402dbf056df7d45090b3c58f0e9a2ad469569e908e212/README.md",
            ],
            clusters=["master_v2_double_play", "archives_legacy"],
        ),
        understood(
            rid="RCN-000023",
            historical_purpose=(
                "Read-only Market Surface module: GET /market bound to PR-D product "
                "surface (build_market_dashboard_product_template_context_v1 → presenter "
                "→ market_dashboard_product_v1.html). Legacy producers remain unreachable "
                "from the routed GET /market handler."
            ),
            problem="Own the GET /market route for the v1 product surface.",
            inputs=["PR-D product template context builder"],
            outputs=["GET /market HTML; GET /api/market/ohlcv JSON (legacy kraken/dummy)"],
            dependencies=["RCN-000009 product surface"],
            consumers=["Historical browser /market"],
            authority_role="Read-only product surface route",
            safety_role="Legacy producers unreachable from routed GET /market (docstring)",
            runtime_role="Historical FastAPI/SSR module; deleted with product stack",
            invariants=["PR-D binds /market to product presenter"],
            claims=[
                _raw(
                    "Parent blob: Read-only Market Surface — PR-D product surface on GET /market.",
                    f"{DELETION_PARENT}:src/webui/market_surface.py",
                ),
                _hist("Deleted by b5b81728.", DELETION_COMMIT),
            ],
            open_questions=["POSSIBLE_SAME_AS RCN-000012 remains hypothesis."],
            extra_relations=[
                _rel(
                    "CALLS",
                    "RCN-000009",
                    f"{DELETION_PARENT}:src/webui/market_surface.py",
                ),
            ],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[f"{DELETION_PARENT}:src/webui/market_surface.py"],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000024",
            historical_purpose=(
                "Contract tests proving supervised graphical Market Landscape "
                "presentation-only v1: existing JSON routes stay semantically compatible; "
                "GET /landscape returns text/html; static CSS/JS HTTP 200; no "
                "direct_browser_okx path in JS."
            ),
            problem="Prove Landscape presentation-only HTTP/static contracts without changing route semantics.",
            inputs=["create_o2_dashboard_http_app_v1; durable read model fixture"],
            outputs=["pytest assertions over /health /market /landscape /ohlcv"],
            dependencies=["RCN-000001 templates/JS and dashboard HTTP host"],
            consumers=[],
            authority_role="Test-only; not a product authority",
            safety_role="Asserts failures are visible; no direct_browser_okx",
            runtime_role="pytest contract tests",
            invariants=["Legacy browser_payload is not required"],
            claims=[
                _raw(
                    "Module docstring lists GET /landscape HTML, static CSS/JS 200, "
                    "no direct_browser_okx path in JS.",
                    "tests/ops/test_supervised_graphical_market_landscape_presentation_only_v1.py",
                ),
                _raw(
                    "Test file references static/js/market_dashboard_landscape_v2.js and "
                    "templates/peak_trade_dashboard/market_landscape_v2.html.",
                    "tests/ops/test_supervised_graphical_market_landscape_presentation_only_v1.py",
                ),
            ],
            open_questions=["POSSIBLE_SAME_AS RCN-000001 is test-to-package, not identity fusion."],
            extra_relations=[
                _rel(
                    "TESTS",
                    "RCN-000001",
                    "tests/ops/test_supervised_graphical_market_landscape_presentation_only_v1.py",
                ),
            ],
            historical_blobs=[],
            historical_commits=[],
            evidence_refs=[
                "tests/ops/test_supervised_graphical_market_landscape_presentation_only_v1.py",
            ],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000027",
            historical_purpose=(
                "Market Depth runtime resolution (env + offline bundle builder), shared "
                "by HTTP and future SSR. Env-gated PEAK_TRADE_MARKET_DEPTH_ENABLED."
            ),
            problem="Resolve market-depth readmodel payload from an offline bundle for display.",
            inputs=["ENV_BUNDLE_ROOT offline bundle"],
            outputs=["build_market_depth_readmodel_v0 JSON dict"],
            dependencies=["market_depth_readmodel_v0 package (same historical family)"],
            consumers=["Historical HTTP/SSR depth display"],
            authority_role="Readmodel runtime; env-gated",
            safety_role="Offline bundle; no live book inferred from docstring",
            runtime_role="Historical; deleted with product stack",
            invariants=["READMODEL_ID from depth builder"],
            claims=[
                _raw(
                    "Parent blob: Market Depth runtime resolution (env + offline bundle builder).",
                    f"{DELETION_PARENT}:src/webui/market_depth_runtime_v0.py",
                ),
                _hist("Deleted by b5b81728.", DELETION_COMMIT),
            ],
            open_questions=["POSSIBLE_SAME_AS RCN-000009 is generation hypothesis only."],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[f"{DELETION_PARENT}:src/webui/market_depth_runtime_v0.py"],
            clusters=["landscape_dashboard", "data_market"],
        ),
        understood(
            rid="RCN-000028",
            historical_purpose=(
                "Read-only Market Trades/Tape readmodel v0: intentionally pure/offline "
                "with no provider calls, no network, no trading-side handles, no dashboard polling."
            ),
            problem="Build an offline tape/trades readmodel for display.",
            inputs=["Offline bundle via ENV_BUNDLE_ROOT when enabled"],
            outputs=["build_market_tape_readmodel_v0 JSON dict"],
            dependencies=[],
            consumers=["Historical tape display"],
            authority_role="AUTHORITY_BOUNDARY exported; read-only",
            safety_role="No provider/network/trading handles (docstring)",
            runtime_role="Historical package; deleted with product stack",
            invariants=["pure/offline for v0"],
            claims=[
                _raw(
                    "Parent blob: no provider calls, no network, no trading-side handles, "
                    "no dashboard polling.",
                    f"{DELETION_PARENT}:src/webui/market_tape_readmodel_v0/__init__.py",
                ),
                _hist("Deleted by b5b81728.", DELETION_COMMIT),
            ],
            open_questions=[],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[f"{DELETION_PARENT}:src/webui/market_tape_readmodel_v0/__init__.py"],
            clusters=["landscape_dashboard", "data_market"],
        ),
        understood(
            rid="RCN-000029",
            historical_purpose=(
                "Market Ranking Funnel runtime resolution (env + offline bundle), SSR-only. "
                "Stages labeled universe/shortlist/selected."
            ),
            problem="Resolve ranking-funnel readmodel from an offline bundle for SSR.",
            inputs=["PEAK_TRADE_MARKET_RANKING_FUNNEL_BUNDLE_ROOT"],
            outputs=["build_market_ranking_funnel_readmodel payload"],
            dependencies=[],
            consumers=["Historical SSR ranking funnel"],
            authority_role="SSR-only env-gated runtime",
            safety_role="Offline bundle",
            runtime_role="Historical; deleted with product stack",
            invariants=["SSR-only (module docstring)"],
            claims=[
                _raw(
                    "Parent blob: Market Ranking Funnel runtime resolution (env + offline bundle), SSR-only.",
                    f"{DELETION_PARENT}:src/webui/market_ranking_funnel_runtime_v0.py",
                ),
                _hist("Deleted by b5b81728.", DELETION_COMMIT),
            ],
            open_questions=["POSSIBLE_SAME_AS RCN-000009 is hypothesis."],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[f"{DELETION_PARENT}:src/webui/market_ranking_funnel_runtime_v0.py"],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000030",
            historical_purpose=(
                "Market Futures OHLCV runtime resolution (env + offline bundle), SSR-only."
            ),
            problem="Resolve futures OHLCV readmodel from an offline bundle for SSR.",
            inputs=["PEAK_TRADE_MARKET_FUTURES_OHLCV_BUNDLE_ROOT"],
            outputs=["build_market_futures_ohlcv_readmodel payload"],
            dependencies=[],
            consumers=["Historical SSR OHLCV panel"],
            authority_role="SSR-only env-gated",
            safety_role="Offline bundle",
            runtime_role="Historical; deleted with product stack",
            invariants=["SSR-only"],
            claims=[
                _raw(
                    "Parent blob: Market Futures OHLCV runtime resolution (env + offline bundle), SSR-only.",
                    f"{DELETION_PARENT}:src/webui/market_futures_ohlcv_runtime_v0.py",
                ),
                _hist("Deleted by b5b81728.", DELETION_COMMIT),
            ],
            open_questions=["POSSIBLE_SAME_AS RCN-000012 is hypothesis."],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[f"{DELETION_PARENT}:src/webui/market_futures_ohlcv_runtime_v0.py"],
            clusters=["landscape_dashboard", "data_market"],
        ),
        understood(
            rid="RCN-000031",
            historical_purpose=(
                "Canonical instrument eligibility/exclusion for read-only market dashboard "
                "(SSR-only). CANONICAL_EXCLUSION_OWNER bound to this file; Bitcoin base "
                "aliases and instrument IDs listed."
            ),
            problem="Exclude/label instruments (including Bitcoin aliases) for the read-only dashboard.",
            inputs=["Instrument id/symbol strings"],
            outputs=["Eligibility/exclusion classification (module-level constants and helpers)"],
            dependencies=[],
            consumers=["Historical read-only market dashboard"],
            authority_role="Canonical exclusion owner string self-declared",
            safety_role="SSR-only dashboard eligibility; not an order gate in the recovered header",
            runtime_role="Historical module; deleted with product stack",
            invariants=["SSR-only (module docstring)"],
            claims=[
                _raw(
                    "Parent blob: Canonical instrument eligibility / exclusion for "
                    "read-only market dashboard (SSR-only).",
                    f"{DELETION_PARENT}:src/webui/market_instrument_eligibility_v0.py",
                ),
                _hist("Deleted by b5b81728.", DELETION_COMMIT),
            ],
            open_questions=["POSSIBLE_SAME_AS RCN-000009 is hypothesis."],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[f"{DELETION_PARENT}:src/webui/market_instrument_eligibility_v0.py"],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000032",
            historical_purpose=(
                "SSR-only active Paper run panel for GET /market (env-gated, "
                "bridge/staging evidence)."
            ),
            problem="Show an active paper-run panel from bridge evidence without making it a control surface.",
            inputs=["PEAK_TRADE_MARKET_ACTIVE_PAPER_RUN_BRIDGE_ROOT"],
            outputs=["SSR panel context; ACTIVE_IDLE_MINUTES=10"],
            dependencies=[],
            consumers=["Historical GET /market paper-run panel"],
            authority_role="Env-gated SSR panel",
            safety_role="bridge/staging evidence (docstring)",
            runtime_role="Historical; deleted with product stack",
            invariants=["SSR-only"],
            claims=[
                _raw(
                    "Parent blob: SSR-only active Paper run panel for GET /market "
                    "(env-gated, bridge/staging evidence).",
                    f"{DELETION_PARENT}:src/webui/market_active_paper_run_runtime_v0.py",
                ),
                _hist("Deleted by b5b81728.", DELETION_COMMIT),
            ],
            open_questions=["POSSIBLE_SAME_AS RCN-000012 is hypothesis."],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[f"{DELETION_PARENT}:src/webui/market_active_paper_run_runtime_v0.py"],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000033",
            historical_purpose=(
                "SSR display context for STEP29M current-state panel on GET /market "
                "(always on, view-only). Builds template context from "
                "market_dashboard_current_state_snapshot_v0 with controls_allowed=False."
            ),
            problem="Show current-system/governance/evidence snapshot on /market without controls.",
            inputs=["market_dashboard_current_state_snapshot_v0()"],
            outputs=["template context with view_only=True, controls_allowed=False"],
            dependencies=[],
            consumers=["Historical GET /market current-state panel"],
            authority_role="view-only SSR; no duplicate SSOT (docstring)",
            safety_role="controls_allowed=False",
            runtime_role="Historical; deleted with product stack",
            invariants=["always on, view-only"],
            claims=[
                _raw(
                    "Parent blob: SSR display context for STEP29M current-state panel "
                    "on GET /market (always on, view-only).",
                    f"{DELETION_PARENT}:src/webui/market_dashboard_current_state_runtime_v0.py",
                ),
                _hist("Deleted by b5b81728.", DELETION_COMMIT),
            ],
            open_questions=[
                "POSSIBLE_SAME_AS RCN-000001 is later-landscape naming hypothesis only."
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[
                f"{DELETION_PARENT}:src/webui/market_dashboard_current_state_runtime_v0.py",
            ],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000034",
            historical_purpose=(
                "Deleted Market Dashboard product-surface documentation: PR-D ownership "
                "of page aggregate/presenter/route/template and GET /market path. "
                "Authority/SSOT reference pointed at the Architecture Reset Master Runbook "
                "without duplicating it."
            ),
            problem="Document the v1 product surface owners and GET /market binding.",
            inputs=[],
            outputs=["Markdown ownership/path documentation"],
            dependencies=["RCN-000009 / RCN-000010 owners named in the doc"],
            consumers=["Historical implementers of PR-D"],
            authority_role="Documentation; points to product runbook as SSOT reference",
            safety_role="Not runtime",
            runtime_role="Deleted docs with product stack",
            invariants=["Active route owner: product surface only (document text)"],
            claims=[
                _raw(
                    "Parent blob: Market Dashboard Product Surface v1 (PR-D; active after merge) "
                    "with GET /market path through source_loader → page_builder → presenter.",
                    f"{DELETION_PARENT}:docs/webui/MARKET_DASHBOARD_PRODUCT_SURFACE_V1.md",
                ),
                _hist("Deleted by b5b81728.", DELETION_COMMIT),
            ],
            open_questions=[
                "POSSIBLE_SAME_AS RCN-000009/011 remains documentation-to-code hypothesis."
            ],
            extra_relations=[
                _rel(
                    "DOCUMENTS",
                    "RCN-000009",
                    f"{DELETION_PARENT}:docs/webui/MARKET_DASHBOARD_PRODUCT_SURFACE_V1.md",
                ),
            ],
            historical_blobs=[],
            historical_commits=[DELETION_COMMIT, DELETION_PARENT],
            evidence_refs=[
                f"{DELETION_PARENT}:docs/webui/MARKET_DASHBOARD_PRODUCT_SURFACE_V1.md",
            ],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000047",
            historical_purpose=(
                "Historical evidence/market_dashboard_reset pack (pr_a family in census). "
                "Bound as CURRENTLY_ABSENT path family related by name to the later "
                "deletion evidence pack; purpose of the reset pack itself is not fully "
                "recovered beyond the path/name evidence in this pass."
            ),
            problem="Unknown beyond census path-family evidence; not reconstructed.",
            inputs=[],
            outputs=[],
            dependencies=[],
            consumers=[],
            authority_role="",
            safety_role="",
            runtime_role="Absent path family",
            invariants=[],
            claims=[
                _open(
                    "evidence/market_dashboard_reset/pr_a is absent on current origin/main; "
                    "purpose text of that pack was not recovered in this pass.",
                    "docs/system_atlas/reconciliation/ledger.yaml",
                ),
            ],
            open_questions=[
                "What did the reset pack assert that the deletion pack (RCN-000013) did not?",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[],
            evidence_refs=["docs/system_atlas/reconciliation/ledger.yaml"],
            clusters=["landscape_dashboard"],
        ),
        understood(
            rid="RCN-000053",
            historical_purpose=(
                "Documentation tree under src/docs: Peak_Trade_OVERVIEW.md describes a "
                "modular trading-framework prototype (Kraken-spot backtesting, MA-crossover, "
                "backtest engine). Other files are contributing/setup/architecture notes."
            ),
            problem="Provide a project overview for new chats/machines (stated in OVERVIEW).",
            inputs=[],
            outputs=["Markdown documentation files under src/docs/"],
            dependencies=[],
            consumers=["Human/agent onboarding (stated)"],
            authority_role="Documentation; not declared canonical SSOT in recovered header",
            safety_role="Live-trading-bot described as not part of then-current MVP",
            runtime_role="Docs misplaced under src/; not executable runtime",
            invariants=[],
            claims=[
                _raw(
                    "Peak_Trade_OVERVIEW.md: modular Trading-Framework-Prototyp with "
                    "Kraken-Spot backtesting and MA-crossover; live bot not part of MVP.",
                    "src/docs/Peak_Trade_OVERVIEW.md",
                ),
                _open(
                    "POSSIBLE_SAME_AS docs/00_overview (RCN-000049) remains hypothesis; "
                    "path families are not fused.",
                    "docs/system_atlas/reconciliation/relations.yaml",
                ),
            ],
            open_questions=[
                "Whether src/docs was an accidental copy of docs/00_overview is unproven.",
            ],
            extra_relations=[],
            historical_blobs=[],
            historical_commits=[],
            evidence_refs=["src/docs/Peak_Trade_OVERVIEW.md"],
            clusters=["archives_legacy"],
        ),
    ]


# RCN-000047 marked PURPOSE_UNDERSTOOD above but purpose is NOT proven - I should
# change it to PARTIAL. The understood() helper forces purpose_understood True.
# I'll override in persist for 047 OR fix here: remove 047 from purpose_understood
# and handle as partial in persist.

PARTIAL_OVERRIDES = {
    "RCN-000047": {
        "understand_status": "UNDERSTAND_PARTIAL",
        "purpose_understood": False,
        "historical_purpose": "",
        "epistemic_class": "OPEN_QUESTION",
    }
}


def clusters_payload() -> list[dict[str, Any]]:
    return [
        {
            "cluster_id": "landscape_dashboard",
            "cluster_kind": "NAVIGATION_ONLY",
            "identity_group": False,
            "description": (
                "Market dashboard / Landscape-named historical records. Not one identity. "
                "Includes Runbooks Landscape index because of the shared token only."
            ),
            "record_ids": list(LANDSCAPE_CLUSTER_IDS),
        },
        {
            "cluster_id": "master_v2_double_play",
            "cluster_kind": "NAVIGATION_ONLY",
            "identity_group": False,
            "description": "Master V2 / Double Play packages, ops scaffold, forensic indexes, selector, JSON route.",
            "record_ids": list(MASTER_V2_CLUSTER_IDS),
        },
        {
            "cluster_id": "governance_gates",
            "cluster_kind": "NAVIGATION_ONLY",
            "identity_group": False,
            "description": "Runbook indexes, superseded Vollautonomie runbook, selector policy.",
            "record_ids": ["RCN-000003", "RCN-000015", "RCN-000016"],
        },
        {
            "cluster_id": "data_market",
            "cluster_kind": "NAVIGATION_ONLY",
            "identity_group": False,
            "description": "Historical market depth/tape/OHLCV dashboard readmodels.",
            "record_ids": ["RCN-000027", "RCN-000028", "RCN-000030"],
        },
        {
            "cluster_id": "archives_legacy",
            "cluster_kind": "NAVIGATION_ONLY",
            "identity_group": False,
            "description": "Forensic reference tree, corpus persistence base, src/docs.",
            "record_ids": ["RCN-000007", "RCN-000008", "RCN-000017", "RCN-000022", "RCN-000053"],
        },
    ]
