"""REEVALUATE_OPEN_RECORDS_PASS_V1 payloads. Re-evaluate/adjudicate OPEN records only.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Does not reintegrate, fuse identities, or mutate runtime.
UNDERSTAND / EVALUATE / INTEGRATE_OR_DISPOSITION / OPEN_EVIDENCE_RESOLUTION
snapshots remain frozen.
"""

from __future__ import annotations

from typing import Any

from scripts.ops.system_atlas_v1.evidence_resolution_pass_v1_records import (
    EVIDENCE_RESOLUTION_BOUND_SHA,
    LANDSCAPE_V1_IDS,
    OPEN_IDS,
)

REEVALUATE_PASS_ID = "REEVALUATE_OPEN_RECORDS_PASS_V1"
REEVALUATE_BOUND_REF = "origin/main"
REEVALUATE_BOUND_SHA = "f9618c73f1834b68588ceab586da4d6408962a10"
INPUT_PASS_ID = "OPEN_EVIDENCE_RESOLUTION_PASS_V1"
ADJUDICATE_FROZEN_SHA = "64aa353073ae7971a966e2f7a1e2a8d3e3c9e6d2"

RETAIN = "RETAIN_AS_IS"
ADAPT = "ADAPT_AND_REINTEGRATE"
COVERED = "CAPABILITY_ALREADY_COVERED"
INCOMPATIBLE = "HISTORICALLY_VALID_BUT_INCOMPATIBLE"
REJECT = "REJECT_FOR_CURRENT_SYSTEM"
INSUFFICIENT = "INSUFFICIENT_EVIDENCE"

ER_REC = "docs/system_atlas/reconciliation/evidence_resolution/records"
ER_STATUS = "docs/system_atlas/reconciliation/evidence_resolution/pass_v1_status.yaml"
OWNER_REG = "src/webui/market_dashboard_landscape_v2/owner_registry.py"
CAP23 = "src/ops/single_selected_future_policy_v1/constants_v1.py"
KS_PKG = "src/risk_layer/kill_switch/__init__.py"
RISK_GATE = "src/risk_layer/risk_gate.py"
HUB = "docs/webui/observability/OBSERVABILITY_HUB_V0.md"
LEDGER = "docs/system_atlas/reconciliation/ledger.yaml"


def _claim(cls: str, text: str, evidence: list[str], *, used_as_fact: bool) -> dict[str, Any]:
    return {
        "claim_class": cls,
        "text": text,
        "evidence": list(evidence),
        "used_as_fact": used_as_fact,
    }


def _er(rid: str) -> str:
    return f"{ER_REC}/{rid}.yaml"


def _understand(rid: str) -> str:
    return f"docs/system_atlas/reconciliation/understand/records/{rid}.yaml"


def _evaluate(rid: str) -> str:
    return f"docs/system_atlas/reconciliation/evaluate/records/{rid}.yaml"


def _adjudicate(rid: str) -> str:
    return f"docs/system_atlas/reconciliation/adjudicate/records/{rid}.yaml"


def _open_row(
    record_id: str,
    *,
    current_evidence_set: list[str],
    historical_function: str,
    historical_relations: str,
    current_system_analogues: str,
    identity_status: str,
    successor_status: str,
    replacement_status: str,
    current_value_status: str,
    current_compatibility_status: str,
    contradictions: list[str],
    unresolved_gaps: list[str],
    evaluation_result: str,
    alternatives_rejected: list[str],
    claims: list[dict[str, Any]],
    extra_refs: list[str] | None = None,
) -> dict[str, Any]:
    if record_id not in OPEN_IDS:
        raise ValueError(f"not_an_open_input_record:{record_id}")
    refs = [
        _understand(record_id),
        _evaluate(record_id),
        _adjudicate(record_id),
        _er(record_id),
        ER_STATUS,
    ]
    if extra_refs:
        refs.extend(extra_refs)
    seen: set[str] = set()
    unique_refs: list[str] = []
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        unique_refs.append(ref)
    refs = unique_refs
    return {
        "record_id": record_id,
        "reevaluate_pass_id": REEVALUATE_PASS_ID,
        "input_pass_id": INPUT_PASS_ID,
        "reevaluation_attempted": True,
        "adjudication_attempted": True,
        "disposition_burden_met": False,
        "disposition_candidate": INSUFFICIENT,
        "disposition": INSUFFICIENT,
        "lifecycle_state": "OPEN",
        "final_disposition_change_performed": False,
        "identity_merge_performed": False,
        "reintegration_performed": False,
        "reintegration_candidate": False,
        "runtime_mutation_performed": False,
        "further_evidence_required": True,
        "current_evidence_set": list(current_evidence_set),
        "historical_function": historical_function,
        "historical_relations": historical_relations,
        "current_system_analogues": current_system_analogues,
        "identity_status": identity_status,
        "successor_status": successor_status,
        "replacement_status": replacement_status,
        "current_value_status": current_value_status,
        "current_compatibility_status": current_compatibility_status,
        "contradictions": list(contradictions),
        "unresolved_gaps": list(unresolved_gaps),
        "evaluation_result": evaluation_result,
        "alternatives_rejected": list(alternatives_rejected),
        "claims": list(claims),
        "evidence_refs": refs,
        "bound_against_ref": REEVALUATE_BOUND_REF,
        "bound_against_sha": REEVALUATE_BOUND_SHA,
        "input_pass_bound_sha": EVIDENCE_RESOLUTION_BOUND_SHA,
        "adjudicate_frozen_sha": ADJUDICATE_FROZEN_SHA,
    }


_LANDSCAPE_REJECTED = [
    f"{RETAIN}: historical path is CURRENTLY_ABSENT; same-identity current artifact is not proven",
    f"{COVERED}: GET /market overlap and Landscape V2 owner_registry slots are not proven replacement of this artifact's unique purpose",
    f"{ADAPT}: independent current value versus Landscape V2 is unproven; reintegration is not authorized",
    f"{INCOMPATIBLE}: no proven current Master-V2/Double-Play/Safety invariant incompatibility for this artifact",
    f"{REJECT}: deletion, absence, and historical 'kein Rebuild autorisiert' are not a positive current rejection reason",
    "Identity fusion with RCN-000001 or sibling v1 records: forbidden without SAME_AS proof",
]


def _landscape(
    record_id: str,
    *,
    artifact: str,
    historical_function: str,
    historical_relations: str,
    analogue: str,
    extra_gaps: list[str] | None = None,
    extra_refs: list[str] | None = None,
) -> dict[str, Any]:
    gaps = [
        "Unique purpose coverage by a specific Landscape V2 slot remains unproven.",
        "GET /market consumer overlap is not identity and not replacement.",
    ]
    if extra_gaps:
        gaps.extend(extra_gaps)
    return _open_row(
        record_id,
        current_evidence_set=[
            _er(record_id),
            _evaluate(record_id),
            _adjudicate(record_id),
            OWNER_REG,
        ],
        historical_function=historical_function,
        historical_relations=historical_relations,
        current_system_analogues=analogue,
        identity_status="PROVEN_DISTINCT_FROM_LANDSCAPE_V2_NOT_SAME_AS_SIBLINGS",
        successor_status="NOT_PROVEN",
        replacement_status="NOT_PROVEN",
        current_value_status="UNPROVEN",
        current_compatibility_status="UNPROVEN_NOT_RETAINABLE_WHILE_ABSENT",
        contradictions=[],
        unresolved_gaps=gaps,
        evaluation_result=(
            f"{artifact}: INPUT_PASS proved distinctness from Landscape V2, co-deletion in "
            "b5b81728, and internal v1 relations where attested. That does not meet RETAIN "
            "(absent), COVERED (endpoint/slot similarity forbidden as sole proof), ADAPT "
            "(unique current value unproven), INCOMPATIBLE (no current invariant proof), or "
            "REJECT (absence/deletion/no-rebuild are not positive reject grounds). "
            "INSUFFICIENT_EVIDENCE remains OPEN."
        ),
        alternatives_rejected=_LANDSCAPE_REJECTED,
        claims=[
            _claim(
                "ADJUDICATED_CONCLUSION",
                f"{artifact}: evidence after OPEN_EVIDENCE_RESOLUTION_PASS_V1 still does not "
                "meet the burden of a stronger terminal class. INSUFFICIENT_EVIDENCE remains "
                "OPEN and is not a rejection.",
                [_er(record_id), _evaluate(record_id), OWNER_REG],
                used_as_fact=True,
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "INPUT_PASS: Landscape V2 was added 82f71bbe after v1 stack deletion b5b81728; "
                "GET /market overlap is not identity.",
                [_er(record_id), OWNER_REG],
                used_as_fact=True,
            ),
            _claim(
                "HYPOTHESIS",
                "A later slot-level coverage proof might support COVERED or ADAPT; it is not proven here.",
                [OWNER_REG],
                used_as_fact=False,
            ),
        ],
        extra_refs=[OWNER_REG, *(extra_refs or [])],
    )


def _absent_unproven(
    record_id: str,
    *,
    artifact: str,
    historical_function: str,
    historical_relations: str,
    analogue: str,
    identity_status: str,
    gaps: list[str],
    rejected: list[str],
    extra_refs: list[str] | None = None,
    extra_claims: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    claims = [
        _claim(
            "ADJUDICATED_CONCLUSION",
            f"{artifact}: after OPEN_EVIDENCE_RESOLUTION_PASS_V1 the burden for a stronger "
            "terminal class is not met. INSUFFICIENT_EVIDENCE remains OPEN.",
            [_er(record_id), _evaluate(record_id)],
            used_as_fact=True,
        ),
        _claim(
            "FORENSIC_RAW_FACT",
            "Current absence, later namesakes, and never-merged-to-origin/main presence are "
            "not identity, not replacement, and not rejection.",
            [_er(record_id)],
            used_as_fact=True,
        ),
    ]
    if extra_claims:
        claims.extend(extra_claims)
    return _open_row(
        record_id,
        current_evidence_set=[_er(record_id), _evaluate(record_id), _adjudicate(record_id)],
        historical_function=historical_function,
        historical_relations=historical_relations,
        current_system_analogues=analogue,
        identity_status=identity_status,
        successor_status="NOT_PROVEN",
        replacement_status="NOT_PROVEN",
        current_value_status="UNPROVEN",
        current_compatibility_status="UNPROVEN",
        contradictions=[],
        unresolved_gaps=gaps,
        evaluation_result=(
            f"{artifact}: historical function is understood at UNDERSTAND/INPUT_PASS level, but "
            "current same-identity presence, proven replacement, unique current value, proven "
            "incompatibility, and positive reject reason are not all (or any stronger class) "
            "satisfied. INSUFFICIENT_EVIDENCE remains OPEN."
        ),
        alternatives_rejected=rejected,
        claims=claims,
        extra_refs=extra_refs,
    )


def reevaluate_open_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = [
        _landscape(
            "RCN-000009",
            artifact="product_surface_v1",
            historical_function=(
                "Read-only GET /market presenter path: source loader → aggregate → presenter → template."
            ),
            historical_relations="IMPORTS RCN-000010/029/030 at 987e020; co-deleted in b5b81728. Not SAME_AS V2.",
            analogue="Landscape V2 GET /market shell + owner_registry (RCN-000001, RETAIN) is a later distinct consumer.",
        ),
        _landscape(
            "RCN-000010",
            artifact="readmodels_v1",
            historical_function="v1 page snapshot aggregate/contracts/adapters consumed by product_surface_v1.",
            historical_relations="IMPORTED_BY RCN-000009; separate package; co-deleted in b5b81728.",
            analogue="Landscape V2 owner_registry maps slots to canonical producers, not readmodels_v1.",
        ),
        _landscape(
            "RCN-000011",
            artifact="market_visual_operator_surface_v1",
            historical_function="v1 visual operator chrome/display modules.",
            historical_relations="Co-deleted in b5b81728; not fused with product_surface_v1 or V2.",
            analogue="No owner_registry slot is named market_visual_operator_surface_v1.",
        ),
        _landscape(
            "RCN-000012",
            artifact="futures_read_only_market_dashboard_runtime_v0",
            historical_function="SSR-only F5 GET /market/futures context, fail-closed by default.",
            historical_relations="Co-deleted in b5b81728. POSSIBLE_SAME_AS product_surface_v1 remains hypothesis.",
            analogue="Landscape V2 GET /market is not proven to be the F5 /market/futures runtime.",
        ),
        _absent_unproven(
            "RCN-000014",
            artifact="archive/PeakTradeRepo",
            historical_function="Nested historical PeakTradeRepo archive tree; inner blobs split as 044/045/046.",
            historical_relations="Co-deleted with other archive/* on origin/main by 75722feea. Not fused with inner records.",
            analogue="No proven current equivalent of the nested archive tree.",
            identity_status="IDENTITY_UNPROVEN",
            gaps=[
                "Which recovered inner blobs represent the claimed stack remains open.",
                "Fuller pre-placeholder snapshot is not reconstructed.",
            ],
            rejected=[
                f"{RETAIN}: path CURRENTLY_ABSENT",
                f"{COVERED}: later namesakes are not proven SAME_AS the archive tree",
                f"{ADAPT}: unique current value unproven",
                f"{INCOMPATIBLE}: no current invariant incompatibility proven",
                f"{REJECT}: archive deletion is not a positive reject reason",
            ],
            extra_refs=[
                "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml"
            ],
        ),
        _rcn_000015(),
        _rcn_000019(),
        _absent_unproven(
            "RCN-000020",
            artifact="docs/observability Grafana family",
            historical_function="Grafana/Prometheus observability runbook family.",
            historical_relations=(
                "Purged on origin/main by 1c71a4eab. POSSIBLE_SAME_AS docs/webui/observability "
                "(RCN-000052) and later src/obs remain hypothesis."
            ),
            analogue="src/obs and src/observability exist; Grafana-runbook identity unproven.",
            identity_status="IDENTITY_UNPROVEN",
            gaps=["Current Grafana/OTLP runbook same-identity is unproven."],
            rejected=[
                f"{RETAIN}: path CURRENTLY_ABSENT on origin/main",
                f"{COVERED}: later src/obs is not proven Grafana-runbook replacement",
                f"{ADAPT}: unique current Grafana-stack value unproven",
                f"{INCOMPATIBLE}: security purge of artifacts is not proven incompatibility of observability purpose",
                f"{REJECT}: purge/absence is not by itself a positive reject of the observability purpose",
            ],
            extra_refs=[HUB, _er("RCN-000052")],
        ),
        _landscape(
            "RCN-000023",
            artifact="market_surface.py",
            historical_function="Canonical GET /market route owner binding PR-D product surface.",
            historical_relations="REFERENCES RCN-000029/031/030 as canonical owners at 987e020; co-deleted in b5b81728.",
            analogue="Current GET /market is market_dashboard_landscape_shell_router_v2.py. HTTP path reuse is not identity.",
            extra_refs=["src/webui/market_dashboard_landscape_shell_router_v2.py"],
        ),
        _landscape(
            "RCN-000027",
            artifact="market_depth v0",
            historical_function="Depth fixture read-model and GET /api/market/depth JSON.",
            historical_relations="Co-deleted in b5b81728. Not SAME_AS product_surface_v1.",
            analogue="No owner_registry slot is named market_depth.",
        ),
        _landscape(
            "RCN-000028",
            artifact="market_tape_readmodel_v0",
            historical_function="Market tape read-model v0.",
            historical_relations="Co-deleted in b5b81728. Standalone; not fused.",
            analogue="No owner_registry slot is named market_tape.",
        ),
        _landscape(
            "RCN-000029",
            artifact="market_ranking_funnel v0",
            historical_function="Ranking funnel readmodel/runtime for futures universe/ranking.",
            historical_relations="IMPORTED_BY RCN-000009; named ranking owner by RCN-000023.",
            analogue="V2 universe_ranking slot owner is universe_selection_readmodel.v1, not this package.",
        ),
        _landscape(
            "RCN-000030",
            artifact="market_futures_ohlcv v0",
            historical_function="Futures OHLCV readmodel/runtime v0 for the v1 chart path.",
            historical_relations="IMPORTED_BY RCN-000009; named OHLCV owner by RCN-000023.",
            analogue="V2 market_instrument notes bind OHLCV via okx_selected_instrument_ohlcv_readmodel.v1.",
        ),
        _landscape(
            "RCN-000031",
            artifact="market_instrument_eligibility_v0",
            historical_function="Instrument eligibility helper for the v1 market surface.",
            historical_relations="Named CANONICAL_ELIGIBILITY_OWNER by market_surface.py; co-deleted in b5b81728.",
            analogue="No owner_registry slot is this eligibility module.",
        ),
        _landscape(
            "RCN-000032",
            artifact="market_active_paper_run_runtime_v0",
            historical_function="Active paper-run runtime helper for the v1 dashboard.",
            historical_relations="Co-deleted in b5b81728. Relation to later paper-shadow runtimes unproven.",
            analogue="No owner_registry slot is this paper-run runtime.",
            extra_gaps=["Relation to paper-shadow runtimes remains unproven identity."],
        ),
        _landscape(
            "RCN-000033",
            artifact="market_dashboard_current_state v0",
            historical_function="Current-state snapshot/runtime v0 for the v1 dashboard.",
            historical_relations="Co-deleted in b5b81728. Not fused.",
            analogue="No owner_registry slot is this current-state runtime.",
        ),
        _landscape(
            "RCN-000034",
            artifact="deleted market dashboard product runbooks",
            historical_function="Product documentation of the v1 dashboard architecture/reset.",
            historical_relations="v1 docs deleted in b5b81728. Documentation-to-code SAME_AS remains hypothesis.",
            analogue="Landscape V2 docs (RCN-000002, RETAIN) are a later document set, not proven SAME_AS.",
        ),
        _landscape(
            "RCN-000035",
            artifact="Composition Landmark Master Runbook v1.3",
            historical_function="Composition landmark master runbook v1.3 for the dashboard product.",
            historical_relations="Distinct from Landscape V2 master runbook RCN-000002 unless proven SAME_AS.",
            analogue="RCN-000002 remains a separate RETAIN record; not fused.",
        ),
        _absent_unproven(
            "RCN-000036",
            artifact="archive/full_files_stand_02.12.2025",
            historical_function="Dated 2025-12-02 export tree.",
            historical_relations="Different tree from PeakTradeRepo; POSSIBLE_SAME_AS remains hypothesis.",
            analogue="No proven current equivalent.",
            identity_status="IDENTITY_UNPROVEN",
            gaps=["Same snapshot as archive/PeakTradeRepo remains unproven."],
            rejected=[
                f"{RETAIN}: CURRENTLY_ABSENT",
                f"{COVERED}: later namesake not proven",
                f"{ADAPT}: unique value unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: deletion is not reject",
            ],
        ),
        _absent_unproven(
            "RCN-000037",
            artifact="archive/legacy_docs",
            historical_function="Legacy docs archive (README.before_phase58.md attested).",
            historical_relations="Deleted with archive cleanup 75722feea.",
            analogue="No proven current equivalent of the full archive contents.",
            identity_status="IDENTITY_UNPROVEN",
            gaps=["Full inner listing beyond the README is not reconstructed."],
            rejected=[
                f"{RETAIN}: CURRENTLY_ABSENT",
                f"{COVERED}: not proven",
                f"{ADAPT}: unique value unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: deletion is not reject",
            ],
        ),
        _absent_unproven(
            "RCN-000038",
            artifact="archive/legacy_scripts/run_regime_experiments.sh",
            historical_function="Legacy regime-experiment shell script.",
            historical_relations="Relation to later regime-sweep scripts is unproven identity.",
            analogue="Later regime-sweep scripts are namesakes, not proven SAME_AS.",
            identity_status="IDENTITY_UNPROVEN",
            gaps=["Standalone tooling versus later regime sweep scripts remains unproven."],
            rejected=[
                f"{RETAIN}: CURRENTLY_ABSENT",
                f"{COVERED}: later scripts not proven replacement",
                f"{ADAPT}: unique value unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: deletion is not reject",
            ],
        ),
        _absent_unproven(
            "RCN-000039",
            artifact="src/infra/health",
            historical_function="Central HealthChecker ampel GREEN/YELLOW/RED; never merged to origin/main.",
            historical_relations="Commit 781713e9 is not an ancestor of origin/main.",
            analogue=(
                "kill_switch/health_check.py HealthChecker and core.resilience HealthCheck are "
                "namesakes, not proven SAME_AS."
            ),
            identity_status="PROVEN_HISTORICAL_EXISTENCE_ON_NON_MAIN_COMMIT",
            gaps=["Blob identity versus kill_switch/health_check.py is unproven."],
            rejected=[
                f"{RETAIN}: CURRENTLY_ABSENT on origin/main",
                f"{COVERED}: namesake HealthChecker is not proven identity",
                f"{ADAPT}: unique value unproven",
                f"{INCOMPATIBLE}: never-merged is not incompatibility",
                f"{REJECT}: never-merged/absent is not reject",
            ],
            extra_refs=["src/risk_layer/kill_switch/health_check.py", "src/core/resilience.py"],
        ),
        _absent_unproven(
            "RCN-000040",
            artifact="src/infra/backup",
            historical_function="Historical backup package on never-merged commit 12188014.",
            historical_relations="Bundled with resilience/monitoring on that commit; not on origin/main.",
            analogue="No src/infra/backup on origin/main. Disaster-recovery docs are not proven SAME_AS.",
            identity_status="PROVEN_HISTORICAL_EXISTENCE_ON_NON_MAIN_COMMIT",
            gaps=["Later backup/recovery owner same-identity is unproven."],
            rejected=[
                f"{RETAIN}: CURRENTLY_ABSENT",
                f"{COVERED}: later DR docs/scripts not proven replacement",
                f"{ADAPT}: unique value unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: never-merged/absent is not reject",
            ],
        ),
        _absent_unproven(
            "RCN-000041",
            artifact="src/infra/monitoring",
            historical_function="Historical monitoring package on never-merged commit 12188014.",
            historical_relations="Thematic proximity to RCN-000020 and src/obs is not identity.",
            analogue="src/obs, src/observability, risk_layer.alerting exist; successor unproven.",
            identity_status="PROVEN_HISTORICAL_EXISTENCE_ON_NON_MAIN_COMMIT",
            gaps=["Is risk_layer.alerting or src/obs a successor? Unproven."],
            rejected=[
                f"{RETAIN}: CURRENTLY_ABSENT",
                f"{COVERED}: later obs packages not proven SAME_AS",
                f"{ADAPT}: unique value unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: never-merged/absent is not reject",
            ],
            extra_refs=["src/risk_layer/alerting/__init__.py"],
        ),
        _absent_unproven(
            "RCN-000042",
            artifact="src/infra/resilience",
            historical_function="circuit_breaker/retry/fallback/rate_limiter package on never-merged 12188014.",
            historical_relations="src/core/resilience.py is a later origin/main module; blob SAME_AS unproven.",
            analogue="src/core/resilience.py (circuit breaker, retry, health_check) is a namesake module.",
            identity_status="PROVEN_HISTORICAL_EXISTENCE_ON_NON_MAIN_COMMIT",
            gaps=[
                "Blob-level SAME_AS to src/core/resilience.py is unproven; no origin/main rename."
            ],
            rejected=[
                f"{RETAIN}: CURRENTLY_ABSENT as src/infra/resilience",
                f"{COVERED}: similar circuit-breaker/retry behavior is not proven replacement without identity",
                f"{ADAPT}: unique uncovered value unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: never-merged/absent is not reject",
            ],
            extra_refs=["src/core/resilience.py"],
        ),
        _absent_unproven(
            "RCN-000043",
            artifact="pre_economic_zero_order observer/arming/evidence trio",
            historical_function="Wallclock arming, hypothetical zero-order economics, decision-cycle observer. Never orders.",
            historical_relations=(
                "Commit 00417f6ea is not an ancestor of origin/main. Current evidence_session_* "
                "modules share a campaign prefix, not proven SAME_AS."
            ),
            analogue="pre_economic_zero_order_evidence_session_* on origin/main; different capability id/filenames.",
            identity_status="PROVEN_HISTORICAL_EXISTENCE_ON_NON_MAIN_COMMIT",
            gaps=["Same family as later evidence_session modules is unproven identity."],
            rejected=[
                f"{RETAIN}: observer/arming trio CURRENTLY_ABSENT on origin/main",
                f"{COVERED}: evidence_session contract is not proven replacement of observer/arming trio",
                f"{ADAPT}: unique uncovered observer/arming semantics unproven",
                f"{INCOMPATIBLE}: none proven against current fail-closed zero-order gates",
                f"{REJECT}: never-merged/absent is not reject",
            ],
            extra_refs=["src/ops/pre_economic_zero_order_evidence_session_contract_v1.py"],
        ),
        _absent_unproven(
            "RCN-000044",
            artifact="PeakTradeRepo nested backtest engine",
            historical_function="Nested archive backtest engine/results/stats snapshot.",
            historical_relations="Inner component of RCN-000014; not fused. Deleted with archive.",
            analogue="Later src/backtest namesake is not proven SAME_AS.",
            identity_status="IDENTITY_UNPROVEN",
            gaps=["Placeholder vs implemented export engine remains unfused."],
            rejected=[
                f"{RETAIN}: CURRENTLY_ABSENT",
                f"{COVERED}: later src/backtest not proven SAME_AS",
                f"{ADAPT}: unique value unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: deletion is not reject",
            ],
        ),
        _absent_unproven(
            "RCN-000045",
            artifact="PeakTradeRepo nested position_sizer",
            historical_function="Nested archive position_sizer snapshot.",
            historical_relations="Inner component of RCN-000014; not fused.",
            analogue="Later sizer modules / position_sizer_old_backup are not proven SAME_AS.",
            identity_status="IDENTITY_UNPROVEN",
            gaps=["Identity versus later sizer modules remains unproven."],
            rejected=[
                f"{RETAIN}: CURRENTLY_ABSENT",
                f"{COVERED}: later sizers not proven replacement",
                f"{ADAPT}: unique value unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: deletion is not reject",
            ],
        ),
        _absent_unproven(
            "RCN-000046",
            artifact="PeakTradeRepo nested ma_crossover",
            historical_function="Nested archive ma_crossover strategy snapshot.",
            historical_relations="Inner component of RCN-000014; not fused.",
            analogue="Later ma_crossover implementations are not proven SAME_AS.",
            identity_status="IDENTITY_UNPROVEN",
            gaps=["Same strategy as later ma_crossover implementations remains unproven."],
            rejected=[
                f"{RETAIN}: CURRENTLY_ABSENT",
                f"{COVERED}: later implementations not proven SAME_AS",
                f"{ADAPT}: unique value unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: deletion is not reject",
            ],
        ),
        _landscape(
            "RCN-000047",
            artifact="evidence/market_dashboard_reset pack",
            historical_function="Reset-pack evidence for the v1 dashboard architecture reset, then deleted with the stack.",
            historical_relations=(
                "Different evidence event from still-present deletion pack RCN-000013 (RETAIN). "
                "POSSIBLE_SAME_AS remains hypothesis."
            ),
            analogue="RCN-000013 deletion pack remains; that is a different evidence event, not proven SAME_AS.",
            extra_refs=["evidence/market_dashboard_deletion/deletion_manifest.txt"],
            extra_gaps=[
                "What the reset pack asserted that the deletion pack did not remains open."
            ],
        ),
        _absent_unproven(
            "RCN-000048",
            artifact="docs/20_phases",
            historical_function="Numbered phase markdowns (e.g. Phase 16A ExecutionPipeline; LIVE blocked).",
            historical_relations=(
                "R100 docs/PHASE_* → docs/20_phases/PHASE_* on never-merged 42c3f443d. That rename "
                "is not into the Master Runbook."
            ),
            analogue="Master Runbook is current semantic authority; not proven relocated 20_phases corpus.",
            identity_status="PROVEN_PATH_FAMILY_ON_NON_MAIN_COMMIT_VIA_R100",
            gaps=["Path move versus later runbook locations is unproven identity on origin/main."],
            rejected=[
                f"{RETAIN}: docs/20_phases CURRENTLY_ABSENT on origin/main",
                f"{COVERED}: Master Runbook existence is not proven SAME_AS the 20_phases corpus",
                f"{ADAPT}: unique current value of phase markdowns unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: never-merged/absent is not reject",
            ],
            extra_refs=["docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md"],
        ),
        _absent_unproven(
            "RCN-000049",
            artifact="docs/00_overview",
            historical_function="Mixed: origin/main TODO-board add/delete; never-merged R100 overview moves.",
            historical_relations="POSSIBLE_SAME_AS src/docs RCN-000053 remains hypothesis. Two histories not fused.",
            analogue="src/docs/Peak_Trade_OVERVIEW.md exists (RCN-000053 RETAIN); relocation unproven.",
            identity_status="MIXED_TWO_PATH_HISTORIES_NOT_FUSED",
            gaps=[
                "Are current overview docs the relocated 00_overview family, or separately authored?"
            ],
            rejected=[
                f"{RETAIN}: docs/00_overview CURRENTLY_ABSENT",
                f"{COVERED}: src/docs overview is not proven SAME_AS this family",
                f"{ADAPT}: unique value unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: absence is not reject",
            ],
            extra_refs=["src/docs/Peak_Trade_OVERVIEW.md"],
        ),
        _absent_unproven(
            "RCN-000050",
            artifact="step29m v2 strategy/research family",
            historical_function=(
                "Offline-only diagnostic v2 wrappers keeping parent v1 as immutable negative baseline. "
                "Three STRATEGY_IDs remain distinct internally."
            ),
            historical_relations=(
                "Commit 34574e139 is not an ancestor of origin/main. Parent v1 modules still exist "
                "as declared baselines, not as the v2 wrappers."
            ),
            analogue="src/strategies/bollinger.py, momentum.py, trend_following.py; plus later step29m research adapters.",
            identity_status="PROVEN_HISTORICAL_EXISTENCE_ON_NON_MAIN_COMMIT",
            gaps=[
                "Did v2 wrappers retire into parent modules? Parent v1 is the declared immutable baseline, not proven retirement identity."
            ],
            rejected=[
                f"{RETAIN}: step29m v2 paths CURRENTLY_ABSENT on origin/main",
                f"{COVERED}: parent v1 modules are the baseline v2 said it would not mutate, not proven v2 replacement",
                f"{ADAPT}: unique current value of v2 wrappers unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: never-merged/absent is not reject",
                "Splitting the three STRATEGY_IDs is not performed; grouping remains path-prefix only",
            ],
            extra_refs=[
                "src/strategies/bollinger.py",
                "src/strategies/momentum.py",
                "src/strategies/trend_following.py",
            ],
        ),
        _absent_unproven(
            "RCN-000051",
            artifact="archive/noch_einordnen",
            historical_function="Staging archive with README; deleted 24001182d.",
            historical_relations="Text overlap with PeakTradeRepo README is not SAME_AS without blob proof.",
            analogue="No proven current equivalent.",
            identity_status="IDENTITY_UNPROVEN",
            gaps=["What was queued in this archive remains incompletely listed."],
            rejected=[
                f"{RETAIN}: CURRENTLY_ABSENT",
                f"{COVERED}: not proven",
                f"{ADAPT}: unique value unproven",
                f"{INCOMPATIBLE}: none proven",
                f"{REJECT}: deletion is not reject",
            ],
        ),
        _rcn_000052(),
    ]
    if len(rows) != 35:
        raise ValueError(f"reevaluate_count_mismatch:{len(rows)}")
    ids = [r["record_id"] for r in rows]
    if tuple(ids) != OPEN_IDS:
        raise ValueError(f"reevaluate_id_order_mismatch:{ids}")
    if any(r["disposition_burden_met"] is True for r in rows):
        raise ValueError("unexpected_burden_met")
    if any(r["disposition"] != INSUFFICIENT for r in rows):
        raise ValueError("unexpected_non_open_disposition")
    return rows


def _rcn_000015() -> dict[str, Any]:
    return _open_row(
        "RCN-000015",
        current_evidence_set=[_er("RCN-000015"), CAP23, _evaluate("RCN-000015")],
        historical_function=(
            "Census → structural eligibility → exactly-one-or-none; ranking is not selection "
            "authority; fail-closed if eligible_count != 1."
        ),
        historical_relations=(
            "Selector constants explicitly do not rewrite Cap 2.3. Cap 2.3 (ecb44849 2026-08-02) "
            "predates selector #6165/#6166 (2026-08-30). Succession selector→Cap 2.3 is refuted."
        ),
        current_system_analogues=(
            "Cap 2.3 single_selected_future_policy_v1 is current selection owner: ranking, "
            "hysteresis, min holding, SELECTION_AUTHORITY_ADDED=true."
        ),
        identity_status="PROVEN_DISTINCT_FROM_CAP_2_3",
        successor_status="REFUTED_AS_SUCCESSOR_OF_SELECTOR",
        replacement_status="NOT_PROVEN",
        current_value_status="UNPROVEN",
        current_compatibility_status=(
            "UNPROVEN: hypothetical wiring as a second selection authority is not a proven "
            "current invariant violation of the dormant historical package"
        ),
        contradictions=[],
        unresolved_gaps=[
            "Why was #6165 reverted, beyond the revert pointer in #6166?",
            "Unique current value of fail-closed-unless-exactly-one versus Cap 2.3 ranking selection remains unproven.",
        ],
        evaluation_result=(
            "INPUT_PASS proved the selector is a distinct Owner policy that does not rewrite "
            "Cap 2.3 and cannot be Cap 2.3's successor (Cap 2.3 predates it). Different "
            "selection semantics are not functional coverage. Revert is not REJECT. Unique "
            "current value is unproven, so ADAPT burden is unmet. Hypothetical co-authority "
            "conflict is not a proven INCOMPATIBLE invariant. INSUFFICIENT_EVIDENCE remains OPEN."
        ),
        alternatives_rejected=[
            f"{RETAIN}: selector path CURRENTLY_ABSENT after revert",
            f"{COVERED}: Cap 2.3 ranking/hysteresis selection does not provenly fulfill fail-closed-unless-exactly-one; later code is not coverage",
            f"{ADAPT}: independent current value versus Cap 2.3 is unproven; this label would not authorize implementation",
            f"{INCOMPATIBLE}: no proven current invariant that the dormant package itself violates; hypothetical wiring conflict is not used",
            f"{REJECT}: revert #6166 is not a positive rejection reason",
            "Declaring SAME_AS / successor of single_selected_future_policy_v1: refuted, not a merge",
        ],
        claims=[
            _claim(
                "ADJUDICATED_CONCLUSION",
                "Master V2 minimal selector: stronger terminal class burden is not met after "
                "INPUT_PASS. INSUFFICIENT_EVIDENCE remains OPEN.",
                [_er("RCN-000015"), CAP23],
                used_as_fact=True,
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "Selector does not rewrite Cap 2.3; Cap 2.3 predates the selector; succession is refuted.",
                [_er("RCN-000015"), CAP23],
                used_as_fact=True,
            ),
            _claim(
                "CANONICAL_CURRENT_FACT",
                "Cap 2.3 remains current SINGLE_SELECTED_FUTURE selection owner with ranking provenance.",
                [CAP23],
                used_as_fact=True,
            ),
            _claim(
                "OPEN_QUESTION",
                "Semantic cause of revert #6166 beyond the revert pointer remains unproven.",
                [_er("RCN-000015")],
                used_as_fact=False,
            ),
        ],
        extra_refs=[CAP23, "src/ops/single_selected_future_policy_v1/selection_v1.py"],
    )


def _rcn_000019() -> dict[str, Any]:
    return _open_row(
        "RCN-000019",
        current_evidence_set=[_er("RCN-000019"), KS_PKG, RISK_GATE],
        historical_function=(
            "Bundled historical top-level modules: KillSwitchLayer, LiquidityGate, StressGate, "
            "VaRGate, RiskMetrics, MicrostructureMetrics."
        ),
        historical_relations=(
            "kill_switch.py and kill_switch/ package coexisted at 14d58ec3 with different blobs/"
            "classes; no rename. Gates deleted in f83442953. Record remains a bundle, not fused."
        ),
        current_system_analogues=(
            "src/risk_layer/kill_switch/ package present; risk_gate.py skeleton without "
            "Liquidity/Stress/VaR imports."
        ),
        identity_status="PARTIAL_FAMILY_IDENTITY_UNPROVEN",
        successor_status="NOT_PROVEN_FOR_GATES",
        replacement_status="NOT_PROVEN_FOR_GATES",
        current_value_status="UNPROVEN",
        current_compatibility_status="UNPROVEN_AT_BUNDLE_LEVEL",
        contradictions=[],
        unresolved_gaps=[
            "Are LiquidityGate/StressGate/VaRGate purposes covered anywhere other than the skeleton docstring?",
            "Bundle-level stronger class would conflate present package with absent modules.",
        ],
        evaluation_result=(
            "INPUT_PASS proved kill_switch.py ≠ kill_switch/ package and that deleted gates are "
            "not implemented by current risk_gate.py. CAPABILITY_ALREADY_COVERED is therefore "
            "unmet for the bundled record. RETAIN of the whole family is unmet (missing modules). "
            "ADAPT unique value of missing gates is unproven. Absence is not REJECT. "
            "INSUFFICIENT_EVIDENCE remains OPEN. No identity merge or split performed."
        ),
        alternatives_rejected=[
            f"{RETAIN}: missing historical modules are not present as those artifacts",
            f"{COVERED}: kill_switch package does not prove Liquidity/Stress/VaR identity or coverage; skeleton risk_gate.py has no those imports",
            f"{ADAPT}: unique current value of missing gates versus skeleton is unproven",
            f"{INCOMPATIBLE}: no proven current invariant that the historical gate purposes themselves violate",
            f"{REJECT}: deletion/absence is not a positive reject reason",
            "Normalizing KillSwitch package as the whole historical top-level family: forbidden",
        ],
        claims=[
            _claim(
                "ADJUDICATED_CONCLUSION",
                "risk_layer historical top-level modules: stronger class burden unmet at bundle "
                "level. INSUFFICIENT_EVIDENCE remains OPEN.",
                [_er("RCN-000019"), KS_PKG, RISK_GATE],
                used_as_fact=True,
            ),
            _claim(
                "CANONICAL_CURRENT_FACT",
                "Current risk_gate.py is a skeleton importing KillSwitch package; it does not "
                "import liquidity_gate, stress_gate, or var_gate.",
                [RISK_GATE, KS_PKG],
                used_as_fact=True,
            ),
            _claim(
                "HYPOTHESIS",
                "A later split of the bundle into per-module records might allow differentiated "
                "adjudication; splitting is not performed here.",
                [_er("RCN-000019")],
                used_as_fact=False,
            ),
        ],
        extra_refs=[KS_PKG, RISK_GATE, "src/risk_layer/kill_switch/core.py"],
    )


def _rcn_000052() -> dict[str, Any]:
    return _open_row(
        "RCN-000052",
        current_evidence_set=[_er("RCN-000052"), LEDGER, HUB],
        historical_function="Observability Hub v0 read-only HTML plus Paper/Shadow contracts.",
        historical_relations=(
            "Census CURRENTLY_ABSENT vs tree present at census SHA 1b52df25 (11 files) and "
            "origin/main. Post-census restore hypothesis refuted. POSSIBLE_SAME_AS Grafana "
            "RCN-000020 remains hypothesis."
        ),
        current_system_analogues="docs/webui/observability/OBSERVABILITY_HUB_V0.md exists on origin/main.",
        identity_status="CENSUS_TREE_CONTRADICTION",
        successor_status="NOT_APPLICABLE",
        replacement_status="NOT_PROVEN",
        current_value_status="UNPROVEN_WHILE_PRESENCE_CONTRADICTED",
        current_compatibility_status="CONTRADICTION_BLOCKS_PRESENCE_NORMALIZATION",
        contradictions=[
            "Census discovery.current_presence=CURRENTLY_ABSENT while git ls-tree census SHA "
            "1b52df25 and origin/main f9618c73 both contain docs/webui/observability/ (11 files).",
        ],
        unresolved_gaps=[
            "Why did FIND_COMPLETELY bind current_presence=CURRENTLY_ABSENT for a path present on the census SHA?",
            "POSSIBLE_SAME_AS Grafana docs/observability RCN-000020 remains hypothesis.",
        ],
        evaluation_result=(
            "Fail-closed: the census/tree contradiction is preserved and not semantically "
            "resolved. RETAIN_AS_IS from tree presence would silently overwrite "
            "CURRENTLY_ABSENT. COVERED would assume present hub docs are the census-deleted "
            "family. Presence is not rewritten. INSUFFICIENT_EVIDENCE remains OPEN."
        ),
        alternatives_rejected=[
            f"{RETAIN}: would normalize census CURRENTLY_ABSENT into a currently retained identity",
            f"{COVERED}: present hub docs are not proven identical to the census-deleted family",
            f"{ADAPT}: contradiction blocks treating the census identity as an adaptation candidate",
            f"{INCOMPATIBLE}: tree presence is not incompatibility",
            f"{REJECT}: census said deleted is not a positive reject reason",
            "Rewriting discovery.current_presence: forbidden; census field is historical discovery fact",
        ],
        claims=[
            _claim(
                "ADJUDICATED_CONCLUSION",
                "docs/webui/observability: contradiction unresolved; stronger class burden unmet. "
                "INSUFFICIENT_EVIDENCE remains OPEN.",
                [_er("RCN-000052"), LEDGER, HUB],
                used_as_fact=True,
            ),
            _claim(
                "CONTRADICTION",
                "Ledger discovery.current_presence is CURRENTLY_ABSENT while census SHA and "
                "current origin/main both contain the family. Census field is not rewritten.",
                [LEDGER, HUB, _er("RCN-000052")],
                used_as_fact=False,
            ),
            _claim(
                "CANONICAL_CURRENT_FACT",
                "docs/webui/observability/OBSERVABILITY_HUB_V0.md exists on origin/main@f9618c73.",
                [HUB],
                used_as_fact=True,
            ),
        ],
        extra_refs=[
            LEDGER,
            HUB,
            "docs/system_atlas/reconciliation/evidence/evidence_resolution_v1/commands/rcn_000052_census_tree.txt",
        ],
    )


def landscape_v1_ids() -> tuple[str, ...]:
    return LANDSCAPE_V1_IDS
