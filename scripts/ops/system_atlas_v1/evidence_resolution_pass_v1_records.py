"""OPEN_EVIDENCE_RESOLUTION_PASS_V1 payloads. Evidence resolution only.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Does not change disposition, fuse identities, reintegrate, or mutate runtime.
UNDERSTAND / EVALUATE / INTEGRATE_OR_DISPOSITION snapshots remain frozen.
"""

from __future__ import annotations

from typing import Any

EVIDENCE_RESOLUTION_PASS_ID = "OPEN_EVIDENCE_RESOLUTION_PASS_V1"
EVIDENCE_RESOLUTION_BOUND_REF = "origin/main"
EVIDENCE_RESOLUTION_BOUND_SHA = "f9618c73f1834b68588ceab586da4d6408962a10"
CENSUS_BOUND_SHA = "1b52df25b99a36b99eed91943c2a203ce84f1cad"
ADJUDICATE_FROZEN_SHA = "64aa353073ae7971a966e2f7a1e2a8d3e3c9e6d2"
EVALUATE_FROZEN_SHA = "0e6cbb860f716d527873d97556d0968df4a197bf"
UNDERSTAND_FROZEN_SHA = "a70bed0dc1586bedb58642fe7f6c6fef760b2478"

STACK_DELETE_SHA = "b5b8172806eae55d8639f964fcb2ad036337a0f3"
STACK_PARENT_SHA = "987e020378d1767fbd6fb1f0914d475f9a485f51"
LANDSCAPE_V2_ADD_SHA = "82f71bbef835e6a63453190b5eb1e3d4c2ef1884"
SELECTOR_ADD_SHA = "75eee7bdc501ab4b0ec93812675cd074acb9e2ee"
SELECTOR_REVERT_SHA = "afbae518b67eb1b789c835e219db37f5b15f308b"
CAP23_ADD_SHA = "ecb4484936b6079f90bde252abef77ff129aea8f"
RISK_DELETE_SHA = "f834429531cef0a6e9897c30fc792620d4f8dffa"
KS_PACKAGE_ADD_SHA = "14d58ec3b9d7acac26720d1aa4cf5ce46acfb725"
KS_PY_PARENT_SHA = "6e1ce02727f1719f8a9a5d1f001bb3e0c59411c7"
DOC_TIDY_SHA = "42c3f443d84c4f27110083c86d0c99db61a022ed"
INFRA_HEALTH_SHA = "781713e9b2304733c399979273c588fec8cc7eab"
INFRA_BUNDLE_SHA = "12188014cb93a78555bbdf5cbaaf60906f6755a5"
PRE_ECON_SHA = "00417f6ea5b6a79732b5a96fc132f158436a56a9"
STEP29M_SHA = "34574e1392af7bbfab20ce87854ee47bf5fbbe76"
NOCH_EINORDNEN_DEL_SHA = "24001182de0209dabac4d6296bc7738eec442107"
ARCHIVE_DELETE_SHA = "75722feea8c342c56ef93f796983467f33f98f25"
GRAFANA_PURGE_SHA = "1c71a4eab503b2b4d06fb310a1b85b9a127e8495"

RESOLVED = "EVIDENCE_GAP_RESOLVED"
PARTIAL = "EVIDENCE_GAP_PARTIALLY_RESOLVED"
UNRESOLVED = "EVIDENCE_GAP_UNRESOLVED"
CONTRADICTION = "CONTRADICTION_DISCOVERED"

ALLOWED_RESOLUTION_STATUSES = frozenset({RESOLVED, PARTIAL, UNRESOLVED, CONTRADICTION})

OPEN_IDS = (
    "RCN-000009",
    "RCN-000010",
    "RCN-000011",
    "RCN-000012",
    "RCN-000014",
    "RCN-000015",
    "RCN-000019",
    "RCN-000020",
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
    "RCN-000036",
    "RCN-000037",
    "RCN-000038",
    "RCN-000039",
    "RCN-000040",
    "RCN-000041",
    "RCN-000042",
    "RCN-000043",
    "RCN-000044",
    "RCN-000045",
    "RCN-000046",
    "RCN-000047",
    "RCN-000048",
    "RCN-000049",
    "RCN-000050",
    "RCN-000051",
    "RCN-000052",
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

QUOTES_REL = "docs/system_atlas/reconciliation/evidence/evidence_resolution_v1/raw_quotes.yaml"
COMMANDS_REL = (
    "docs/system_atlas/reconciliation/evidence/evidence_resolution_v1/commands/presence_matrix.txt"
)
IMPORTS_REL = (
    "docs/system_atlas/reconciliation/evidence/evidence_resolution_v1/commands/"
    "landscape_v1_import_edges.txt"
)
OWNER_REG = "src/webui/market_dashboard_landscape_v2/owner_registry.py"


def _claim(
    cls: str,
    text: str,
    evidence: list[str],
    *,
    used_as_fact: bool,
    source_sha: str = "",
    source_path: str = "",
    evidence_type: str = "",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "claim_class": cls,
        "text": text,
        "evidence": list(evidence),
        "used_as_fact": used_as_fact,
    }
    if source_sha:
        row["source_sha"] = source_sha
    if source_path:
        row["source_path"] = source_path
    if evidence_type:
        row["evidence_type"] = evidence_type
    return row


def _gap(
    *,
    status: str,
    statement: str,
    used_as_fact: bool,
    source: str,
    source_sha: str,
    evidence_type: str,
) -> dict[str, Any]:
    return {
        "status": status,
        "statement": statement,
        "used_as_fact": used_as_fact,
        "source": source,
        "source_sha": source_sha,
        "evidence_type": evidence_type,
    }


def _row(
    record_id: str,
    *,
    status: str,
    missing_proof_question: str,
    identity_gap: dict[str, Any],
    function_gap: dict[str, Any],
    relation_gap: dict[str, Any],
    successor_or_replacement_gap: dict[str, Any],
    current_system_fit_gap: dict[str, Any],
    claims: list[dict[str, Any]],
    evidence_refs: list[str],
    remaining_open_questions: list[str],
    relations_proven: list[dict[str, Any]] | None = None,
    contradictions: list[str] | None = None,
) -> dict[str, Any]:
    if status not in ALLOWED_RESOLUTION_STATUSES:
        raise ValueError(f"resolution_status_unknown:{record_id}:{status}")
    if record_id not in OPEN_IDS:
        raise ValueError(f"not_an_open_record:{record_id}")
    return {
        "record_id": record_id,
        "evidence_resolution_pass_id": EVIDENCE_RESOLUTION_PASS_ID,
        "evidence_resolution_status": status,
        "final_disposition_change_performed": False,
        "identity_merge_performed": False,
        "reintegration_performed": False,
        "runtime_mutation_performed": False,
        "disposition_unchanged": True,
        "missing_proof_question": missing_proof_question,
        "identity_gap": identity_gap,
        "function_gap": function_gap,
        "relation_gap": relation_gap,
        "successor_or_replacement_gap": successor_or_replacement_gap,
        "current_system_fit_gap": current_system_fit_gap,
        "claims": list(claims),
        "evidence_refs": list(evidence_refs),
        "remaining_open_questions": list(remaining_open_questions),
        "relations_proven": list(relations_proven or []),
        "contradictions": list(contradictions or []),
        "bound_against_ref": EVIDENCE_RESOLUTION_BOUND_REF,
        "bound_against_sha": EVIDENCE_RESOLUTION_BOUND_SHA,
        "census_bound_sha": CENSUS_BOUND_SHA,
        "adjudicate_frozen_sha": ADJUDICATE_FROZEN_SHA,
        "evaluate_frozen_sha": EVALUATE_FROZEN_SHA,
        "understand_frozen_sha": UNDERSTAND_FROZEN_SHA,
    }


def _understand(rid: str) -> str:
    return f"docs/system_atlas/reconciliation/understand/records/{rid}.yaml"


def _evaluate(rid: str) -> str:
    return f"docs/system_atlas/reconciliation/evaluate/records/{rid}.yaml"


def _adjudicate(rid: str) -> str:
    return f"docs/system_atlas/reconciliation/adjudicate/records/{rid}.yaml"


def _landscape(
    record_id: str,
    *,
    historical_artifact: str,
    historical_function: str,
    family_relations: str,
    unique_purpose_vs_v2_slots: str,
    extra_claims: list[dict[str, Any]] | None = None,
    extra_refs: list[str] | None = None,
    extra_relations: list[dict[str, Any]] | None = None,
    extra_questions: list[str] | None = None,
) -> dict[str, Any]:
    claims = [
        _claim(
            "FORENSIC_RAW_FACT",
            "Commit b5b81728 deleted the Market-Dashboard product stack on 2026-07-17 and stated "
            "kein Rebuild autorisiert oder begonnen; /market* absent (HTTP 404).",
            [QUOTES_REL, _understand(record_id)],
            used_as_fact=True,
            source_sha=STACK_DELETE_SHA,
            source_path="commit b5b81728 message",
            evidence_type="FORENSIC_RAW",
        ),
        _claim(
            "FORENSIC_RAW_FACT",
            "Landscape V2 projection contracts were first added on 2026-07-23 by 82f71bbe (#5499), "
            "six calendar days after the v1 stack deletion. Later existence is not succession.",
            [QUOTES_REL, OWNER_REG],
            used_as_fact=True,
            source_sha=LANDSCAPE_V2_ADD_SHA,
            source_path="commit 82f71bbe",
            evidence_type="FORENSIC_RAW",
        ),
        _claim(
            "FORENSIC_RAW_FACT",
            "Landscape V2 owner_registry slots are market_instrument, universe_ranking, dynamic_scope, "
            "regime_bull_bear_switch, canonical_decision, double_play, risk_sizing_capital, "
            "safety_authority, execution_reconciliation, economic_summary, autonomy_stage, "
            "diagnostics_summary, source_health. The registry does not declare itself as "
            "product_surface_v1, readmodels_v1, depth/tape/ohlcv/eligibility/paper-run packages.",
            [OWNER_REG],
            used_as_fact=True,
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            source_path=OWNER_REG,
            evidence_type="FORENSIC_RAW",
        ),
        _claim(
            "FORENSIC_RAW_FACT",
            f"Historical artifact {historical_artifact} is absent on census SHA {CENSUS_BOUND_SHA} "
            f"and on origin/main {EVIDENCE_RESOLUTION_BOUND_SHA} (path count 0).",
            [COMMANDS_REL],
            used_as_fact=True,
            source_sha=CENSUS_BOUND_SHA,
            source_path=COMMANDS_REL,
            evidence_type="FORENSIC_RAW",
        ),
        _claim(
            "HYPOTHESIS",
            "GET /market consumer overlap with Landscape V2 may later support a coverage argument; "
            "it is not identity and not proven replacement of this artifact's unique purpose.",
            [OWNER_REG, _evaluate(record_id)],
            used_as_fact=False,
            source_path=OWNER_REG,
            evidence_type="HYPOTHESIS",
        ),
    ]
    if extra_claims:
        claims.extend(extra_claims)
    refs = [
        _understand(record_id),
        _evaluate(record_id),
        _adjudicate(record_id),
        OWNER_REG,
        QUOTES_REL,
        COMMANDS_REL,
        IMPORTS_REL,
    ]
    if extra_refs:
        refs.extend(extra_refs)
    questions = [
        "Does a current Landscape V2 slot cover this historical purpose, or only share GET /market?",
        "Unique current value of the deleted artifact versus Landscape V2 remains unproven.",
    ]
    if extra_questions:
        questions.extend(extra_questions)
    return _row(
        record_id,
        status=PARTIAL,
        missing_proof_question=(
            "Is this artifact the same identity as Landscape V2, a proven replacement/successor, "
            "or a distinct co-deleted v1 stack member whose unique purpose is or is not covered "
            "by a current Landscape V2 slot?"
        ),
        identity_gap=_gap(
            status="PROVEN_DISTINCT_FROM_LANDSCAPE_V2",
            statement=(
                f"{historical_artifact} is a distinct historical path/package. Co-deletion with "
                "other v1 dashboard files and later Landscape V2 naming do not prove SAME_AS "
                "RCN-000001. Similar name/path/GET /market is not identity."
            ),
            used_as_fact=True,
            source=STACK_DELETE_SHA,
            source_sha=STACK_DELETE_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        function_gap=_gap(
            status="PROVEN_HISTORICAL_FUNCTION",
            statement=historical_function,
            used_as_fact=True,
            source=_understand(record_id),
            source_sha=UNDERSTAND_FROZEN_SHA,
            evidence_type="HISTORICAL_INTERMEDIATE",
        ),
        relation_gap=_gap(
            status="PROVEN_FAMILY_RELATION_NOT_IDENTITY",
            statement=family_relations,
            used_as_fact=True,
            source=IMPORTS_REL,
            source_sha=STACK_PARENT_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        successor_or_replacement_gap=_gap(
            status="NOT_PROVEN",
            statement=(
                "Landscape V2 is a later consumer added after an explicit no-rebuild deletion. "
                "Later existence is not succession. Shared GET /market is not replacement. "
                f"{unique_purpose_vs_v2_slots}"
            ),
            used_as_fact=True,
            source=OWNER_REG,
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        current_system_fit_gap=_gap(
            status="UNPROVEN",
            statement=(
                "Current fit / unique uncovered value versus Landscape V2 slots remains unproven. "
                "This pass does not assign RETAIN, ADAPT, COVERED, INCOMPATIBLE, or REJECT."
            ),
            used_as_fact=False,
            source=_evaluate(record_id),
            source_sha=EVALUATE_FROZEN_SHA,
            evidence_type="OPEN_OR_CONTRADICTORY",
        ),
        claims=claims,
        evidence_refs=refs,
        remaining_open_questions=questions,
        relations_proven=extra_relations,
    )


def _never_merged_infra(
    record_id: str,
    *,
    path: str,
    commit_sha: str,
    historical_function: str,
    current_namesake: str,
    namesake_not_identity: str,
    missing_q: str,
    extra_questions: list[str],
    extra_refs: list[str],
) -> dict[str, Any]:
    return _row(
        record_id,
        status=PARTIAL,
        missing_proof_question=missing_q,
        identity_gap=_gap(
            status="PROVEN_HISTORICAL_EXISTENCE_ON_NON_MAIN_COMMIT",
            statement=(
                f"{path} exists at {commit_sha}. git merge-base --is-ancestor {commit_sha} "
                f"origin/main is false. Historical existence is proven off origin/main; it is "
                "not a current origin/main identity."
            ),
            used_as_fact=True,
            source=commit_sha,
            source_sha=commit_sha,
            evidence_type="FORENSIC_RAW",
        ),
        function_gap=_gap(
            status="PROVEN_HISTORICAL_FUNCTION",
            statement=historical_function,
            used_as_fact=True,
            source=_understand(record_id),
            source_sha=UNDERSTAND_FROZEN_SHA,
            evidence_type="HISTORICAL_INTERMEDIATE",
        ),
        relation_gap=_gap(
            status="UNPROVEN_VERSUS_CURRENT_NAMESAKE",
            statement=namesake_not_identity,
            used_as_fact=False,
            source=current_namesake,
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="HYPOTHESIS",
        ),
        successor_or_replacement_gap=_gap(
            status="NOT_PROVEN",
            statement=(
                f"Current namesake {current_namesake} is not proven SAME_AS / RENAMED_TO / "
                f"REPLACED_BY {path}. Similar theme is not replacement. Never-merged-to-main "
                "is not rejection."
            ),
            used_as_fact=True,
            source=current_namesake,
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        current_system_fit_gap=_gap(
            status="UNPROVEN",
            statement="Current unique value versus the namesake remains unproven. No disposition.",
            used_as_fact=False,
            source=_evaluate(record_id),
            source_sha=EVALUATE_FROZEN_SHA,
            evidence_type="OPEN_OR_CONTRADICTORY",
        ),
        claims=[
            _claim(
                "FORENSIC_RAW_FACT",
                f"{path} is absent on origin/main@{EVIDENCE_RESOLUTION_BOUND_SHA} and census "
                f"SHA {CENSUS_BOUND_SHA} (path count 0).",
                [COMMANDS_REL],
                used_as_fact=True,
                source_sha=CENSUS_BOUND_SHA,
                source_path=path,
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                f"Commit {commit_sha} is not an ancestor of origin/main@"
                f"{EVIDENCE_RESOLUTION_BOUND_SHA}.",
                [QUOTES_REL],
                used_as_fact=True,
                source_sha=commit_sha,
                source_path=path,
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "HYPOTHESIS",
                f"{current_namesake} may overlap thematically with {path}; identity is unproven.",
                [current_namesake] if not current_namesake.startswith("ABSENT:") else [QUOTES_REL],
                used_as_fact=False,
                source_path=current_namesake,
                evidence_type="HYPOTHESIS",
            ),
        ],
        evidence_refs=[
            _understand(record_id),
            _evaluate(record_id),
            _adjudicate(record_id),
            QUOTES_REL,
            COMMANDS_REL,
            *extra_refs,
        ],
        remaining_open_questions=extra_questions,
    )


def _archive_deleted(
    record_id: str,
    *,
    path: str,
    historical_function: str,
    missing_q: str,
    extra_questions: list[str],
    extra_refs: list[str],
    delete_sha: str = ARCHIVE_DELETE_SHA,
) -> dict[str, Any]:
    return _row(
        record_id,
        status=PARTIAL,
        missing_proof_question=missing_q,
        identity_gap=_gap(
            status="PROVEN_HISTORICAL_PATH_THEN_DELETED_ON_MAIN",
            statement=(
                f"{path} is historically attested then deleted on origin/main by {delete_sha}. "
                "Deletion is not identity with later namesakes."
            ),
            used_as_fact=True,
            source=delete_sha,
            source_sha=delete_sha,
            evidence_type="FORENSIC_RAW",
        ),
        function_gap=_gap(
            status="PROVEN_HISTORICAL_FUNCTION",
            statement=historical_function,
            used_as_fact=True,
            source=_understand(record_id),
            source_sha=UNDERSTAND_FROZEN_SHA,
            evidence_type="HISTORICAL_INTERMEDIATE",
        ),
        relation_gap=_gap(
            status="PROVEN_CO_DELETION_EVENT_NOT_IDENTITY",
            statement=(
                "Multiple archive/* trees were removed by the same 75722feea docs/archive cleanup "
                "where applicable. Shared deletion event is not SAME_AS among archive trees."
            ),
            used_as_fact=True,
            source=delete_sha,
            source_sha=delete_sha,
            evidence_type="FORENSIC_RAW",
        ),
        successor_or_replacement_gap=_gap(
            status="NOT_PROVEN",
            statement=(
                "Later current modules with similar names are not proven replacements. "
                "Absence is not irrelevance. Relocation is not assumed."
            ),
            used_as_fact=True,
            source=_evaluate(record_id),
            source_sha=EVALUATE_FROZEN_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        current_system_fit_gap=_gap(
            status="UNPROVEN",
            statement="Current unique value versus later namesakes remains unproven. No disposition.",
            used_as_fact=False,
            source=_evaluate(record_id),
            source_sha=EVALUATE_FROZEN_SHA,
            evidence_type="OPEN_OR_CONTRADICTORY",
        ),
        claims=[
            _claim(
                "FORENSIC_RAW_FACT",
                f"{path} is absent on origin/main and census SHA (path count 0).",
                [COMMANDS_REL],
                used_as_fact=True,
                source_sha=CENSUS_BOUND_SHA,
                source_path=path,
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                f"Last origin/main touching commit for this archive family includes {delete_sha} "
                "(docs: governance/audit runbooks + remove obsolete archive/ #573) except where "
                "a different deletion SHA is bound on the record.",
                [QUOTES_REL],
                used_as_fact=True,
                source_sha=delete_sha,
                source_path=path,
                evidence_type="FORENSIC_RAW",
            ),
        ],
        evidence_refs=[
            _understand(record_id),
            _evaluate(record_id),
            _adjudicate(record_id),
            QUOTES_REL,
            COMMANDS_REL,
            *extra_refs,
        ],
        remaining_open_questions=extra_questions,
    )


def evidence_resolution_records() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    rows.append(
        _landscape(
            "RCN-000009",
            historical_artifact="src/webui/market_dashboard_product_surface_v1",
            historical_function=(
                "Read-only presentation path: source loader → page aggregate → presenter → "
                "template for GET /market (PR-D). Presenter maps MarketDashboardPageSnapshotV1 "
                "with no producer I/O."
            ),
            family_relations=(
                "At 987e020, product_surface_v1/presenter.py IMPORTS readmodels_v1 (RCN-000010). "
                "source_loader.py IMPORTS market_futures_ohlcv_* (RCN-000030) and "
                "market_ranking_funnel_* (RCN-000029). Co-deleted with the v1 stack in b5b81728. "
                "IMPORTS is not SAME_AS."
            ),
            unique_purpose_vs_v2_slots=(
                "No Landscape V2 slot is named product_surface_v1. Slot overlap is unproven."
            ),
            extra_claims=[
                _claim(
                    "FORENSIC_RAW_FACT",
                    "987e020:src/webui/market_dashboard_product_surface_v1/presenter.py imports "
                    "src.webui.market_dashboard_readmodels_v1.aggregate.MarketDashboardPageSnapshotV1.",
                    [IMPORTS_REL],
                    used_as_fact=True,
                    source_sha=STACK_PARENT_SHA,
                    source_path="src/webui/market_dashboard_product_surface_v1/presenter.py",
                    evidence_type="FORENSIC_RAW",
                )
            ],
            extra_relations=[
                {
                    "relation_type": "IMPORTS",
                    "target_id": "RCN-000010",
                    "epistemic_status": "FORENSIC_RAW_FACT",
                    "used_as_fact": True,
                    "source": f"{STACK_PARENT_SHA}:src/webui/market_dashboard_product_surface_v1/presenter.py",
                },
                {
                    "relation_type": "IMPORTS",
                    "target_id": "RCN-000030",
                    "epistemic_status": "FORENSIC_RAW_FACT",
                    "used_as_fact": True,
                    "source": f"{STACK_PARENT_SHA}:src/webui/market_dashboard_product_surface_v1/source_loader.py",
                },
                {
                    "relation_type": "IMPORTS",
                    "target_id": "RCN-000029",
                    "epistemic_status": "FORENSIC_RAW_FACT",
                    "used_as_fact": True,
                    "source": f"{STACK_PARENT_SHA}:src/webui/market_dashboard_product_surface_v1/source_loader.py",
                },
            ],
        )
    )
    rows.append(
        _landscape(
            "RCN-000010",
            historical_artifact="src/webui/market_dashboard_readmodels_v1",
            historical_function=(
                "Read-model aggregate/contracts/page_builder/adapters for the v1 dashboard page "
                "snapshot consumed by product_surface_v1."
            ),
            family_relations=(
                "IMPORTED_BY product_surface_v1 (RCN-000009). Separate package from "
                "product_surface_v1. Co-deleted in b5b81728. Not fused."
            ),
            unique_purpose_vs_v2_slots=(
                "Landscape V2 owner_registry maps slots to canonical producers, not to "
                "market_dashboard_readmodels_v1."
            ),
            extra_relations=[
                {
                    "relation_type": "IMPORTED_BY",
                    "target_id": "RCN-000009",
                    "epistemic_status": "FORENSIC_RAW_FACT",
                    "used_as_fact": True,
                    "source": f"{STACK_PARENT_SHA}:src/webui/market_dashboard_product_surface_v1/presenter.py",
                }
            ],
        )
    )
    rows.append(
        _landscape(
            "RCN-000011",
            historical_artifact="src/webui/market_visual_operator_surface_v1",
            historical_function=(
                "Visual operator chrome/display modules (header, overview, decision funnel, "
                "economic observability, chart display) for the v1 operator surface."
            ),
            family_relations=(
                "Co-deleted in b5b81728 with the v1 stack. No proven SAME_AS to product_surface_v1 "
                "or Landscape V2. Operator chrome relation remains unfused."
            ),
            unique_purpose_vs_v2_slots=(
                "No owner_registry slot is named market_visual_operator_surface_v1."
            ),
        )
    )
    rows.append(
        _landscape(
            "RCN-000012",
            historical_artifact="src/webui/futures_read_only_market_dashboard_runtime_v0.py",
            historical_function=(
                "SSR-only F5 dashboard context for GET /market/futures (fail closed by default)."
            ),
            family_relations=(
                "Referenced from historical app.py as GET /market/futures. Co-deleted in b5b81728. "
                "POSSIBLE_SAME_AS product_surface_v1 remains hypothesis."
            ),
            unique_purpose_vs_v2_slots=(
                "Landscape V2 shell is GET /market, not proven to be the F5 /market/futures runtime."
            ),
        )
    )
    rows.append(
        _archive_deleted(
            "RCN-000014",
            path="archive/PeakTradeRepo",
            historical_function=(
                "Nested historical PeakTradeRepo tree under archive/. Placeholder vs implemented "
                "inner blobs remain separately recorded as RCN-000044/045/046."
            ),
            missing_q=(
                "Which recovered inner blobs represent the claimed historical stack, and is any "
                "current module the same identity?"
            ),
            extra_questions=[
                "Inner components RCN-000044/045/046 remain separate records; not fused here.",
                "Whether a fuller snapshot existed before placeholder blobs is not reconstructed.",
            ],
            extra_refs=[
                "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml"
            ],
        )
    )
    rows.append(_rcn_000015())
    rows.append(_rcn_000019())
    rows.append(_rcn_000020())
    rows.append(
        _landscape(
            "RCN-000023",
            historical_artifact="src/webui/market_surface.py",
            historical_function=(
                "Canonical GET /market owner (CANONICAL_MARKET_ROUTE=/market; "
                "CANONICAL_MARKET_ROUTE_OWNER=src/webui/market_surface.py) binding PR-D product "
                "surface. Named owners for ranking funnel, eligibility, and futures OHLCV."
            ),
            family_relations=(
                "At 987e020, market_surface.py declares CANONICAL_FUTURES_UNIVERSE_OWNER and "
                "CANONICAL_RANKING_FUNNEL_OWNER as market_ranking_funnel_runtime_v0.py (RCN-000029), "
                "CANONICAL_ELIGIBILITY_OWNER as market_instrument_eligibility_v0.py (RCN-000031), "
                "CANONICAL_FUTURES_OHLCV_OWNER as market_futures_ohlcv_runtime_v0.py (RCN-000030). "
                "Route ownership is a relation, not SAME_AS those modules."
            ),
            unique_purpose_vs_v2_slots=(
                "Current GET /market is served by market_dashboard_landscape_shell_router_v2.py. "
                "HTTP path reuse is not identity of market_surface.py with Landscape V2."
            ),
            extra_claims=[
                _claim(
                    "FORENSIC_RAW_FACT",
                    "987e020:src/webui/market_surface.py sets CANONICAL_MARKET_ROUTE = '/market' "
                    "and CANONICAL_MARKET_ROUTE_OWNER = 'src/webui/market_surface.py'.",
                    [QUOTES_REL, IMPORTS_REL],
                    used_as_fact=True,
                    source_sha=STACK_PARENT_SHA,
                    source_path="src/webui/market_surface.py",
                    evidence_type="FORENSIC_RAW",
                )
            ],
            extra_refs=["src/webui/market_dashboard_landscape_shell_router_v2.py"],
            extra_relations=[
                {
                    "relation_type": "REFERENCES",
                    "target_id": "RCN-000029",
                    "epistemic_status": "FORENSIC_RAW_FACT",
                    "used_as_fact": True,
                    "source": f"{STACK_PARENT_SHA}:src/webui/market_surface.py",
                },
                {
                    "relation_type": "REFERENCES",
                    "target_id": "RCN-000031",
                    "epistemic_status": "FORENSIC_RAW_FACT",
                    "used_as_fact": True,
                    "source": f"{STACK_PARENT_SHA}:src/webui/market_surface.py",
                },
                {
                    "relation_type": "REFERENCES",
                    "target_id": "RCN-000030",
                    "epistemic_status": "FORENSIC_RAW_FACT",
                    "used_as_fact": True,
                    "source": f"{STACK_PARENT_SHA}:src/webui/market_surface.py",
                },
            ],
        )
    )
    rows.append(
        _landscape(
            "RCN-000027",
            historical_artifact="src/webui/market_depth_api_v0.py + depth readmodel/runtime",
            historical_function="Market depth fixture read-model v0 and GET /api/market/depth JSON.",
            family_relations=(
                "Co-deleted in b5b81728. Historical app.py documented GET /api/market/depth. "
                "No proven SAME_AS product_surface_v1."
            ),
            unique_purpose_vs_v2_slots="No owner_registry slot is named market_depth.",
        )
    )
    rows.append(
        _landscape(
            "RCN-000028",
            historical_artifact="src/webui/market_tape_readmodel_v0",
            historical_function="Market tape read-model v0 package (builder/gate).",
            family_relations="Co-deleted in b5b81728. Standalone tape package; not fused.",
            unique_purpose_vs_v2_slots="No owner_registry slot is named market_tape.",
        )
    )
    rows.append(
        _landscape(
            "RCN-000029",
            historical_artifact="src/webui/market_ranking_funnel_readmodel_v0",
            historical_function="Ranking funnel readmodel/runtime v0 for futures universe/ranking.",
            family_relations=(
                "IMPORTED_BY product_surface_v1 source_loader (RCN-000009). Named as "
                "CANONICAL_RANKING_FUNNEL_OWNER by market_surface.py (RCN-000023). Co-deleted "
                "in b5b81728. Landscape V2 universe_ranking slot uses "
                "universe_selection_readmodel.v1 — namesake ranking is not identity."
            ),
            unique_purpose_vs_v2_slots=(
                "universe_ranking slot owner is workflow_dashboard_readmodel_v1."
                "universe_selection_contract_v1, not market_ranking_funnel_runtime_v0."
            ),
            extra_relations=[
                {
                    "relation_type": "IMPORTED_BY",
                    "target_id": "RCN-000009",
                    "epistemic_status": "FORENSIC_RAW_FACT",
                    "used_as_fact": True,
                    "source": f"{STACK_PARENT_SHA}:src/webui/market_dashboard_product_surface_v1/source_loader.py",
                }
            ],
        )
    )
    rows.append(
        _landscape(
            "RCN-000030",
            historical_artifact="src/webui/market_futures_ohlcv_readmodel_v0",
            historical_function="Futures OHLCV readmodel/runtime v0 for the v1 dashboard chart path.",
            family_relations=(
                "IMPORTED_BY product_surface_v1 source_loader. Named CANONICAL_FUTURES_OHLCV_OWNER "
                "by market_surface.py. Co-deleted in b5b81728. Landscape V2 market_instrument notes "
                "bind OHLCV via okx_selected_instrument_ohlcv_readmodel.v1 — different owner path."
            ),
            unique_purpose_vs_v2_slots=(
                "OHLCV projection in Landscape V2 is not this v0 package; replacement unproven."
            ),
            extra_relations=[
                {
                    "relation_type": "IMPORTED_BY",
                    "target_id": "RCN-000009",
                    "epistemic_status": "FORENSIC_RAW_FACT",
                    "used_as_fact": True,
                    "source": f"{STACK_PARENT_SHA}:src/webui/market_dashboard_product_surface_v1/source_loader.py",
                }
            ],
        )
    )
    rows.append(
        _landscape(
            "RCN-000031",
            historical_artifact="src/webui/market_instrument_eligibility_v0.py",
            historical_function="Instrument eligibility helper for the v1 market surface.",
            family_relations=(
                "Named CANONICAL_ELIGIBILITY_OWNER by market_surface.py. Co-deleted in b5b81728. "
                "Not fused with ranking funnel."
            ),
            unique_purpose_vs_v2_slots="No owner_registry slot is this eligibility module.",
        )
    )
    rows.append(
        _landscape(
            "RCN-000032",
            historical_artifact="src/webui/market_active_paper_run_runtime_v0.py",
            historical_function="Active paper-run runtime helper for the v1 dashboard (CSV/JSON IO).",
            family_relations=(
                "Co-deleted in b5b81728. Relation to later paper-shadow runtimes is unproven identity."
            ),
            unique_purpose_vs_v2_slots="No owner_registry slot is market_active_paper_run_runtime_v0.",
            extra_questions=[
                "Relation to paper-shadow runtimes remains unproven identity.",
            ],
        )
    )
    rows.append(
        _landscape(
            "RCN-000033",
            historical_artifact="src/webui/market_dashboard_current_state_runtime_v0.py",
            historical_function="Current-state snapshot/runtime v0 for the v1 dashboard.",
            family_relations="Co-deleted in b5b81728. Imports sibling snapshot module. Not fused.",
            unique_purpose_vs_v2_slots="No owner_registry slot is this current-state runtime.",
        )
    )
    rows.append(
        _landscape(
            "RCN-000034",
            historical_artifact="docs/product Market Dashboard Architecture Reset/Rebuild + v1 docs",
            historical_function="Product documentation of the v1 dashboard architecture/reset.",
            family_relations=(
                "docs/webui/MARKET_DASHBOARD_PRODUCT_SURFACE_V1.md and READMODELS_V1.md were "
                "deleted in b5b81728. Documentation-to-code POSSIBLE_SAME_AS remains hypothesis."
            ),
            unique_purpose_vs_v2_slots="Current Landscape V2 docs (RCN-000002, RETAIN) are a later document set.",
        )
    )
    rows.append(
        _landscape(
            "RCN-000035",
            historical_artifact="docs/product Composition Landmark Master Runbook v1.3",
            historical_function="Composition landmark master runbook v1.3 for the dashboard product.",
            family_relations=(
                "Distinct from Landscape V2 master runbook RCN-000002 unless proven SAME_AS. "
                "Co-deleted/absent with the v1 product docs family."
            ),
            unique_purpose_vs_v2_slots="RCN-000002 remains a separate RETAIN record; not fused here.",
        )
    )
    rows.append(
        _archive_deleted(
            "RCN-000036",
            path="archive/full_files_stand_02.12.2025",
            historical_function="Dated 2025-12-02 export tree (INSTALLATION.txt / peak_trade_export).",
            missing_q="Same snapshot as archive/PeakTradeRepo or a different export?",
            extra_questions=[
                "Different tree from PeakTradeRepo; POSSIBLE_SAME_AS remains hypothesis.",
            ],
            extra_refs=[],
        )
    )
    rows.append(
        _archive_deleted(
            "RCN-000037",
            path="archive/legacy_docs",
            historical_function="Legacy docs archive (README.before_phase58.md attested).",
            missing_q="What documents did this archive hold besides the README?",
            extra_questions=["Full inner listing beyond the README is not reconstructed."],
            extra_refs=[],
        )
    )
    rows.append(
        _archive_deleted(
            "RCN-000038",
            path="archive/legacy_scripts/run_regime_experiments.sh",
            historical_function="Legacy regime-experiment shell script archived from repo root.",
            missing_q="Standalone tooling versus later regime sweep scripts?",
            extra_questions=["Relation to later regime-sweep scripts is unproven identity."],
            extra_refs=[],
        )
    )
    rows.append(
        _never_merged_infra(
            "RCN-000039",
            path="src/infra/health",
            commit_sha=INFRA_HEALTH_SHA,
            historical_function=(
                "Central HealthChecker/HealthStatus ampel GREEN/YELLOW/RED with backtest/exchange/"
                "live/portfolio/risk checks; CLI python -m src.infra.health.health_checker."
            ),
            current_namesake="src/risk_layer/kill_switch/health_check.py",
            namesake_not_identity=(
                "Current kill_switch.health_check.HealthChecker validates recovery from killed "
                "state (psutil/system issues). That is not proven SAME_AS infra.health ampel. "
                "src/core/resilience.py HealthCheck is a third namesake."
            ),
            missing_q=(
                "Did src/infra/health migrate into kill_switch health_check, core.resilience, or neither?"
            ),
            extra_questions=[
                "Blob identity versus kill_switch/health_check.py is unproven.",
                "Never-merged-to-origin/main is presence, not disposition.",
            ],
            extra_refs=[
                "src/risk_layer/kill_switch/health_check.py",
                "src/core/resilience.py",
            ],
        )
    )
    rows.append(
        _never_merged_infra(
            "RCN-000040",
            path="src/infra/backup",
            commit_sha=INFRA_BUNDLE_SHA,
            historical_function="Historical backup package introduced with resilience/monitoring (12188014).",
            current_namesake="ABSENT:no_src_infra_backup_on_origin_main",
            namesake_not_identity=(
                "No src/infra/backup on origin/main. Later disaster-recovery docs/scripts are "
                "not proven SAME_AS this package."
            ),
            missing_q="Does a later backup/recovery owner exist under another path as the same identity?",
            extra_questions=["Relation to disaster-recovery docs/scripts is unproven identity."],
            extra_refs=[],
        )
    )
    rows.append(
        _never_merged_infra(
            "RCN-000041",
            path="src/infra/monitoring",
            commit_sha=INFRA_BUNDLE_SHA,
            historical_function="Historical monitoring package bundled with resilience/backup (12188014).",
            current_namesake="src/obs",
            namesake_not_identity=(
                "src/obs and src/observability exist on origin/main as later packages. "
                "Thematic proximity to deleted docs/observability (RCN-000020) is not identity."
            ),
            missing_q="Is risk_layer.alerting or src/obs a successor of src/infra/monitoring?",
            extra_questions=[
                "Relation to deleted Grafana docs/observability is unproven identity.",
            ],
            extra_refs=["src/risk_layer/alerting/__init__.py"],
        )
    )
    rows.append(
        _never_merged_infra(
            "RCN-000042",
            path="src/infra/resilience",
            commit_sha=INFRA_BUNDLE_SHA,
            historical_function=(
                "Historical package: circuit_breaker.py, retry.py, fallback.py, rate_limiter.py "
                f"at {INFRA_BUNDLE_SHA}."
            ),
            current_namesake="src/core/resilience.py",
            namesake_not_identity=(
                "src/core/resilience.py (circuit breaker, retry, health_check) exists on origin/main "
                "(added 714b90f0 #102). Blob SHAs of infra/resilience files at 12188014 are not "
                "the same path. Package vs module namesake is not identity."
            ),
            missing_q="Is src/core/resilience.py the same historical package as src/infra/resilience?",
            extra_questions=[
                "Blob-level SAME_AS is unproven; no git rename recorded on origin/main."
            ],
            extra_refs=["src/core/resilience.py"],
        )
    )
    rows.append(_rcn_000043())
    rows.append(
        _archive_deleted(
            "RCN-000044",
            path="archive/PeakTradeRepo/src/backtest/engine.py",
            historical_function="Nested archive backtest engine/results/stats snapshot.",
            missing_q="Same component as later src/backtest or a distinct nested snapshot?",
            extra_questions=["Placeholder vs implemented export engine remains unfused."],
            extra_refs=[
                "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml"
            ],
        )
    )
    rows.append(
        _archive_deleted(
            "RCN-000045",
            path="archive/PeakTradeRepo/src/risk/position_sizer.py",
            historical_function="Nested archive position_sizer snapshot.",
            missing_q="Identity versus deleted position_sizer_old_backup or current sizer modules?",
            extra_questions=["No SAME_AS to later sizer modules is proven."],
            extra_refs=[],
        )
    )
    rows.append(
        _archive_deleted(
            "RCN-000046",
            path="archive/PeakTradeRepo/src/strategies/ma_crossover.py",
            historical_function="Nested archive ma_crossover strategy snapshot.",
            missing_q="Same strategy as later ma_crossover implementations?",
            extra_questions=["Not proven SAME_AS later ma_crossover implementations."],
            extra_refs=[],
        )
    )
    rows.append(
        _landscape(
            "RCN-000047",
            historical_artifact="evidence/market_dashboard_reset/pr_a",
            historical_function=(
                "Reset-pack evidence for the market dashboard architecture reset (added 987e020/"
                "1d61ec0d/500f15e4 on 2026-07-17) then deleted with the stack in b5b81728."
            ),
            family_relations=(
                "Different evidence event from the still-present deletion pack "
                "evidence/market_dashboard_deletion (RCN-000013, RETAIN). POSSIBLE_SAME_AS "
                "RCN-000013 remains hypothesis: reset pack vs later deletion pack."
            ),
            unique_purpose_vs_v2_slots=(
                "Reset pack is evidence, not a Landscape V2 slot. GET /market overlap does not apply "
                "as identity."
            ),
            extra_refs=["evidence/market_dashboard_deletion/deletion_manifest.txt"],
            extra_questions=[
                "What did the reset pack assert that the deletion pack (RCN-000013) did not?",
            ],
        )
    )
    rows.append(_rcn_000048())
    rows.append(_rcn_000049())
    rows.append(_rcn_000050())
    rows.append(
        _archive_deleted(
            "RCN-000051",
            path="archive/noch_einordnen/README.md",
            historical_function="Staging archive 'noch_einordnen' with README.",
            missing_q="What was queued in this archive?",
            extra_questions=[
                "Text overlap with PeakTradeRepo README is not SAME_AS without blob proof."
            ],
            extra_refs=[],
            delete_sha=NOCH_EINORDNEN_DEL_SHA,
        )
    )
    rows.append(_rcn_000052())

    if len(rows) != 35:
        raise ValueError(f"open_resolution_count_mismatch:{len(rows)}")
    ids = [r["record_id"] for r in rows]
    if tuple(ids) != OPEN_IDS:
        raise ValueError(f"open_id_order_mismatch:{ids}")
    return rows


def _rcn_000015() -> dict[str, Any]:
    cap23 = "src/ops/single_selected_future_policy_v1/constants_v1.py"
    cap23_sel = "src/ops/single_selected_future_policy_v1/selection_v1.py"
    return _row(
        "RCN-000015",
        status=PARTIAL,
        missing_proof_question=(
            "Is single_selected_future_policy_v1 a successor of master_v2_minimal_selector_v1, "
            "or a distinct later/earlier owner? Why was #6165 reverted?"
        ),
        identity_gap=_gap(
            status="PROVEN_DISTINCT_FROM_CAP_2_3",
            statement=(
                "Capability IDs differ (MASTER_V2_MINIMAL_SELECTOR_V1 vs "
                "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1). The selector package itself "
                "states it does not rewrite Cap 2.3 stickiness/ranking selection. Cap 2.3 was "
                "added 2026-08-02 (#5642 / ecb44849) before the selector add 2026-08-30 (#6165)."
            ),
            used_as_fact=True,
            source=SELECTOR_ADD_SHA,
            source_sha=SELECTOR_ADD_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        function_gap=_gap(
            status="PROVEN_HISTORICAL_FUNCTION",
            statement=(
                "Census → structural eligibility → exactly-one-or-none → durable artifact. "
                "eligible_count==0 or >1 → NO_SELECTION; ranking is not a selection authority; "
                "no fallback/cadence/hot-path rescan. Ranking is ignored (ranking_input_ignored=True)."
            ),
            used_as_fact=True,
            source=f"{SELECTOR_ADD_SHA}:src/ops/master_v2_minimal_selector_v1/selection_v1.py",
            source_sha=SELECTOR_ADD_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        relation_gap=_gap(
            status="PROVEN_EXPLICIT_NON_REWRITE_OF_CAP_2_3",
            statement=(
                "Selector constants_v1.py: This package is a new Owner policy surface. It does not "
                "rewrite Cap 2.1 GFU eligibility, Cap 2.2 ranking authority, Cap 2.3 stickiness/"
                "ranking selection, or Cap 2.4 ranking-gated binding. CAP22_SELECTION_AUTHORITY=False. "
                "Cap 2.3 SELECTION_AUTHORITY_ADDED=True and uses ranking hysteresis/min holding."
            ),
            used_as_fact=True,
            source=f"{SELECTOR_ADD_SHA}:src/ops/master_v2_minimal_selector_v1/constants_v1.py",
            source_sha=SELECTOR_ADD_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        successor_or_replacement_gap=_gap(
            status="REFUTED_AS_SUCCESSOR_OF_SELECTOR",
            statement=(
                "Cap 2.3 cannot be a successor of the selector: it predates the selector by 28 days. "
                "The selector explicitly claims not to rewrite Cap 2.3. Revert #6166 is not a "
                "replacement proof and not a disposition."
            ),
            used_as_fact=True,
            source=CAP23_ADD_SHA,
            source_sha=CAP23_ADD_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        current_system_fit_gap=_gap(
            status="UNPROVEN",
            statement=(
                "Whether the selector's fail-closed-unless-exactly-one policy has unique current "
                "value versus Cap 2.3 ranking selection remains a later EVALUATE/ADJUDICATE question. "
                "No disposition in this pass."
            ),
            used_as_fact=False,
            source=_evaluate("RCN-000015"),
            source_sha=EVALUATE_FROZEN_SHA,
            evidence_type="OPEN_OR_CONTRADICTORY",
        ),
        claims=[
            _claim(
                "FORENSIC_RAW_FACT",
                "Selector constants: 'This package is a new Owner policy surface. It does not rewrite "
                "Cap 2.1 GFU eligibility, Cap 2.2 ranking authority, Cap 2.3 stickiness/ranking "
                "selection, or Cap 2.4 ranking-gated binding.'",
                [QUOTES_REL],
                used_as_fact=True,
                source_sha=SELECTOR_ADD_SHA,
                source_path="src/ops/master_v2_minimal_selector_v1/constants_v1.py",
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "Selector selection_v1.py: eligible_count == 0 → NO_SELECTION; == 1 → SELECT; "
                "> 1 → NO_SELECTION. No ranking, score, sort-to-select, fallback, cadence, or "
                "hot-path rescan.",
                [QUOTES_REL],
                used_as_fact=True,
                source_sha=SELECTOR_ADD_SHA,
                source_path="src/ops/master_v2_minimal_selector_v1/selection_v1.py",
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "Cap 2.3 added ecb44849 2026-08-02 feat(ops): Single Selected Future Policy "
                "(Capability 2.3) (#5642). Selector added 75eee7bd 2026-08-30 (#6165) and "
                "reverted afbae518 2026-08-30 (#6166).",
                [QUOTES_REL, cap23],
                used_as_fact=True,
                source_sha=CAP23_ADD_SHA,
                source_path=cap23,
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "Revert #6166 body is only: This reverts commit 75eee7bdc501ab4b0ec93812675cd074acb9e2ee. "
                "No additional causal statement is in that commit message.",
                [QUOTES_REL],
                used_as_fact=True,
                source_sha=SELECTOR_REVERT_SHA,
                source_path="commit afbae518",
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "CANONICAL_CURRENT_FACT",
                "Cap 2.3 constants: SELECTION_AUTHORITY_ADDED=True; provenance includes Cap 2.2 "
                "Top-20 ranking + hysteresis/min holding. That is current-system fact, not identity "
                "with RCN-000015.",
                [cap23, cap23_sel],
                used_as_fact=True,
                source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
                source_path=cap23,
                evidence_type="CANONICAL_AUTHORITY",
            ),
            _claim(
                "OPEN_QUESTION",
                "Semantic cause of revert #6166 beyond the revert pointer is not stated in the "
                "commit body. Cause remains unproven.",
                [QUOTES_REL],
                used_as_fact=False,
                source_sha=SELECTOR_REVERT_SHA,
                evidence_type="OPEN_OR_CONTRADICTORY",
            ),
        ],
        evidence_refs=[
            _understand("RCN-000015"),
            _evaluate("RCN-000015"),
            _adjudicate("RCN-000015"),
            cap23,
            cap23_sel,
            QUOTES_REL,
            COMMANDS_REL,
        ],
        remaining_open_questions=[
            "Why was #6165 reverted, beyond the revert pointer in #6166?",
            "Unique current value of fail-closed-unless-exactly-one versus Cap 2.3 ranking selection remains unproven.",
        ],
        relations_proven=[
            {
                "relation_type": "REFERENCES",
                "unresolved_target": "CAPABILITY_2_3_SINGLE_SELECTED_FUTURE_POLICY_V1",
                "epistemic_status": "FORENSIC_RAW_FACT",
                "used_as_fact": True,
                "note": "Selector constants explicitly refuse to rewrite Cap 2.3. Not SAME_AS.",
            }
        ],
    )


def _rcn_000019() -> dict[str, Any]:
    ks_pkg = "src/risk_layer/kill_switch/__init__.py"
    ks_core = "src/risk_layer/kill_switch/core.py"
    risk_gate = "src/risk_layer/risk_gate.py"
    return _row(
        "RCN-000019",
        status=PARTIAL,
        missing_proof_question=(
            "Are deleted top-level kill_switch.py / LiquidityGate / StressGate / VaRGate / metrics "
            "the same identity as src/risk_layer/kill_switch/ or covered by risk_gate.py?"
        ),
        identity_gap=_gap(
            status="PROVEN_DISTINCT_KILL_SWITCH_PY_VS_PACKAGE",
            statement=(
                "At 14d58ec3 both src/risk_layer/kill_switch.py (blob 0980df3c) and "
                "src/risk_layer/kill_switch/ package (core.py blob fca4f4c1) coexisted. "
                "git log --follow on kill_switch.py shows D, not R, at f83442953. Different "
                "class names: KillSwitchLayer vs KillSwitch. Adapter.py labeled TEMPORARY/"
                "DEPRECATED legacy KillSwitchLayer API. Coexistence + different blobs + no "
                "rename is not identity."
            ),
            used_as_fact=True,
            source=KS_PACKAGE_ADD_SHA,
            source_sha=KS_PACKAGE_ADD_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        function_gap=_gap(
            status="PROVEN_HISTORICAL_FUNCTION_PER_MODULE",
            statement=(
                "kill_switch.py: KillSwitchLayer emergency sticky block on daily loss/drawdown/"
                "volatility using RiskMetrics. liquidity_gate.py: pre-trade microstructure "
                "OK/WARN/BLOCK (missing metrics → OK). stress_gate.py: scenario shocks. "
                "var_gate.py: portfolio VaR vs thresholds, RiskGate orchestration interface. "
                "metrics.py / micro_metrics.py: extractors. Functions are proven per historical blob."
            ),
            used_as_fact=True,
            source=KS_PY_PARENT_SHA,
            source_sha=KS_PY_PARENT_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        relation_gap=_gap(
            status="PROVEN_CO_DELETION_AND_LEGACY_ADAPTER_NOT_FUSION",
            statement=(
                "f83442953 (#413) deleted kill_switch.py, liquidity_gate.py, stress_gate.py, "
                "var_gate.py, metrics.py, micro_metrics.py, and also risk_gate.py/models.py/"
                "audit_log.py on origin/main. kill_switch/ package survived that commit. "
                "PR #409 adapter bridged old KillSwitchLayer evaluator API to new state machine. "
                "Adapter is compatibility, not SAME_AS."
            ),
            used_as_fact=True,
            source=RISK_DELETE_SHA,
            source_sha=RISK_DELETE_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        successor_or_replacement_gap=_gap(
            status="NOT_PROVEN_FOR_GATES",
            statement=(
                "Current risk_gate.py docstring: 'In this skeleton version, only basic validation "
                "is performed. Future versions will integrate VaR, stress testing, and other risk "
                "models.' No LiquidityGate/StressGate/VaRGate imports in current risk_gate.py or "
                "kill_switch package. src/risk_layer/types.py has class RiskMetrics (namesake). "
                "docs/risk/*_GATE_RUNBOOK.md still show from src.risk_layer.var_gate import VaRGate "
                "which is documentation of a missing module, not current code identity."
            ),
            used_as_fact=True,
            source=risk_gate,
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        current_system_fit_gap=_gap(
            status="UNPROVEN",
            statement=(
                "Record still bundles present package + absent modules. Stronger family-level "
                "disposition would conflate them. Unique current value of missing gates remains "
                "unproven. No disposition in this pass."
            ),
            used_as_fact=False,
            source=_evaluate("RCN-000019"),
            source_sha=EVALUATE_FROZEN_SHA,
            evidence_type="OPEN_OR_CONTRADICTORY",
        ),
        claims=[
            _claim(
                "FORENSIC_RAW_FACT",
                "14d58ec3 contains BOTH src/risk_layer/kill_switch.py and src/risk_layer/kill_switch/.",
                [QUOTES_REL],
                used_as_fact=True,
                source_sha=KS_PACKAGE_ADD_SHA,
                source_path="src/risk_layer/kill_switch.py",
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "Historical kill_switch.py class is KillSwitchLayer; package core.py class is KillSwitch.",
                [QUOTES_REL, ks_core],
                used_as_fact=True,
                source_sha=KS_PY_PARENT_SHA,
                source_path="src/risk_layer/kill_switch.py",
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "adapter.py: TEMPORARY / DEPRECATED Legacy Adapter for KillSwitchLayer API Compatibility.",
                [QUOTES_REL],
                used_as_fact=True,
                source_sha=KS_PACKAGE_ADD_SHA,
                source_path="src/risk_layer/kill_switch/adapter.py",
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "CANONICAL_CURRENT_FACT",
                "Current risk_gate.py is a skeleton orchestrator importing KillSwitch package; "
                "it does not import liquidity_gate, stress_gate, or var_gate.",
                [risk_gate, ks_pkg],
                used_as_fact=True,
                source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
                source_path=risk_gate,
                evidence_type="CANONICAL_AUTHORITY",
            ),
            _claim(
                "HYPOTHESIS",
                "risk_gate.py may later grow VaR/stress integration as its docstring speculates; "
                "that is not current coverage of historical LiquidityGate/StressGate/VaRGate.",
                [risk_gate],
                used_as_fact=False,
                source_path=risk_gate,
                evidence_type="HYPOTHESIS",
            ),
        ],
        evidence_refs=[
            _understand("RCN-000019"),
            _evaluate("RCN-000019"),
            _adjudicate("RCN-000019"),
            ks_pkg,
            ks_core,
            risk_gate,
            QUOTES_REL,
            COMMANDS_REL,
        ],
        remaining_open_questions=[
            "Are LiquidityGate/StressGate/VaRGate purposes covered anywhere other than the skeleton risk_gate docstring?",
            "Should the bundled family record later be split? Splitting is not identity fusion and is not done here.",
        ],
    )


def _rcn_000020() -> dict[str, Any]:
    return _row(
        "RCN-000020",
        status=PARTIAL,
        missing_proof_question="Does a current Grafana/observability stack remain under another path as the same identity?",
        identity_gap=_gap(
            status="PROVEN_HISTORICAL_PATH_PURGED_ON_MAIN",
            statement=(
                "docs/observability Grafana family was purged on origin/main by 1c71a4eab "
                "2026-02-23 security: purge Grafana artifacts (#1578). Path count 0 on current "
                "origin/main and census SHA."
            ),
            used_as_fact=True,
            source=GRAFANA_PURGE_SHA,
            source_sha=GRAFANA_PURGE_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        function_gap=_gap(
            status="PROVEN_HISTORICAL_FUNCTION",
            statement="Grafana/Prometheus observability runbook family (LOGGING_FIELDS, OBS_STACK_RUNBOOK, dashboard setup).",
            used_as_fact=True,
            source=_understand("RCN-000020"),
            source_sha=UNDERSTAND_FROZEN_SHA,
            evidence_type="HISTORICAL_INTERMEDIATE",
        ),
        relation_gap=_gap(
            status="UNPROVEN_VERSUS_WEBUI_OBSERVABILITY_AND_SRC_OBS",
            statement=(
                "RCN-000052 docs/webui/observability is a different path family (hub HTML, not Grafana). "
                "src/obs and src/observability are later code packages. POSSIBLE_SAME_AS remains hypothesis."
            ),
            used_as_fact=False,
            source="docs/webui/observability/OBSERVABILITY_HUB_V0.md",
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="HYPOTHESIS",
        ),
        successor_or_replacement_gap=_gap(
            status="NOT_PROVEN",
            statement="Later src/obs / src/observability existence is not proven Grafana-runbook replacement.",
            used_as_fact=True,
            source=_evaluate("RCN-000020"),
            source_sha=EVALUATE_FROZEN_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        current_system_fit_gap=_gap(
            status="UNPROVEN",
            statement="Current unique value of a Grafana stack versus src/obs remains unproven. No disposition.",
            used_as_fact=False,
            source=_evaluate("RCN-000020"),
            source_sha=EVALUATE_FROZEN_SHA,
            evidence_type="OPEN_OR_CONTRADICTORY",
        ),
        claims=[
            _claim(
                "FORENSIC_RAW_FACT",
                "1c71a4eab is an ancestor of origin/main and is the last origin/main commit touching docs/observability.",
                [QUOTES_REL, COMMANDS_REL],
                used_as_fact=True,
                source_sha=GRAFANA_PURGE_SHA,
                source_path="docs/observability",
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "HYPOTHESIS",
                "src/obs or src/observability may cover some observability purpose; Grafana identity is unproven.",
                [QUOTES_REL],
                used_as_fact=False,
                evidence_type="HYPOTHESIS",
            ),
        ],
        evidence_refs=[
            _understand("RCN-000020"),
            _evaluate("RCN-000020"),
            _adjudicate("RCN-000020"),
            "docs/webui/observability/OBSERVABILITY_HUB_V0.md",
            QUOTES_REL,
            COMMANDS_REL,
        ],
        remaining_open_questions=[
            "Is any current Grafana/OTLP runbook the same identity as the purged docs/observability family?",
        ],
    )


def _rcn_000043() -> dict[str, Any]:
    current = "src/ops/pre_economic_zero_order_evidence_session_contract_v1.py"
    return _row(
        "RCN-000043",
        status=PARTIAL,
        missing_proof_question=(
            "Do current evidence-session modules replace observer/arming/evidence, or only share a campaign name?"
        ),
        identity_gap=_gap(
            status="PROVEN_HISTORICAL_EXISTENCE_ON_NON_MAIN_COMMIT",
            statement=(
                f"Observer/arming/evidence trio exists at {PRE_ECON_SHA} which is not an ancestor "
                "of origin/main. Current origin/main has pre_economic_zero_order_evidence_session_* "
                "modules instead."
            ),
            used_as_fact=True,
            source=PRE_ECON_SHA,
            source_sha=PRE_ECON_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        function_gap=_gap(
            status="PROVEN_HISTORICAL_FUNCTION",
            statement=(
                "Wallclock arming lease (never places orders), hypothetical zero-order economics, "
                "decision-cycle observer of Master-V2 / Double-Play / Killstate."
            ),
            used_as_fact=True,
            source=_understand("RCN-000043"),
            source_sha=UNDERSTAND_FROZEN_SHA,
            evidence_type="HISTORICAL_INTERMEDIATE",
        ),
        relation_gap=_gap(
            status="PROVEN_SHARED_CAMPAIGN_PREFIX_NOT_IDENTITY",
            statement=(
                "Current contract capability GOVERNED_PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_STAGE_V1 "
                "and filenames evidence_session_* differ from decision_cycle_observer_v1 / "
                "wallclock_arming_v1 / economic_evidence_v1. Shared prefix is not SAME_AS."
            ),
            used_as_fact=True,
            source=current,
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        successor_or_replacement_gap=_gap(
            status="NOT_PROVEN",
            statement="No git rename from observer/arming trio into evidence_session_* is proven on origin/main.",
            used_as_fact=True,
            source=current,
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        current_system_fit_gap=_gap(
            status="UNPROVEN",
            statement="Unique uncovered observer/arming semantics versus evidence_session remain unproven.",
            used_as_fact=False,
            source=_evaluate("RCN-000043"),
            source_sha=EVALUATE_FROZEN_SHA,
            evidence_type="OPEN_OR_CONTRADICTORY",
        ),
        claims=[
            _claim(
                "FORENSIC_RAW_FACT",
                f"{PRE_ECON_SHA} is not an ancestor of origin/main.",
                [QUOTES_REL],
                used_as_fact=True,
                source_sha=PRE_ECON_SHA,
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "CANONICAL_CURRENT_FACT",
                "Current contract: Capability GOVERNED_PRE_ECONOMIC_ZERO_ORDER_EVIDENCE_STAGE_V1; "
                "never executes a session runtime; never contacts brokers; never creates orders.",
                [current],
                used_as_fact=True,
                source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
                source_path=current,
                evidence_type="CANONICAL_AUTHORITY",
            ),
            _claim(
                "HYPOTHESIS",
                "evidence_session may be a later campaign slice of the same zero-order program; identity unproven.",
                [current],
                used_as_fact=False,
                evidence_type="HYPOTHESIS",
            ),
        ],
        evidence_refs=[
            _understand("RCN-000043"),
            _evaluate("RCN-000043"),
            _adjudicate("RCN-000043"),
            current,
            QUOTES_REL,
            COMMANDS_REL,
        ],
        remaining_open_questions=[
            "Same family as later evidence_session modules is unproven identity.",
        ],
    )


def _rcn_000048() -> dict[str, Any]:
    return _row(
        "RCN-000048",
        status=PARTIAL,
        missing_proof_question=(
            "Were 20_phases markdowns superseded by Master Runbook sections, or lost without replacement?"
        ),
        identity_gap=_gap(
            status="PROVEN_PATH_FAMILY_ON_NON_MAIN_COMMIT_VIA_R100",
            statement=(
                "42c3f443d (not an ancestor of origin/main) recorded R100 renames "
                "docs/PHASE_*.md → docs/20_phases/PHASE_*.md. The 20_phases directory therefore "
                "existed as a rename target on that commit, not as an origin/main path."
            ),
            used_as_fact=True,
            source=DOC_TIDY_SHA,
            source_sha=DOC_TIDY_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        function_gap=_gap(
            status="PROVEN_HISTORICAL_FUNCTION",
            statement="Numbered phase markdowns (e.g. Phase 16A ExecutionPipeline; LIVE blocked in Phase 16A).",
            used_as_fact=True,
            source=_understand("RCN-000048"),
            source_sha=UNDERSTAND_FROZEN_SHA,
            evidence_type="HISTORICAL_INTERMEDIATE",
        ),
        relation_gap=_gap(
            status="PROVEN_R100_FROM_DOCS_ROOT_NOT_TO_MASTER_RUNBOOK",
            statement=(
                "The proven rename is docs/PHASE_* → docs/20_phases/PHASE_* on a never-merged "
                "commit. That is not a rename into docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md."
            ),
            used_as_fact=True,
            source=DOC_TIDY_SHA,
            source_sha=DOC_TIDY_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        successor_or_replacement_gap=_gap(
            status="NOT_PROVEN",
            statement=(
                "Master Runbook is current semantic authority; that does not prove it is the "
                "relocated 20_phases corpus. Current docs/ARCHITECTURE_OVERVIEW.md namesake is "
                "not automatically the 20_phases copy."
            ),
            used_as_fact=True,
            source="docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        current_system_fit_gap=_gap(
            status="UNPROVEN",
            statement="Whether phase markdowns retain unique current value versus Master Runbook is unproven.",
            used_as_fact=False,
            source=_evaluate("RCN-000048"),
            source_sha=EVALUATE_FROZEN_SHA,
            evidence_type="OPEN_OR_CONTRADICTORY",
        ),
        claims=[
            _claim(
                "FORENSIC_RAW_FACT",
                "42c3f443d is not an ancestor of origin/main. docs/20_phases path count is 0 on "
                "origin/main and census SHA.",
                [QUOTES_REL, COMMANDS_REL],
                used_as_fact=True,
                source_sha=DOC_TIDY_SHA,
                source_path="docs/20_phases",
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "42c3f443d name-status includes R100 docs/PHASE_16A_EXECUTION_PIPELINE.md → "
                "docs/20_phases/PHASE_16A_EXECUTION_PIPELINE.md.",
                [QUOTES_REL],
                used_as_fact=True,
                source_sha=DOC_TIDY_SHA,
                evidence_type="FORENSIC_RAW",
            ),
        ],
        evidence_refs=[
            _understand("RCN-000048"),
            _evaluate("RCN-000048"),
            _adjudicate("RCN-000048"),
            "docs/runbooks/canonical/PEAK_TRADE_MASTER_RUNBOOK.md",
            QUOTES_REL,
            COMMANDS_REL,
        ],
        remaining_open_questions=[
            "Path move versus later runbook locations is unproven identity on origin/main.",
        ],
    )


def _rcn_000049() -> dict[str, Any]:
    return _row(
        "RCN-000049",
        status=PARTIAL,
        missing_proof_question="Are current overview docs the relocated 00_overview family, or separately authored?",
        identity_gap=_gap(
            status="MIXED_TWO_PATH_HISTORIES_NOT_FUSED",
            statement=(
                "On origin/main, docs/00_overview TODO-board files were added 6cf92151a and "
                "removed 9ede5aca0. Separately, never-merged 42c3f443d R100-moved several "
                "docs/*.md into docs/00_overview/. These are two histories under one path family "
                "name; they are not fused."
            ),
            used_as_fact=True,
            source=DOC_TIDY_SHA,
            source_sha=DOC_TIDY_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        function_gap=_gap(
            status="PROVEN_HISTORICAL_FUNCTION_SPLIT",
            statement=(
                "TODO-board HTML/README on origin/main (deleted). Overview/status/roadmap markdowns "
                "on the never-merged tidy commit."
            ),
            used_as_fact=True,
            source=_understand("RCN-000049"),
            source_sha=UNDERSTAND_FROZEN_SHA,
            evidence_type="HISTORICAL_INTERMEDIATE",
        ),
        relation_gap=_gap(
            status="HYPOTHESIS_VERSUS_RCN_000053",
            statement=(
                "POSSIBLE_SAME_AS src/docs (RCN-000053, RETAIN) remains hypothesis. 42c3f443d also "
                "R100-moved src/docs/Peak_Trade_WORKFLOW_NOTES.md into docs/00_overview/ on that "
                "never-merged commit — that is not origin/main identity."
            ),
            used_as_fact=False,
            source="src/docs/Peak_Trade_OVERVIEW.md",
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="HYPOTHESIS",
        ),
        successor_or_replacement_gap=_gap(
            status="NOT_PROVEN",
            statement="Current overview docs are not proven to be the relocated 00_overview family.",
            used_as_fact=True,
            source="src/docs/Peak_Trade_OVERVIEW.md",
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        current_system_fit_gap=_gap(
            status="UNPROVEN",
            statement="Unique current value of the deleted 00_overview family remains unproven.",
            used_as_fact=False,
            source=_evaluate("RCN-000049"),
            source_sha=EVALUATE_FROZEN_SHA,
            evidence_type="OPEN_OR_CONTRADICTORY",
        ),
        claims=[
            _claim(
                "FORENSIC_RAW_FACT",
                "origin/main history for docs/00_overview: add 6cf92151a, delete 9ede5aca0 (TODO board).",
                [QUOTES_REL],
                used_as_fact=True,
                source_sha="9ede5aca0",
                source_path="docs/00_overview",
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "42c3f443d R100 docs/PEAK_TRADE_OVERVIEW.md → docs/00_overview/PEAK_TRADE_OVERVIEW.md "
                "on a commit that is not an ancestor of origin/main.",
                [QUOTES_REL],
                used_as_fact=True,
                source_sha=DOC_TIDY_SHA,
                evidence_type="FORENSIC_RAW",
            ),
        ],
        evidence_refs=[
            _understand("RCN-000049"),
            _evaluate("RCN-000049"),
            _adjudicate("RCN-000049"),
            "src/docs/Peak_Trade_OVERVIEW.md",
            QUOTES_REL,
            COMMANDS_REL,
        ],
        remaining_open_questions=[
            "POSSIBLE_SAME_AS src/docs RCN-000053 remains hypothesis; different path families.",
        ],
    )


def _rcn_000050() -> dict[str, Any]:
    return _row(
        "RCN-000050",
        status=PARTIAL,
        missing_proof_question=(
            "Did step29m v2 wrappers retire into parent modules, or was the family removed without replacement?"
        ),
        identity_gap=_gap(
            status="PROVEN_HISTORICAL_EXISTENCE_ON_NON_MAIN_COMMIT",
            statement=(
                f"step29m_*_v2.py exist at {STEP29M_SHA} which is not an ancestor of origin/main. "
                "Record grouping is path-prefix; three STRATEGY_IDs remain distinct internally."
            ),
            used_as_fact=True,
            source=STEP29M_SHA,
            source_sha=STEP29M_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        function_gap=_gap(
            status="PROVEN_HISTORICAL_FUNCTION",
            statement=(
                "Offline-only diagnostic v2 wrappers keeping parent v1 as immutable negative baseline; "
                "no economic evaluation, no runtime authority, no policy relaxation."
            ),
            used_as_fact=True,
            source=_understand("RCN-000050"),
            source_sha=UNDERSTAND_FROZEN_SHA,
            evidence_type="HISTORICAL_INTERMEDIATE",
        ),
        relation_gap=_gap(
            status="PROVEN_DECLARED_PARENT_V1_DEPENDENCY_NOT_IDENTITY",
            statement=(
                "UNDERSTAND binds dependency on src.strategies.bollinger / momentum / trend_following "
                "v1 owners. Current origin/main still has src/strategies/bollinger.py, momentum.py, "
                "trend_following.py. Parent v1 presence is the declared baseline, not the v2 wrapper."
            ),
            used_as_fact=True,
            source="src/strategies/bollinger.py",
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        successor_or_replacement_gap=_gap(
            status="NOT_PROVEN",
            statement=(
                "Parent v1 modules are the baseline the v2 wrappers said they would not mutate. "
                "That is the opposite of v2 retiring into v1. Current src/research/step29m_* "
                "offline economic materializers are different filenames/capabilities."
            ),
            used_as_fact=True,
            source="src/strategies/trend_following.py",
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        current_system_fit_gap=_gap(
            status="UNPROVEN",
            statement="Unique current value of the v2 wrappers versus parent v1 remains unproven.",
            used_as_fact=False,
            source=_evaluate("RCN-000050"),
            source_sha=EVALUATE_FROZEN_SHA,
            evidence_type="OPEN_OR_CONTRADICTORY",
        ),
        claims=[
            _claim(
                "FORENSIC_RAW_FACT",
                f"{STEP29M_SHA} is not an ancestor of origin/main. step29m_bollinger_bands_v2.py "
                "path count is 0 on origin/main and census SHA.",
                [QUOTES_REL, COMMANDS_REL],
                used_as_fact=True,
                source_sha=STEP29M_SHA,
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "CANONICAL_CURRENT_FACT",
                "src/strategies/bollinger.py, momentum.py, and trend_following.py exist on origin/main.",
                [
                    "src/strategies/bollinger.py",
                    "src/strategies/momentum.py",
                    "src/strategies/trend_following.py",
                ],
                used_as_fact=True,
                source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
                evidence_type="CANONICAL_AUTHORITY",
            ),
        ],
        evidence_refs=[
            _understand("RCN-000050"),
            _evaluate("RCN-000050"),
            _adjudicate("RCN-000050"),
            "src/strategies/bollinger.py",
            "src/strategies/momentum.py",
            "src/strategies/trend_following.py",
            QUOTES_REL,
            COMMANDS_REL,
        ],
        remaining_open_questions=[
            "Ledger record groups three strategies by path prefix; they are not fused into one identity.",
        ],
    )


def _rcn_000052() -> dict[str, Any]:
    hub = "docs/webui/observability/OBSERVABILITY_HUB_V0.md"
    return _row(
        "RCN-000052",
        status=CONTRADICTION,
        missing_proof_question=(
            "Was the family restored after the census SHA, or was census presence bound against a different tree?"
        ),
        identity_gap=_gap(
            status="CONTRADICTION_CENSUS_ABSENT_VS_TREE_PRESENT",
            statement=(
                "Ledger discovery.current_presence remains CURRENTLY_ABSENT (census field, not rewritten). "
                "git ls-tree of census SHA 1b52df25 already contains 11 files under "
                "docs/webui/observability, matching origin/main@f9618c73. The family was not restored "
                "after the census SHA; it was already present on the census-bound tree."
            ),
            used_as_fact=True,
            source=COMMANDS_REL,
            source_sha=CENSUS_BOUND_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        function_gap=_gap(
            status="PROVEN_HISTORICAL_AND_CURRENT_HUB_FUNCTION",
            statement=(
                "Observability Hub v0 read-only HTML (GET /observability) plus Paper/Shadow contracts. "
                "Current hub document still exists and states display-only constraints."
            ),
            used_as_fact=True,
            source=hub,
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        relation_gap=_gap(
            status="UNPROVEN_VERSUS_GRAFANA_RCN_000020",
            statement=(
                "POSSIBLE_SAME_AS Grafana docs/observability RCN-000020 remains hypothesis "
                "(different stack/docs generation). Partial deletion of some hub files occurred "
                "inside b5b81728 (market dashboard product stack delete) and files are present "
                "again by census SHA — that collateral history does not rewrite census presence."
            ),
            used_as_fact=False,
            source=_understand("RCN-000052"),
            source_sha=UNDERSTAND_FROZEN_SHA,
            evidence_type="HYPOTHESIS",
        ),
        successor_or_replacement_gap=_gap(
            status="NOT_APPLICABLE",
            statement=(
                "Successor/replacement versus a later family is not the blocking question. The "
                "blocking fact is census CURRENTLY_ABSENT versus tree presence at the census SHA. "
                "NOT_APPLICABLE as replacement claim; contradiction is preserved."
            ),
            used_as_fact=True,
            source=_adjudicate("RCN-000052"),
            source_sha=ADJUDICATE_FROZEN_SHA,
            evidence_type="FORENSIC_RAW",
        ),
        current_system_fit_gap=_gap(
            status="CONTRADICTION_BLOCKS_PRESENCE_NORMALIZATION",
            statement=(
                "Tree presence must not silently overwrite census CURRENTLY_ABSENT. RETAIN_AS_IS "
                "would normalize the contradiction. This pass does not change presence or disposition."
            ),
            used_as_fact=True,
            source="docs/system_atlas/reconciliation/ledger.yaml",
            source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
            evidence_type="OPEN_OR_CONTRADICTORY",
        ),
        claims=[
            _claim(
                "FORENSIC_RAW_FACT",
                "git ls-tree -r --name-only 1b52df25 -- docs/webui/observability lists 11 files "
                "including OBSERVABILITY_HUB_V0.md.",
                [COMMANDS_REL, hub],
                used_as_fact=True,
                source_sha=CENSUS_BOUND_SHA,
                source_path="docs/webui/observability",
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "The 'restored after census SHA' hypothesis is false: census SHA already has the family.",
                [COMMANDS_REL],
                used_as_fact=True,
                source_sha=CENSUS_BOUND_SHA,
                source_path="docs/webui/observability",
                evidence_type="FORENSIC_RAW",
            ),
            _claim(
                "CONTRADICTION",
                "Ledger discovery.current_presence is CURRENTLY_ABSENT while census SHA and current "
                "origin/main both contain docs/webui/observability/. Census field is not rewritten.",
                [
                    "docs/system_atlas/reconciliation/ledger.yaml",
                    hub,
                    COMMANDS_REL,
                ],
                used_as_fact=False,
                source_sha=CENSUS_BOUND_SHA,
                evidence_type="OPEN_OR_CONTRADICTORY",
            ),
            _claim(
                "CANONICAL_CURRENT_FACT",
                "docs/webui/observability/OBSERVABILITY_HUB_V0.md exists on origin/main@f9618c73.",
                [hub],
                used_as_fact=True,
                source_sha=EVIDENCE_RESOLUTION_BOUND_SHA,
                source_path=hub,
                evidence_type="CANONICAL_AUTHORITY",
            ),
        ],
        evidence_refs=[
            _understand("RCN-000052"),
            _evaluate("RCN-000052"),
            _adjudicate("RCN-000052"),
            "docs/system_atlas/reconciliation/ledger.yaml",
            hub,
            QUOTES_REL,
            COMMANDS_REL,
        ],
        remaining_open_questions=[
            "Why did FIND_COMPLETELY bind current_presence=CURRENTLY_ABSENT for a path present on the census SHA?",
            "POSSIBLE_SAME_AS Grafana docs/observability RCN-000020 remains hypothesis.",
        ],
        contradictions=[
            "Census discovery.current_presence=CURRENTLY_ABSENT while git ls-tree census SHA "
            "1b52df25 and origin/main f9618c73 both contain docs/webui/observability/ (11 files).",
        ],
    )
