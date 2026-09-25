"""REEVALUATE_OPEN_RECORDS_PASS_V2 payloads. Additive. Does not rewrite V1 snapshots.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Does not reintegrate, fuse identities, or mutate runtime.
UNDERSTAND / EVALUATE / INTEGRATE_OR_DISPOSITION / OPEN_EVIDENCE_RESOLUTION
and REEVALUATE_OPEN_RECORDS_PASS_V1 snapshots remain frozen.
"""

from __future__ import annotations

from typing import Any

from scripts.ops.system_atlas_v1.evidence_resolution_pass_v1_records import (
    LANDSCAPE_V1_IDS,
    OPEN_IDS,
)
from scripts.ops.system_atlas_v1.reevaluate_open_records_pass_v1_records import (
    ADJUDICATE_FROZEN_SHA,
    INSUFFICIENT,
    REEVALUATE_BOUND_SHA as REEVALUATE_V1_BOUND_SHA,
    REEVALUATE_PASS_ID as REEVALUATE_V1_PASS_ID,
)

REEVALUATE_V2_PASS_ID = "REEVALUATE_OPEN_RECORDS_PASS_V2"
REEVALUATE_V2_BOUND_REF = "origin/main"
REEVALUATE_V2_BOUND_SHA = "7426af2daa4019e7986584a4c53d40b5e182673d"
INPUT_PASS_ID = REEVALUATE_V1_PASS_ID
PREDECESSOR_PASS_ID = REEVALUATE_V1_PASS_ID
PREDECESSOR_BOUND_SHA = REEVALUATE_V1_BOUND_SHA
ADJUDICATE_PASS_ID_FROZEN = "INTEGRATE_OR_DISPOSITION_PASS_V1"

RETAIN = "RETAIN_AS_IS"
ADAPT = "ADAPT_AND_REINTEGRATE"
COVERED = "CAPABILITY_ALREADY_COVERED"
INCOMPATIBLE = "HISTORICALLY_VALID_BUT_INCOMPATIBLE"
REJECT = "REJECT_FOR_CURRENT_SYSTEM"

TARGET_FINAL_IDS = (
    "RCN-000015",
    "RCN-000044",
    "RCN-000045",
    "RCN-000046",
    "RCN-000051",
)
EXPLICIT_REMAIN_OPEN_IDS = ("RCN-000052",)
V2_WRITTEN_RECORD_IDS = TARGET_FINAL_IDS + EXPLICIT_REMAIN_OPEN_IDS
REMAINING_OPEN_IDS = tuple(rid for rid in OPEN_IDS if rid not in TARGET_FINAL_IDS)
OUT_OF_SCOPE_OPEN_IDS = tuple(
    rid for rid in OPEN_IDS if rid not in TARGET_FINAL_IDS and rid not in EXPLICIT_REMAIN_OPEN_IDS
)

RESULTING_DISPOSITIONS = {
    "RCN-000015": INCOMPATIBLE,
    "RCN-000044": REJECT,
    "RCN-000045": REJECT,
    "RCN-000046": REJECT,
    "RCN-000051": REJECT,
    "RCN-000052": INSUFFICIENT,
}

CONTRADICTION_ID_052 = "C052-1"
CENSUS_BOUND_SHA = "1b52df25b99a36b99eed91943c2a203ce84f1cad"
SELECTOR_ADD_SHA = "75eee7bdc501ab4b0ec93812675cd074acb9e2ee"
SELECTOR_REVERT_SHA = "afbae518b67eb1b789c835e219db37f5b15f308b"
CAP23_ADD_SHA = "ecb4484936b6079f90bde252abef77ff129aea8f"
BLOB_ENGINE = "19aaa49470aa766a9f813b672278fe2bcbdac3e3"
BLOB_RESULTS = "cd074be6849834125b0ad5e6e331dc7f2109a1d7"
BLOB_STATS = "7dd32407016f955f2ab4707ae122323a091dab4a"
BLOB_SIZER = "439a60c8176d2990ea8e199443283f2b3e0f9a33"
BLOB_MA = "83bb67757202b250a8273faac1b1e3dd794f8493"
BLOB_README = "8914c7c59c19601053b0965f3a4787abfe68e637"
BLOB_EXPORT_ENGINE = "0d9869d743175c85f3e0286fc45b3b17f9d3d695"
BLOB_EXPORT_SIZER = "04046eb61f426683a2b070ef7e2dd2b27fd1023f"
BLOB_EXPORT_MA = "c89dad61caad99c51bd2e219d66af5956ecf28a9"
BLOB_BACKUP_SIZER = "9a854113d6a230f83fc2c063169761df9d3dc6e0"
BLOB_CURRENT_ENGINE = "a7a54e35bbd81d2ed21ce14a7abbaebcf76de889"
BLOB_CURRENT_SIZER = "c3325deb59eb15a92767b9ca1c7eaa745efc4544"
BLOB_CURRENT_MA = "82e994839b55c7a48258d9864834c96c73781dfd"
NOCH_PARENT = "24001182de0209dabac4d6296bc7738eec442107^"
PTR_README_COMMIT = "cf2253aa60ffdbfd77356e33e611cd85ea53b849"

V1_REC = "docs/system_atlas/reconciliation/reevaluate/records"
V2_EVIDENCE = "docs/system_atlas/reconciliation/evidence/reevaluate_v2"
CMD = f"{V2_EVIDENCE}/commands"
CAP23 = "src/ops/single_selected_future_policy_v1/constants_v1.py"
HUB = "docs/webui/observability/OBSERVABILITY_HUB_V0.md"
APP = "src/webui/app.py"
FAMILIES = "docs/system_atlas/reconciliation/inventories/historical_path_families.yaml"
FIND_V2 = "scripts/ops/system_atlas_v1/census_pass_v2_records.py"


def _claim(cls: str, text: str, evidence: list[str], *, used_as_fact: bool) -> dict[str, Any]:
    return {
        "claim_class": cls,
        "text": text,
        "evidence": list(evidence),
        "used_as_fact": used_as_fact,
    }


def _v1(rid: str) -> str:
    return f"{V1_REC}/{rid}.yaml"


def _understand(rid: str) -> str:
    return f"docs/system_atlas/reconciliation/understand/records/{rid}.yaml"


def _evaluate(rid: str) -> str:
    return f"docs/system_atlas/reconciliation/evaluate/records/{rid}.yaml"


def _adjudicate(rid: str) -> str:
    return f"docs/system_atlas/reconciliation/adjudicate/records/{rid}.yaml"


def _er(rid: str) -> str:
    return f"docs/system_atlas/reconciliation/evidence_resolution/records/{rid}.yaml"


def _base_refs(record_id: str, extra: list[str] | None = None) -> list[str]:
    refs = [
        _understand(record_id),
        _evaluate(record_id),
        _adjudicate(record_id),
        _er(record_id),
        _v1(record_id),
        "docs/system_atlas/reconciliation/reevaluate/pass_v1_status.yaml",
        f"{V2_EVIDENCE}/raw_quotes.yaml",
    ]
    if extra:
        refs.extend(extra)
    seen: set[str] = set()
    unique: list[str] = []
    for ref in refs:
        if ref in seen:
            continue
        seen.add(ref)
        unique.append(ref)
    return unique


def _row(
    record_id: str,
    *,
    disposition_burden_met: bool,
    disposition: str,
    lifecycle_state: str,
    final_disposition_change_performed: bool,
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
    contradiction_id: str = "",
    positive_reason: str = "",
) -> dict[str, Any]:
    if record_id not in OPEN_IDS:
        raise ValueError(f"not_an_open_input_record:{record_id}")
    if record_id not in V2_WRITTEN_RECORD_IDS:
        raise ValueError(f"v2_record_not_in_written_set:{record_id}")
    expected = RESULTING_DISPOSITIONS[record_id]
    if disposition != expected:
        raise ValueError(f"disposition_mismatch:{record_id}:{disposition}!={expected}")
    further = disposition == INSUFFICIENT
    return {
        "record_id": record_id,
        "reevaluate_pass_id": REEVALUATE_V2_PASS_ID,
        "input_pass_id": INPUT_PASS_ID,
        "predecessor_pass_id": PREDECESSOR_PASS_ID,
        "predecessor_bound_sha": PREDECESSOR_BOUND_SHA,
        "reevaluation_attempted": True,
        "adjudication_attempted": True,
        "disposition_burden_met": disposition_burden_met,
        "disposition_candidate": disposition,
        "disposition": disposition,
        "lifecycle_state": lifecycle_state,
        "final_disposition_change_performed": final_disposition_change_performed,
        "identity_merge_performed": False,
        "reintegration_performed": False,
        "reintegration_candidate": False,
        "runtime_mutation_performed": False,
        "further_evidence_required": further,
        "positive_reason": positive_reason,
        "contradiction_id": contradiction_id,
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
        "evidence_refs": _base_refs(record_id, extra_refs),
        "previous_adjudication": {
            "pass_id": REEVALUATE_V1_PASS_ID,
            "bound_sha": REEVALUATE_V1_BOUND_SHA,
            "disposition": INSUFFICIENT,
            "lifecycle_state": "OPEN",
            "adjudicate_pass_id_frozen": ADJUDICATE_PASS_ID_FROZEN,
            "adjudicate_bound_sha_frozen": ADJUDICATE_FROZEN_SHA,
        },
        "bound_against_ref": REEVALUATE_V2_BOUND_REF,
        "bound_against_sha": REEVALUATE_V2_BOUND_SHA,
        "v1_snapshot_frozen": True,
    }


def _rcn_000015() -> dict[str, Any]:
    extra = [
        f"{CMD}/pr_6166_body.txt",
        f"{CMD}/selector_add_revert.txt",
        CAP23,
    ]
    reason = (
        "Owner-adjudicated Master V2 minimal selector (#6165 / 75eee7bdc) had a proven historical "
        "fail-closed-unless-exactly-one purpose and was add-only (10 files), not runtime-consumed, "
        "and created no Cap-2.x importers. Owner reason in #6166 / afbae518b: Cap 2.3 remains "
        "exclusive selection authority; BTC remains excluded. Selector constants do not rewrite "
        "Cap 2.3. Cap 2.3 (ecb44849, 2026-08-02) predates the selector; successor-of-Cap-2.3 is "
        "refuted. Revert is not the rejection reason. The exclusive Cap 2.3 selection-authority "
        "invariant makes the dormant second selector policy incompatible with the current system."
    )
    return _row(
        "RCN-000015",
        disposition_burden_met=True,
        disposition=INCOMPATIBLE,
        lifecycle_state="DISPOSITION_DECIDED",
        final_disposition_change_performed=True,
        positive_reason=reason,
        current_evidence_set=[
            _er("RCN-000015"),
            _v1("RCN-000015"),
            f"{CMD}/pr_6166_body.txt",
            f"{CMD}/selector_add_revert.txt",
            CAP23,
        ],
        historical_function=(
            "Census → structural eligibility → exactly-one-or-none; ranking is not selection "
            "authority; fail-closed if eligible_count != 1."
        ),
        historical_relations=(
            "Selector constants explicitly do not rewrite Cap 2.3. Cap 2.3 predates selector "
            "#6165/#6166. Succession selector→Cap 2.3 is refuted. Add-only; not runtime-consumed."
        ),
        current_system_analogues=(
            "Cap 2.3 single_selected_future_policy_v1 is current exclusive selection owner: "
            "SELECTION_AUTHORITY_ADDED=True; ranking hysteresis/min holding."
        ),
        identity_status="PROVEN_DISTINCT_FROM_CAP_2_3",
        successor_status="REFUTED_AS_SUCCESSOR_OF_CAP_2_3",
        replacement_status="NOT_A_REPLACEMENT_OF_CAP_2_3",
        current_value_status="HISTORICALLY_VALID_NOT_CURRENTLY_ADOPTABLE",
        current_compatibility_status=("INCOMPATIBLE_WITH_EXCLUSIVE_CAP_2_3_SELECTION_AUTHORITY"),
        contradictions=[],
        unresolved_gaps=[
            "None required for this terminal class: Owner exclusive-authority reason is bound.",
        ],
        evaluation_result=(
            "Burden for HISTORICALLY_VALID_BUT_INCOMPATIBLE is met. Historical purpose is proven. "
            "Owner #6166 states Cap 2.3 remains exclusive selection authority. Selector does not "
            "rewrite Cap 2.3 and is not its successor. Revert is not REJECT. INCOMPATIBLE is the "
            "terminal class; historical legitimacy remains documented."
        ),
        alternatives_rejected=[
            f"{RETAIN}: selector path CURRENTLY_ABSENT after revert; absence is not retain",
            f"{COVERED}: Cap 2.3 ranking/hysteresis selection is a distinct later exclusive owner, not proven coverage of fail-closed-unless-exactly-one",
            f"{ADAPT}: reintegration is not authorized; exclusive Cap 2.3 authority forbids a second selector policy",
            f"{REJECT}: revert #6166 is not a positive rejection reason; historical purpose remains legitimate",
            "Declaring SAME_AS / successor of single_selected_future_policy_v1: refuted, not a merge",
        ],
        claims=[
            _claim(
                "ADJUDICATED_CONCLUSION",
                "Master V2 minimal selector is historically valid and incompatible with exclusive Cap 2.3 selection authority.",
                extra,
                used_as_fact=True,
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "PR #6166 Owner decision (A+1): Cap 2.3 remains exclusive selection authority. BTC remains excluded. #6165 was isolated add-only (10 files), not runtime-consumed, and created no Cap-2.x / host importers.",
                [f"{CMD}/pr_6166_body.txt"],
                used_as_fact=True,
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "Selector package states it does not rewrite Cap 2.3 stickiness/ranking selection.",
                [f"{CMD}/selector_add_revert.txt"],
                used_as_fact=True,
            ),
            _claim(
                "CANONICAL_CURRENT_FACT",
                "Cap 2.3 remains current SINGLE_SELECTED_FUTURE selection owner with SELECTION_AUTHORITY_ADDED=True.",
                [CAP23],
                used_as_fact=True,
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "Cap 2.3 was added 2026-08-02 (#5642 / ecb44849) before selector add 2026-08-30 (#6165). Successor-of-Cap-2.3 is refuted.",
                [f"{CMD}/selector_add_revert.txt", CAP23],
                used_as_fact=True,
            ),
        ],
        extra_refs=extra,
    )


def _rcn_000044() -> dict[str, Any]:
    extra = [f"{CMD}/placeholder_blobs.txt", "src/backtest/engine.py"]
    reason = (
        "Nested PeakTradeRepo backtest engine/results/stats blobs are one-line placeholders "
        f"(engine {BLOB_ENGINE[:8]}='# Engine placeholder'; results {BLOB_RESULTS[:8]}="
        f"'# Results placeholder'; stats {BLOB_STATS[:8]}='# Stats placeholder'). Export engine "
        f"{BLOB_EXPORT_ENGINE[:8]} and current src/backtest/engine.py {BLOB_CURRENT_ENGINE[:8]} "
        "are blob-distinct. This nested snapshot is not a current-system capability to adopt. "
        "README narrative is not used in place of blob content. Deletion is not the reject reason."
    )
    return _row(
        "RCN-000044",
        disposition_burden_met=True,
        disposition=REJECT,
        lifecycle_state="DISPOSITION_DECIDED",
        final_disposition_change_performed=True,
        positive_reason=reason,
        current_evidence_set=[
            _er("RCN-000044"),
            _understand("RCN-000044"),
            f"{CMD}/placeholder_blobs.txt",
            "src/backtest/engine.py",
        ],
        historical_function="Nested archive backtest engine/results/stats snapshot whose recovered blobs are placeholders.",
        historical_relations="Inner component of RCN-000014; not fused. Blob-distinct from export and current engine.",
        current_system_analogues="Later src/backtest/engine.py is a distinct blob; not SAME_AS.",
        identity_status="PLACEHOLDER_BLOB_DISTINCT_FROM_EXPORT_AND_CURRENT",
        successor_status="NOT_PROVEN",
        replacement_status="NOT_PROVEN",
        current_value_status="NO_INDEPENDENT_CURRENT_CAPABILITY",
        current_compatibility_status="REJECT_PLACEHOLDER_NOT_ADOPTABLE",
        contradictions=[],
        unresolved_gaps=[
            "None required for REJECT: placeholder blob content is the positive reason.",
        ],
        evaluation_result=(
            "Burden for REJECT_FOR_CURRENT_SYSTEM is met from blob content, not from absence. "
            "Nested engine/results/stats are placeholders. Export and current engines are "
            "blob-distinct. No identity merge with RCN-000014."
        ),
        alternatives_rejected=[
            f"{RETAIN}: CURRENTLY_ABSENT; placeholder is not a retained current artifact",
            f"{COVERED}: later src/backtest not proven SAME_AS; namesake is not coverage",
            f"{ADAPT}: placeholder has no independent current value to adapt",
            f"{INCOMPATIBLE}: placeholder is not a historically valid implemented capability that conflicts with current invariants",
            "REJECT because deleted: deletion is not a positive rejection reason",
            "Using PeakTradeRepo README as this record's purpose: forbidden; blob content is authoritative",
        ],
        claims=[
            _claim(
                "ADJUDICATED_CONCLUSION",
                "Nested backtest engine/results/stats are placeholders and are rejected for the current system.",
                extra,
                used_as_fact=True,
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                f"blob:{BLOB_ENGINE} = '# Engine placeholder'; blob:{BLOB_RESULTS} = '# Results placeholder'; blob:{BLOB_STATS} = '# Stats placeholder'.",
                [f"{CMD}/placeholder_blobs.txt"],
                used_as_fact=True,
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                f"Export engine blob:{BLOB_EXPORT_ENGINE} and current src/backtest/engine.py blob:{BLOB_CURRENT_ENGINE} are distinct from nested placeholders.",
                [f"{CMD}/placeholder_blobs.txt", "src/backtest/engine.py"],
                used_as_fact=True,
            ),
        ],
        extra_refs=extra,
    )


def _rcn_000045() -> dict[str, Any]:
    extra = [f"{CMD}/placeholder_blobs.txt", "src/risk/position_sizer.py"]
    reason = (
        "Nested PeakTradeRepo position_sizer blob is the one-line placeholder "
        f"'# Position sizer placeholder' ({BLOB_SIZER[:8]}). Backup "
        f"{BLOB_BACKUP_SIZER[:8]}, current src/risk/position_sizer.py {BLOB_CURRENT_SIZER[:8]}, "
        f"and export position_sizing {BLOB_EXPORT_SIZER[:8]} are blob-distinct. "
        "CAND:position_sizer_old_backup is related, not SAME_AS. No identity merge. "
        "Placeholder is not a current-system capability to adopt."
    )
    return _row(
        "RCN-000045",
        disposition_burden_met=True,
        disposition=REJECT,
        lifecycle_state="DISPOSITION_DECIDED",
        final_disposition_change_performed=True,
        positive_reason=reason,
        current_evidence_set=[
            _er("RCN-000045"),
            _understand("RCN-000045"),
            f"{CMD}/placeholder_blobs.txt",
            "src/risk/position_sizer.py",
            "docs/system_atlas/reconciliation/discovery_candidates.yaml",
        ],
        historical_function="Nested archive position_sizer snapshot whose recovered blob is a placeholder.",
        historical_relations="Inner component of RCN-000014; not fused. Distinct from backup/current/export sizers.",
        current_system_analogues="Later src/risk/position_sizer.py is a distinct blob; CAND:position_sizer_old_backup is not SAME_AS.",
        identity_status="PLACEHOLDER_BLOB_DISTINCT_FROM_BACKUP_EXPORT_AND_CURRENT",
        successor_status="NOT_PROVEN",
        replacement_status="NOT_PROVEN",
        current_value_status="NO_INDEPENDENT_CURRENT_CAPABILITY",
        current_compatibility_status="REJECT_PLACEHOLDER_NOT_ADOPTABLE",
        contradictions=[],
        unresolved_gaps=[
            "CAND:position_sizer_old_backup remains a candidate, not a ledger identity merge.",
        ],
        evaluation_result=(
            "Burden for REJECT_FOR_CURRENT_SYSTEM is met from nested placeholder blob content. "
            "Backup/current/export are blob-distinct. Identity merge is forbidden and was not performed."
        ),
        alternatives_rejected=[
            f"{RETAIN}: CURRENTLY_ABSENT; placeholder is not retained",
            f"{COVERED}: later sizer modules are not proven SAME_AS",
            f"{ADAPT}: placeholder has no independent current value to adapt",
            f"{INCOMPATIBLE}: placeholder is not a historically valid implemented sizer that conflicts with current invariants",
            "REJECT because deleted: deletion is not a positive rejection reason",
            "SAME_AS CAND:position_sizer_old_backup or current sizer: blob-distinct; merge forbidden",
        ],
        claims=[
            _claim(
                "ADJUDICATED_CONCLUSION",
                "Nested position_sizer is a placeholder and is rejected for the current system.",
                extra,
                used_as_fact=True,
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                f"blob:{BLOB_SIZER} = '# Position sizer placeholder'. Distinct from backup {BLOB_BACKUP_SIZER}, export {BLOB_EXPORT_SIZER}, current {BLOB_CURRENT_SIZER}.",
                [
                    f"{CMD}/placeholder_blobs.txt",
                    "docs/system_atlas/reconciliation/discovery_candidates.yaml",
                ],
                used_as_fact=True,
            ),
        ],
        extra_refs=extra,
    )


def _rcn_000046() -> dict[str, Any]:
    extra = [f"{CMD}/placeholder_blobs.txt", "src/strategies/ma_crossover.py"]
    reason = (
        "Nested PeakTradeRepo MA strategy blob is the one-line placeholder "
        f"'# MA Strategy placeholder' ({BLOB_MA[:8]}). Export MA {BLOB_EXPORT_MA[:8]} and "
        f"current src/strategies/ma_crossover.py {BLOB_CURRENT_MA[:8]} are blob-distinct. "
        "README-versus-placeholder contradiction in the PeakTradeRepo tree is preserved and "
        "is not resolved by substituting README narrative for blob content."
    )
    return _row(
        "RCN-000046",
        disposition_burden_met=True,
        disposition=REJECT,
        lifecycle_state="DISPOSITION_DECIDED",
        final_disposition_change_performed=True,
        positive_reason=reason,
        current_evidence_set=[
            _er("RCN-000046"),
            _understand("RCN-000046"),
            f"{CMD}/placeholder_blobs.txt",
            "src/strategies/ma_crossover.py",
        ],
        historical_function="Nested archive MA strategy snapshot whose recovered blob is a placeholder.",
        historical_relations="Inner component of RCN-000014; not fused. Distinct from export/current MA.",
        current_system_analogues="Later src/strategies/ma_crossover.py is a distinct blob; not SAME_AS.",
        identity_status="PLACEHOLDER_BLOB_DISTINCT_FROM_EXPORT_AND_CURRENT",
        successor_status="NOT_PROVEN",
        replacement_status="NOT_PROVEN",
        current_value_status="NO_INDEPENDENT_CURRENT_CAPABILITY",
        current_compatibility_status="REJECT_PLACEHOLDER_NOT_ADOPTABLE",
        contradictions=[
            "PeakTradeRepo README describes MA strategy capability while nested blob is '# MA Strategy placeholder'. Contradiction is preserved; README is not substituted for blob content.",
        ],
        unresolved_gaps=[
            "README-versus-placeholder contradiction remains documented and is not normalized.",
        ],
        evaluation_result=(
            "Burden for REJECT_FOR_CURRENT_SYSTEM is met from nested placeholder blob content. "
            "Export/current MA blobs are distinct. README contradiction is preserved."
        ),
        alternatives_rejected=[
            f"{RETAIN}: CURRENTLY_ABSENT; placeholder is not retained",
            f"{COVERED}: later MA module is not proven SAME_AS",
            f"{ADAPT}: placeholder has no independent current value to adapt",
            f"{INCOMPATIBLE}: placeholder is not a historically valid implemented MA strategy that conflicts with current invariants",
            "REJECT because deleted: deletion is not a positive rejection reason",
            "Using PeakTradeRepo README as this record's implemented purpose: forbidden; blob content is authoritative",
        ],
        claims=[
            _claim(
                "ADJUDICATED_CONCLUSION",
                "Nested MA strategy is a placeholder and is rejected for the current system.",
                extra,
                used_as_fact=True,
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                f"blob:{BLOB_MA} = '# MA Strategy placeholder'. Distinct from export {BLOB_EXPORT_MA} and current {BLOB_CURRENT_MA}.",
                [f"{CMD}/placeholder_blobs.txt", "src/strategies/ma_crossover.py"],
                used_as_fact=True,
            ),
            _claim(
                "CONTRADICTION",
                "PeakTradeRepo README capability narrative versus nested MA placeholder blob is preserved and not used as fact for identity.",
                [_understand("RCN-000046"), f"{CMD}/placeholder_blobs.txt"],
                used_as_fact=False,
            ),
        ],
        extra_refs=extra,
    )


def _rcn_000051() -> dict[str, Any]:
    extra = [
        f"{CMD}/placeholder_blobs.txt",
        "docs/system_atlas/reconciliation/inventories/inner_archive_peaktraderepo.yaml",
    ]
    reason = (
        f"Last attested archive/noch_einordnen tree contains only README.md whose blob "
        f"{BLOB_README[:8]} is SAME_BLOB_AS archive/PeakTradeRepo/README.md at "
        f"{PTR_README_COMMIT}. Queued duplicate document; not an independent current capability. "
        "Folder identity merge with RCN-000014 is not performed. CAPABILITY_ALREADY_COVERED is "
        "rejected because RCN-000014 is itself OPEN/ABSENT, not a current covering capability."
    )
    return _row(
        "RCN-000051",
        disposition_burden_met=True,
        disposition=REJECT,
        lifecycle_state="DISPOSITION_DECIDED",
        final_disposition_change_performed=True,
        positive_reason=reason,
        current_evidence_set=[
            _er("RCN-000051"),
            _understand("RCN-000051"),
            f"{CMD}/placeholder_blobs.txt",
        ],
        historical_function="Queued archive/noch_einordnen folder whose last attested content is one README.",
        historical_relations=(
            f"README blob {BLOB_README} is SAME_BLOB_AS PeakTradeRepo README. POSSIBLE_SAME_AS "
            "RCN-000014 remains hypothesis for folder identity; SAME_AS / folder merge not performed."
        ),
        current_system_analogues="No independent current capability. Duplicate queued document only.",
        identity_status="QUEUED_DUPLICATE_README_NOT_FOLDER_MERGE",
        successor_status="NOT_APPLICABLE",
        replacement_status="NOT_PROVEN",
        current_value_status="NO_INDEPENDENT_CURRENT_CAPABILITY",
        current_compatibility_status="REJECT_QUEUED_DUPLICATE_DOCUMENT",
        contradictions=[],
        unresolved_gaps=[
            "Folder identity versus RCN-000014 remains unmerged by design.",
        ],
        evaluation_result=(
            "Burden for REJECT_FOR_CURRENT_SYSTEM is met: last attested content is a queued "
            "duplicate README (SAME_BLOB_AS PeakTradeRepo README), not a standalone capability. "
            "Identity merge is not performed."
        ),
        alternatives_rejected=[
            f"{RETAIN}: CURRENTLY_ABSENT; queued duplicate is not retained",
            f"{COVERED}: RCN-000014 is OPEN/ABSENT and is not a current covering capability",
            f"{ADAPT}: duplicate README has no independent current value to adapt",
            f"{INCOMPATIBLE}: queued duplicate document is not a historically distinct capability that conflicts with current invariants",
            "Folder identity merge into RCN-000014: forbidden; SAME_BLOB_AS of README is not SAME_AS of records",
            "SAME_AS RCN-000014: not proven; merge not performed",
        ],
        claims=[
            _claim(
                "ADJUDICATED_CONCLUSION",
                "archive/noch_einordnen is a queued duplicate README and is rejected for the current system. Folder identity is not merged.",
                extra,
                used_as_fact=True,
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                f"blob:{BLOB_README} is the PeakTradeRepo README blob and the only path under {NOCH_PARENT}:archive/noch_einordnen.",
                [f"{CMD}/placeholder_blobs.txt"],
                used_as_fact=True,
            ),
        ],
        extra_refs=extra,
    )


def _rcn_000052() -> dict[str, Any]:
    extra = [
        f"{CMD}/rcn_000052_presence_scope.txt",
        HUB,
        APP,
        FAMILIES,
        FIND_V2,
        "docs/system_atlas/reconciliation/ledger.yaml",
    ]
    reason = (
        "Contradiction C052-1 remains unresolved. FIND bound CURRENTLY_ABSENT to a D/R-deleted "
        "31-file family while 11 hub files existed at census SHA and exist now. GET /observability "
        "is currently wired. Record identity is mixed and not split. Presence rewrite and RETAIN_AS_IS "
        "are forbidden while the contradiction is not adjudicated. SAME_AS RCN-000020 is forbidden."
    )
    return _row(
        "RCN-000052",
        disposition_burden_met=False,
        disposition=INSUFFICIENT,
        lifecycle_state="OPEN",
        final_disposition_change_performed=False,
        positive_reason=reason,
        contradiction_id=CONTRADICTION_ID_052,
        current_evidence_set=[
            _er("RCN-000052"),
            _v1("RCN-000052"),
            f"{CMD}/rcn_000052_presence_scope.txt",
            HUB,
            APP,
            FAMILIES,
            FIND_V2,
        ],
        historical_function="Observability Hub v0 read-only HTML plus Paper/Shadow contracts; census also bound a 31-file deleted family under the same prefix.",
        historical_relations=(
            "Census CURRENTLY_ABSENT vs 11 hub files present at census SHA and origin/main. "
            "POSSIBLE_SAME_AS Grafana RCN-000020 remains hypothesis. No SAME_AS. No split."
        ),
        current_system_analogues=(
            f"{HUB} exists on origin/main. GET /observability is wired in {APP}."
        ),
        identity_status="CENSUS_TREE_CONTRADICTION_MIXED_IDENTITY_NOT_SPLIT",
        successor_status="NOT_APPLICABLE",
        replacement_status="NOT_PROVEN",
        current_value_status="UNPROVEN_WHILE_PRESENCE_CONTRADICTED",
        current_compatibility_status="CONTRADICTION_BLOCKS_PRESENCE_NORMALIZATION",
        contradictions=[
            f"{CONTRADICTION_ID_052}: FIND band CURRENTLY_ABSENT to a D/R-deleted 31-file family while git ls-tree census SHA {CENSUS_BOUND_SHA} and origin/main {REEVALUATE_V2_BOUND_SHA} both contain 11 docs/webui/observability hub files. SCOPE_RECONSTRUCTED_NOT_NORMALIZED. C052_CONTRADICTION_RESOLVED=false.",
        ],
        unresolved_gaps=[
            "Why did FIND_COMPLETELY bind current_presence=CURRENTLY_ABSENT for a path present on the census SHA?",
            "31-file D/R family versus 11 remaining hub files is mixed identity and is not split.",
            "POSSIBLE_SAME_AS Grafana docs/observability RCN-000020 remains hypothesis.",
        ],
        evaluation_result=(
            "Fail-closed: C052-1 is preserved and not semantically resolved. RETAIN_AS_IS from tree "
            "presence would silently overwrite CURRENTLY_ABSENT. Presence rewrite is forbidden. "
            "No split. No SAME_AS with RCN-000020. INSUFFICIENT_EVIDENCE remains OPEN."
        ),
        alternatives_rejected=[
            f"{RETAIN}: would normalize census CURRENTLY_ABSENT into a currently retained identity",
            f"{COVERED}: present hub docs are not proven identical to the census-deleted 31-file family",
            f"{ADAPT}: contradiction blocks treating the census identity as an adaptation candidate",
            f"{INCOMPATIBLE}: tree presence is not incompatibility",
            f"{REJECT}: census said deleted is not a positive reject reason",
            "Rewriting discovery.current_presence: forbidden; census field is historical discovery fact",
            "Split into hub-present versus deleted-family records: not authorized",
            "SAME_AS RCN-000020: forbidden; POSSIBLE_SAME_AS remains hypothesis",
        ],
        claims=[
            _claim(
                "ADJUDICATED_CONCLUSION",
                "docs/webui/observability: C052-1 unresolved; stronger class burden unmet. INSUFFICIENT_EVIDENCE remains OPEN.",
                extra,
                used_as_fact=True,
            ),
            _claim(
                "CONTRADICTION",
                f"{CONTRADICTION_ID_052}: Ledger discovery.current_presence is CURRENTLY_ABSENT while census SHA and current origin/main both contain 11 hub files. Census field is not rewritten. SCOPE_RECONSTRUCTED_NOT_NORMALIZED.",
                extra,
                used_as_fact=False,
            ),
            _claim(
                "CANONICAL_CURRENT_FACT",
                f"{HUB} exists on origin/main@{REEVALUATE_V2_BOUND_SHA}. GET /observability is wired.",
                [HUB, APP],
                used_as_fact=True,
            ),
            _claim(
                "FORENSIC_RAW_FACT",
                "inventories/historical_path_families.yaml counts deleted_docs_families docs/webui/observability as 31 (git log --diff-filter=D/R). FIND v2 hardcoded CURRENTLY_ABSENT and '31 files in census'.",
                [FAMILIES, FIND_V2],
                used_as_fact=True,
            ),
        ],
        extra_refs=extra,
    )


def reevaluate_open_records_pass_v2() -> list[dict[str, Any]]:
    rows = [
        _rcn_000015(),
        _rcn_000044(),
        _rcn_000045(),
        _rcn_000046(),
        _rcn_000051(),
        _rcn_000052(),
    ]
    ids = tuple(row["record_id"] for row in rows)
    if ids != V2_WRITTEN_RECORD_IDS:
        raise ValueError(f"v2_written_id_order_mismatch:{ids}")
    if len(REMAINING_OPEN_IDS) != 30:
        raise ValueError(f"remaining_open_count_mismatch:{len(REMAINING_OPEN_IDS)}")
    if len(OUT_OF_SCOPE_OPEN_IDS) != 29:
        raise ValueError(f"out_of_scope_open_count_mismatch:{len(OUT_OF_SCOPE_OPEN_IDS)}")
    if len(LANDSCAPE_V1_IDS) != 15:
        raise ValueError("landscape_v1_count_mismatch")
    return rows
