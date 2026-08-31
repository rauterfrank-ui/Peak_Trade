"""Historical reconsolidation ledger validation.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Governance/evidence only. Not runtime authorization.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

import yaml

from scripts.ops.system_atlas_v1.constants_v1 import (
    RECONCILIATION_AUTHORITY,
    RECONCILIATION_RELATIVE_ROOT,
    RECONCILIATION_SCHEMA_VERSION,
)

RECONCILIATION_SOURCE_FILES = (
    "GOVERNANCE_V1.yaml",
    "census_status.yaml",
    "search_anchors.yaml",
    "ledger.yaml",
    "schema.yaml",
)
CENSUS_ARTIFACT_FILES = (
    "search_surfaces.yaml",
    "coverage.yaml",
    "discovery_candidates.yaml",
    "relations.yaml",
)
ALLOWED_RELATION_TYPES = frozenset(
    {
        "POSSIBLE_SAME_AS",
        "DEPENDS_ON",
        "SUPERSEDES",
        "REPLACED_BY",
        "CONSUMED_BY",
        "IMPLEMENTS",
        "CONFLICTS_WITH",
        "COVERED_BY",
        "PRODUCES_FOR",
        "CONSUMES_FROM",
        "WRAPS",
        "ORCHESTRATES",
        "GATES",
        "SELECTS",
        "BINDS",
        "CALLS",
        "DERIVES_FROM",
        "RENAMED_TO",
        "PATH_MOVED_OR_RENAMED_TO",
        "SPLIT_INTO",
        "MERGED_INTO",
        "SAME_BLOB_AS",
        "REFERENCES",
        "IMPORTS",
        "TESTS",
        "DOCUMENTS",
        "ARCHIVES",
        "IMPORTED_BY",
        "CALLED_BY",
        "TESTED_BY",
        "CONFIGURES",
        "REGISTERED_AS",
        "MOVED_TO",
    }
)
ALLOWED_CURRENT_PRESENCE = frozenset(
    {
        "CURRENTLY_PRESENT",
        "CURRENTLY_ABSENT",
        "CURRENTLY_PARTIAL",
        "CURRENT_IDENTITY_UNRESOLVED",
    }
)
ALLOWED_EVIDENCE_RESOLUTION_STATUSES = frozenset(
    {
        "EVIDENCE_GAP_RESOLVED",
        "EVIDENCE_GAP_PARTIALLY_RESOLVED",
        "EVIDENCE_GAP_UNRESOLVED",
        "CONTRADICTION_DISCOVERED",
    }
)
EVIDENCE_RESOLUTION_REQUIRED_GAPS = (
    "identity_gap",
    "function_gap",
    "relation_gap",
    "successor_or_replacement_gap",
    "current_system_fit_gap",
)
REEVALUATE_REQUIRED_TEXT_FIELDS = (
    "historical_function",
    "historical_relations",
    "current_system_analogues",
    "identity_status",
    "successor_status",
    "replacement_status",
    "current_value_status",
    "current_compatibility_status",
    "evaluation_result",
)
CENSUS_STARTED_STATUSES = frozenset(
    {
        "CENSUS_IN_PROGRESS",
        "CENSUS_SCOPE_BOUND",
        "CENSUS_EXHAUSTION_PROVEN",
        "CENSUS_CLOSED",
    }
)

REQUIRED_INITIAL_ANCHOR_NAMES = ("Landscape", "Master V2", "Double Play")
ID_PATTERN = re.compile(r"^RCN-[0-9]{6}$")
ANCHOR_ID_PATTERN = re.compile(r"^ANCHOR:[a-z0-9_]+$")

FACT_CLAIM_CLASSES = frozenset(
    {
        "CANONICAL_CURRENT_FACT",
        "FORENSIC_RAW_FACT",
        "HISTORICAL_FACT",
        "ADJUDICATED_CONCLUSION",
    }
)
NON_FACT_CLAIM_CLASSES = frozenset(
    {
        "INTERPRETATION",
        "HYPOTHESIS",
        "OPEN_QUESTION",
        "CONTRADICTION",
    }
)

DISPOSITION_TO_POST_STATES = {
    "RETAIN_AS_IS": frozenset({"DISPOSITION_DECIDED", "REINTEGRATED"}),
    "ADAPT_AND_REINTEGRATE": frozenset({"DISPOSITION_DECIDED", "REINTEGRATED"}),
    "CAPABILITY_ALREADY_COVERED": frozenset({"DISPOSITION_DECIDED", "COVERED"}),
    "HISTORICALLY_VALID_BUT_INCOMPATIBLE": frozenset({"DISPOSITION_DECIDED", "INCOMPATIBLE"}),
    "REJECT_FOR_CURRENT_SYSTEM": frozenset({"DISPOSITION_DECIDED", "REJECTED"}),
    "INSUFFICIENT_EVIDENCE": frozenset({"ADJUDICATED", "DISPOSITION_DECIDED", "OPEN"}),
}

FINAL_DISPOSITIONS_REQUIRE_PURPOSE = frozenset(
    {
        "RETAIN_AS_IS",
        "ADAPT_AND_REINTEGRATE",
        "CAPABILITY_ALREADY_COVERED",
        "HISTORICALLY_VALID_BUT_INCOMPATIBLE",
        "REJECT_FOR_CURRENT_SYSTEM",
    }
)


class ReconciliationValidationError(ValueError):
    """Reconciliation governance or ledger integrity failure."""


def reconciliation_root(repo_root: Path) -> Path:
    return repo_root / RECONCILIATION_RELATIVE_ROOT


def _read_yaml(path: Path) -> Any:
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    return loaded if loaded is not None else {}


def load_reconciliation_v1(*, repo_root: Path) -> dict[str, Any]:
    root = reconciliation_root(repo_root)
    if not root.is_dir():
        raise ReconciliationValidationError("RECONCILIATION_TREE_MISSING")
    payload: dict[str, Any] = {
        "reconciliation_authority": RECONCILIATION_AUTHORITY,
        "schema_version": RECONCILIATION_SCHEMA_VERSION,
        "root": str(root),
        "records": {},
    }
    for rel in RECONCILIATION_SOURCE_FILES:
        path = root / rel
        if not path.is_file():
            raise ReconciliationValidationError(f"RECONCILIATION_SOURCE_MISSING:{rel}")
        payload["records"][rel] = _read_yaml(path)
    census_status = str(
        (payload["records"].get("census_status.yaml") or {}).get("census_status") or ""
    )
    for rel in CENSUS_ARTIFACT_FILES:
        path = root / rel
        if path.is_file():
            payload["records"][rel] = _read_yaml(path)
        elif census_status in CENSUS_STARTED_STATUSES:
            raise ReconciliationValidationError(f"RECONCILIATION_CENSUS_ARTIFACT_MISSING:{rel}")
    return payload


def _require_schema_version(row: dict[str, Any], *, source: str) -> None:
    version = str(row.get("schema_version") or "")
    if version != RECONCILIATION_SCHEMA_VERSION:
        raise ReconciliationValidationError(
            f"RECONCILIATION_SCHEMA_VERSION_INVALID:{source}:{version}"
        )


def _as_bool(value: Any, *, field: str) -> bool:
    if value is True:
        return True
    if value is False:
        return False
    raise ReconciliationValidationError(f"RECONCILIATION_BOOL_REQUIRED:{field}")


def _claims_of(record: dict[str, Any]) -> list[dict[str, Any]]:
    claims = list(record.get("claims") or [])
    for section in (
        "discovery",
        "understanding",
        "current_comparison",
        "adjudication",
        "audit",
        "evidence_resolution",
        "reevaluate",
    ):
        block = record.get(section) or {}
        if isinstance(block, dict):
            claims.extend(list(block.get("claims") or []))
    return claims


def _validate_governance(gov: dict[str, Any]) -> None:
    _require_schema_version(gov, source="GOVERNANCE_V1.yaml")
    if gov.get("creates_productive_authority") is True:
        raise ReconciliationValidationError("RECONCILIATION_RAISED_PRODUCTIVE_AUTHORITY")
    if gov.get("creates_runtime_authorization") is True:
        raise ReconciliationValidationError("RECONCILIATION_RAISED_RUNTIME_AUTHORIZATION")
    sequence = [str(x) for x in (gov.get("sequence") or [])]
    expected = [
        "FIND_COMPLETELY",
        "UNDERSTAND",
        "EVALUATE_INDIVIDUALLY",
        "INTEGRATE_OR_DISPOSITION",
    ]
    if sequence != expected:
        raise ReconciliationValidationError("RECONCILIATION_SEQUENCE_INVALID")
    rules = gov.get("epistemic_rules") or {}
    required_true = (
        "HISTORICAL_EXISTENCE_IS_NOT_AUTOMATIC_AUTHORITY",
        "HISTORICAL_EXISTENCE_IS_NOT_AUTOMATIC_REINTEGRATION",
        "HISTORICAL_EXISTENCE_IS_NOT_REJECTION_GROUNDS",
        "LOST_COMPONENT_IS_INVESTIGATION_TRIGGER",
        "MEMORY_OF_COMPONENT_NAMES_IS_NOT_CENSUS_BOUNDARY",
        "UNKNOWN_HISTORICAL_COMPONENTS_MUST_BE_SEARCHABLE",
        "NO_COMPONENT_DISPOSITION_BEFORE_PURPOSE_UNDERSTOOD",
        "NO_REINTEGRATION_BEFORE_CURRENT_SYSTEM_COMPATIBILITY_ASSESSED",
        "NO_REJECTION_WITHOUT_POSITIVE_REASON",
        "INSUFFICIENT_EVIDENCE_REMAINS_OPEN",
        "CURRENT_ABSENCE_DOES_NOT_PROVE_HISTORICAL_IRRELEVANCE",
        "CURRENT_REPLACEMENT_MUST_BE_PROVEN_NOT_ASSUMED",
        "HISTORICAL_PURPOSE_AND_CURRENT_FIT_ARE_SEPARATE_QUESTIONS",
        "CENSUS_COMPLETENESS_MUST_BE_PROVEN_NOT_INFERRED",
        "UNPROVEN_COMPLETENESS_REMAINS_UNPROVEN",
        "NO_SILENT_NORMALIZATION",
        "NO_MISSING_FACT_RECONSTRUCTION",
        "CONTRADICTIONS_ARE_PRESERVED_AS_SYSTEM_FACTS",
    )
    for key in required_true:
        if rules.get(key) is not True:
            raise ReconciliationValidationError(f"EPISTEMIC_RULE_UNBOUND:{key}")
    taxonomy = gov.get("disposition_taxonomy") or {}
    expected_disp = {
        "RETAIN_AS_IS",
        "ADAPT_AND_REINTEGRATE",
        "CAPABILITY_ALREADY_COVERED",
        "HISTORICALLY_VALID_BUT_INCOMPATIBLE",
        "INSUFFICIENT_EVIDENCE",
        "REJECT_FOR_CURRENT_SYSTEM",
    }
    if set(taxonomy) != expected_disp:
        raise ReconciliationValidationError("DISPOSITION_TAXONOMY_INVALID")
    claim_classes = set(str(x) for x in (gov.get("claim_classes") or []))
    if claim_classes != (FACT_CLAIM_CLASSES | NON_FACT_CLAIM_CLASSES):
        raise ReconciliationValidationError("CLAIM_CLASSES_INVALID")
    if gov.get("hypothesis_must_not_serialize_as_fact") is not True:
        raise ReconciliationValidationError("HYPOTHESIS_FACT_RULE_UNBOUND")
    if gov.get("mapping_does_not_mutate_atlas_ontology") is not True:
        raise ReconciliationValidationError("ATLAS_ONTOLOGY_MAPPING_UNBOUND")
    pattern = str((gov.get("id_schema") or {}).get("pattern") or "")
    if pattern != ID_PATTERN.pattern:
        raise ReconciliationValidationError("ID_PATTERN_UNBOUND")


def _validate_census(census: dict[str, Any], gov: dict[str, Any]) -> None:
    _require_schema_version(census, source="census_status.yaml")
    allowed = {str(x) for x in (gov.get("census_status_values") or [])}
    status = str(census.get("census_status") or "")
    if status not in allowed:
        raise ReconciliationValidationError(f"CENSUS_STATUS_UNKNOWN:{status}")
    exhaustion = _as_bool(census.get("census_exhaustion_proven"), field="census_exhaustion_proven")
    closed = _as_bool(census.get("census_closed"), field="census_closed")
    universe_bound = _as_bool(census.get("search_universe_bound"), field="search_universe_bound")
    if closed and status != "CENSUS_CLOSED":
        raise ReconciliationValidationError("CENSUS_CLOSED_FLAG_STATUS_MISMATCH")
    if status == "CENSUS_CLOSED" and not closed:
        raise ReconciliationValidationError("CENSUS_CLOSED_STATUS_WITHOUT_FLAG")
    if closed:
        if not exhaustion:
            raise ReconciliationValidationError("CENSUS_CLOSED_WITHOUT_EXHAUSTION")
        if not universe_bound:
            raise ReconciliationValidationError("CENSUS_CLOSED_WITHOUT_SEARCH_UNIVERSE")
    if status == "CENSUS_NOT_STARTED":
        if exhaustion or closed or universe_bound:
            raise ReconciliationValidationError("CENSUS_NOT_STARTED_NOT_EMPTY")
        if census.get("historical_census_performed") is True:
            raise ReconciliationValidationError("CENSUS_NOT_STARTED_BUT_PERFORMED")


def _validate_anchors(anchors_doc: dict[str, Any], records: list[dict[str, Any]]) -> None:
    _require_schema_version(anchors_doc, source="search_anchors.yaml")
    if str(anchors_doc.get("kind") or "") != "KNOWN_SEARCH_ANCHOR":
        raise ReconciliationValidationError("SEARCH_ANCHOR_KIND_INVALID")
    if anchors_doc.get("counted_as_ledger_records") is not False:
        raise ReconciliationValidationError("SEARCH_ANCHORS_COUNTED_AS_RECORDS")
    if anchors_doc.get("anchors_are_not_ledger_records") is not True:
        raise ReconciliationValidationError("SEARCH_ANCHORS_COUNTED_AS_RECORDS")
    if anchors_doc.get("anchors_are_not_census_boundaries") is not True:
        raise ReconciliationValidationError("SEARCH_ANCHORS_USED_AS_CENSUS_BOUNDARY")
    anchors = list(anchors_doc.get("anchors") or [])
    names = [str(row.get("name") or "") for row in anchors]
    missing = [n for n in REQUIRED_INITIAL_ANCHOR_NAMES if n not in names]
    if missing:
        raise ReconciliationValidationError("KNOWN_SEARCH_ANCHOR_MISSING:" + ",".join(missing))
    seen_ids: set[str] = set()
    for row in anchors:
        aid = str(row.get("id") or "")
        if not ANCHOR_ID_PATTERN.match(aid):
            raise ReconciliationValidationError(f"SEARCH_ANCHOR_ID_MALFORMED:{aid}")
        if ID_PATTERN.match(aid):
            raise ReconciliationValidationError(f"SEARCH_ANCHOR_HAS_RCN_ID:{aid}")
        if aid in seen_ids:
            raise ReconciliationValidationError(f"SEARCH_ANCHOR_ID_DUPLICATE:{aid}")
        seen_ids.add(aid)
        if str(row.get("kind") or "") != "KNOWN_SEARCH_ANCHOR":
            raise ReconciliationValidationError(f"SEARCH_ANCHOR_KIND_INVALID:{aid}")
    record_ids = {
        str(
            (rec.get("identity") or {}).get("reconciliation_id")
            or rec.get("reconciliation_id")
            or ""
        )
        for rec in records
    }
    overlap = seen_ids & record_ids
    if overlap:
        raise ReconciliationValidationError("SEARCH_ANCHOR_IN_LEDGER:" + ",".join(sorted(overlap)))


def _validate_claim(claim: dict[str, Any], *, rid: str) -> None:
    cls = str(claim.get("claim_class") or claim.get("class") or "")
    allowed = FACT_CLAIM_CLASSES | NON_FACT_CLAIM_CLASSES
    if cls not in allowed:
        raise ReconciliationValidationError(f"CLAIM_CLASS_UNKNOWN:{rid}:{cls}")
    if cls == "HYPOTHESIS" and (
        claim.get("used_as_fact") is True or claim.get("serialized_as_fact") is True
    ):
        raise ReconciliationValidationError(f"HYPOTHESIS_SERIALIZED_AS_FACT:{rid}")
    if cls in NON_FACT_CLAIM_CLASSES and claim.get("used_as_fact") is True:
        raise ReconciliationValidationError(f"NON_FACT_SERIALIZED_AS_FACT:{rid}:{cls}")


def _validate_record(
    record: dict[str, Any],
    *,
    gov: dict[str, Any],
    seen_ids: set[str],
) -> str:
    if str(record.get("kind") or "") == "KNOWN_SEARCH_ANCHOR":
        raise ReconciliationValidationError("SEARCH_ANCHOR_IN_LEDGER")
    identity = record.get("identity") or {}
    if not isinstance(identity, dict):
        raise ReconciliationValidationError("RECORD_IDENTITY_MISSING")
    rid = str(identity.get("reconciliation_id") or record.get("reconciliation_id") or "")
    if not ID_PATTERN.match(rid):
        raise ReconciliationValidationError(f"RECORD_ID_MALFORMED:{rid}")
    if rid in seen_ids:
        raise ReconciliationValidationError(f"RECORD_ID_DUPLICATE:{rid}")
    seen_ids.add(rid)
    for category in gov.get("required_record_categories") or []:
        if category not in record or not isinstance(record.get(category), dict):
            raise ReconciliationValidationError(f"RECORD_CATEGORY_MISSING:{rid}:{category}")
    understanding = record.get("understanding") or {}
    purpose_understood = understanding.get("purpose_understood")
    if purpose_understood not in {True, False}:
        raise ReconciliationValidationError(f"PURPOSE_UNDERSTOOD_NOT_BOOLEAN:{rid}")
    if purpose_understood is True:
        statement = str(understanding.get("purpose_statement") or "").strip()
        if not statement:
            raise ReconciliationValidationError(f"PURPOSE_UNDERSTOOD_WITHOUT_STATEMENT:{rid}")
        claim_evidence = []
        for claim in list(understanding.get("claims") or []):
            if not isinstance(claim, dict):
                continue
            cls = str(claim.get("claim_class") or "")
            if cls in FACT_CLAIM_CLASSES:
                claim_evidence.extend([str(x) for x in (claim.get("evidence") or []) if str(x)])
        if not claim_evidence:
            raise ReconciliationValidationError(f"PURPOSE_UNDERSTOOD_WITHOUT_EVIDENCE:{rid}")
    adjudication = record.get("adjudication") or {}
    lifecycle = str(adjudication.get("lifecycle_state") or "")
    lifecycle_allowed = list(gov.get("lifecycle_states") or []) + list(
        gov.get("post_decision_states") or []
    )
    if lifecycle not in lifecycle_allowed:
        raise ReconciliationValidationError(f"LIFECYCLE_UNKNOWN:{rid}:{lifecycle}")
    disposition = str(adjudication.get("disposition") or "").strip()
    if disposition:
        taxonomy = gov.get("disposition_taxonomy") or {}
        if disposition not in taxonomy:
            raise ReconciliationValidationError(f"DISPOSITION_UNKNOWN:{rid}:{disposition}")
        if disposition in FINAL_DISPOSITIONS_REQUIRE_PURPOSE and purpose_understood is not True:
            raise ReconciliationValidationError(f"DISPOSITION_BEFORE_PURPOSE_UNDERSTOOD:{rid}")
        if disposition == "REJECT_FOR_CURRENT_SYSTEM":
            reason = str(adjudication.get("positive_reason") or "").strip()
            if not reason:
                raise ReconciliationValidationError(f"REJECT_WITHOUT_POSITIVE_REASON:{rid}")
        if disposition == "INSUFFICIENT_EVIDENCE" and lifecycle == "REJECTED":
            raise ReconciliationValidationError(f"INSUFFICIENT_EVIDENCE_MARKED_REJECTED:{rid}")
        allowed_states = DISPOSITION_TO_POST_STATES.get(disposition)
        if (
            allowed_states is not None
            and lifecycle not in allowed_states
            and lifecycle
            in (
                list(gov.get("post_decision_states") or []) + ["DISPOSITION_DECIDED", "ADJUDICATED"]
            )
        ):
            if lifecycle in {"REINTEGRATED", "COVERED", "INCOMPATIBLE", "REJECTED", "OPEN"}:
                if lifecycle not in allowed_states:
                    raise ReconciliationValidationError(
                        f"DISPOSITION_STATE_MISMATCH:{rid}:{disposition}:{lifecycle}"
                    )
    if lifecycle == "REJECTED":
        if disposition != "REJECT_FOR_CURRENT_SYSTEM":
            raise ReconciliationValidationError(f"REJECTED_WITHOUT_REJECT_DISPOSITION:{rid}")
        if not str(adjudication.get("positive_reason") or "").strip():
            raise ReconciliationValidationError(f"REJECT_WITHOUT_POSITIVE_REASON:{rid}")
    if lifecycle == "OPEN" and disposition not in {"", "INSUFFICIENT_EVIDENCE"}:
        raise ReconciliationValidationError(f"OPEN_WITHOUT_INSUFFICIENT_EVIDENCE:{rid}")
    if lifecycle in {"DISCOVERED", "EVIDENCE_BOUND", "PURPOSE_UNDERSTOOD"} and disposition:
        raise ReconciliationValidationError(f"DISPOSITION_BEFORE_CURRENT_SYSTEM_COMPARE:{rid}")
    if lifecycle in {"DISPOSITION_DECIDED", "ADJUDICATED"} and not disposition:
        raise ReconciliationValidationError(f"DISPOSITION_STATE_WITHOUT_DISPOSITION:{rid}")
    if lifecycle == "CURRENT_SYSTEM_COMPARED":
        if purpose_understood is not True:
            raise ReconciliationValidationError(f"COMPARE_BEFORE_PURPOSE_UNDERSTOOD:{rid}")
        if disposition:
            raise ReconciliationValidationError(f"DISPOSITION_DURING_CURRENT_SYSTEM_COMPARE:{rid}")
        overlap = str((record.get("current_comparison") or {}).get("capability_overlap") or "")
        if not overlap.strip():
            raise ReconciliationValidationError(f"CURRENT_SYSTEM_COMPARED_WITHOUT_OVERLAP:{rid}")
    discovery = record.get("discovery") or {}
    presence = str(discovery.get("current_presence") or "")
    if presence and presence not in ALLOWED_CURRENT_PRESENCE:
        raise ReconciliationValidationError(f"CURRENT_PRESENCE_UNKNOWN:{rid}:{presence}")
    relations = record.get("relations") or {}
    for rel in relations.get("items") or relations.get("relations") or []:
        rtype = str(rel.get("relation_type") or rel.get("type") or "")
        if rtype and rtype not in ALLOWED_RELATION_TYPES:
            raise ReconciliationValidationError(f"RELATION_TYPE_UNKNOWN:{rid}:{rtype}")
        epi = str(rel.get("epistemic_status") or "")
        if epi and epi not in (FACT_CLAIM_CLASSES | NON_FACT_CLAIM_CLASSES):
            raise ReconciliationValidationError(f"RELATION_EPISTEMIC_UNKNOWN:{rid}:{epi}")
    for claim in _claims_of(record):
        if isinstance(claim, dict):
            _validate_claim(claim, rid=rid)
    _validate_optional_evidence_resolution(record, rid=rid)
    _validate_optional_reevaluate(record, rid=rid)
    _validate_optional_reevaluate_v2(record, rid=rid)
    return rid


def _validate_optional_evidence_resolution(record: dict[str, Any], *, rid: str) -> None:
    block = record.get("evidence_resolution")
    if block is None:
        return
    if not isinstance(block, dict):
        raise ReconciliationValidationError(f"EVIDENCE_RESOLUTION_NOT_MAPPING:{rid}")
    status = str(block.get("evidence_resolution_status") or "")
    if status not in ALLOWED_EVIDENCE_RESOLUTION_STATUSES:
        raise ReconciliationValidationError(f"EVIDENCE_RESOLUTION_STATUS_UNKNOWN:{rid}:{status}")
    for gap_key in EVIDENCE_RESOLUTION_REQUIRED_GAPS:
        gap = block.get(gap_key)
        if not isinstance(gap, dict):
            raise ReconciliationValidationError(f"EVIDENCE_RESOLUTION_GAP_MISSING:{rid}:{gap_key}")
        if not str(gap.get("status") or "").strip():
            raise ReconciliationValidationError(
                f"EVIDENCE_RESOLUTION_GAP_STATUS_MISSING:{rid}:{gap_key}"
            )
        if not str(gap.get("statement") or "").strip():
            raise ReconciliationValidationError(
                f"EVIDENCE_RESOLUTION_GAP_STATEMENT_MISSING:{rid}:{gap_key}"
            )
    if block.get("final_disposition_change_performed") is True:
        raise ReconciliationValidationError(f"EVIDENCE_RESOLUTION_CHANGED_DISPOSITION:{rid}")
    if block.get("identity_merge_performed") is True:
        raise ReconciliationValidationError(f"EVIDENCE_RESOLUTION_IDENTITY_MERGE:{rid}")
    if block.get("reintegration_performed") is True:
        raise ReconciliationValidationError(f"EVIDENCE_RESOLUTION_REINTEGRATION:{rid}")
    if block.get("runtime_mutation_performed") is True:
        raise ReconciliationValidationError(f"EVIDENCE_RESOLUTION_RUNTIME_MUTATION:{rid}")
    adj = record.get("adjudication") or {}
    if str(adj.get("disposition") or "") == "INSUFFICIENT_EVIDENCE":
        if str(adj.get("lifecycle_state") or "") != "OPEN":
            raise ReconciliationValidationError(f"EVIDENCE_RESOLUTION_OPEN_STATE_DRIFT:{rid}")


def _validate_optional_reevaluate(record: dict[str, Any], *, rid: str) -> None:
    block = record.get("reevaluate")
    if block is None:
        return
    if not isinstance(block, dict):
        raise ReconciliationValidationError(f"REEVALUATE_NOT_MAPPING:{rid}")
    burden_met = _as_bool(
        block.get("disposition_burden_met"), field=f"disposition_burden_met:{rid}"
    )
    if block.get("identity_merge_performed") is True:
        raise ReconciliationValidationError(f"REEVALUATE_IDENTITY_MERGE:{rid}")
    if block.get("reintegration_performed") is True:
        raise ReconciliationValidationError(f"REEVALUATE_REINTEGRATION:{rid}")
    if block.get("runtime_mutation_performed") is True:
        raise ReconciliationValidationError(f"REEVALUATE_RUNTIME_MUTATION:{rid}")
    for field in REEVALUATE_REQUIRED_TEXT_FIELDS:
        if not str(block.get(field) or "").strip():
            raise ReconciliationValidationError(f"REEVALUATE_FIELD_MISSING:{rid}:{field}")
    if not list(block.get("current_evidence_set") or []):
        raise ReconciliationValidationError(f"REEVALUATE_EVIDENCE_SET_MISSING:{rid}")
    if not list(block.get("alternatives_rejected") or []):
        raise ReconciliationValidationError(f"REEVALUATE_ALTERNATIVES_MISSING:{rid}")
    if not list(block.get("unresolved_gaps") or []):
        raise ReconciliationValidationError(f"REEVALUATE_GAPS_MISSING:{rid}")
    adj = record.get("adjudication") or {}
    v2 = record.get("reevaluate_v2")
    if burden_met is False:
        if block.get("final_disposition_change_performed") is True:
            raise ReconciliationValidationError(
                f"REEVALUATE_BURDEN_UNMET_CHANGED_DISPOSITION:{rid}"
            )
        if str(block.get("disposition") or "") != "INSUFFICIENT_EVIDENCE":
            raise ReconciliationValidationError(f"REEVALUATE_BURDEN_UNMET_NOT_OPEN:{rid}")
        if str(block.get("lifecycle_state") or "") != "OPEN":
            raise ReconciliationValidationError(f"REEVALUATE_BURDEN_UNMET_STATE_DRIFT:{rid}")
        if not isinstance(v2, dict):
            if str(adj.get("disposition") or "") != "INSUFFICIENT_EVIDENCE":
                raise ReconciliationValidationError(f"REEVALUATE_LIVE_DISPOSITION_DRIFT:{rid}")
            if str(adj.get("lifecycle_state") or "") != "OPEN":
                raise ReconciliationValidationError(f"REEVALUATE_LIVE_STATE_DRIFT:{rid}")
    if rid == "RCN-000052":
        presence = str((record.get("discovery") or {}).get("current_presence") or "")
        if presence != "CURRENTLY_ABSENT":
            raise ReconciliationValidationError("REEVALUATE_RCN000052_PRESENCE_REWRITE")
        if str(block.get("disposition") or "") == "RETAIN_AS_IS":
            raise ReconciliationValidationError("REEVALUATE_RCN000052_RETAIN_WHILE_CONTRADICTED")


def _validate_optional_reevaluate_v2(record: dict[str, Any], *, rid: str) -> None:
    block = record.get("reevaluate_v2")
    if block is None:
        return
    if not isinstance(block, dict):
        raise ReconciliationValidationError(f"REEVALUATE_V2_NOT_MAPPING:{rid}")
    from scripts.ops.system_atlas_v1.reevaluate_open_records_pass_v2_records import (
        CONTRADICTION_ID_052,
        EXPLICIT_REMAIN_OPEN_IDS,
        INCOMPATIBLE,
        INPUT_PASS_ID,
        PREDECESSOR_BOUND_SHA,
        PREDECESSOR_PASS_ID,
        REJECT,
        REEVALUATE_V2_BOUND_SHA,
        REEVALUATE_V2_PASS_ID,
        TARGET_FINAL_IDS,
        V2_WRITTEN_RECORD_IDS,
    )

    if rid not in V2_WRITTEN_RECORD_IDS:
        raise ReconciliationValidationError(f"REEVALUATE_V2_OUT_OF_SCOPE:{rid}")
    if str(block.get("pass_id") or "") != REEVALUATE_V2_PASS_ID:
        raise ReconciliationValidationError(f"REEVALUATE_V2_PASS_ID_MISMATCH:{rid}")
    if str(block.get("input_pass_id") or "") != INPUT_PASS_ID:
        raise ReconciliationValidationError(f"REEVALUATE_V2_INPUT_PASS_MISMATCH:{rid}")
    if str(block.get("predecessor_pass_id") or "") != PREDECESSOR_PASS_ID:
        raise ReconciliationValidationError(f"REEVALUATE_V2_PREDECESSOR_MISMATCH:{rid}")
    if str(block.get("predecessor_bound_sha") or "") != PREDECESSOR_BOUND_SHA:
        raise ReconciliationValidationError(f"REEVALUATE_V2_PREDECESSOR_SHA_MISMATCH:{rid}")
    if str(block.get("bound_against_sha") or "") != REEVALUATE_V2_BOUND_SHA:
        raise ReconciliationValidationError(f"REEVALUATE_V2_BOUND_SHA_MISMATCH:{rid}")
    burden_met = _as_bool(
        block.get("disposition_burden_met"), field=f"reevaluate_v2.disposition_burden_met:{rid}"
    )
    if block.get("identity_merge_performed") is True:
        raise ReconciliationValidationError(f"REEVALUATE_V2_IDENTITY_MERGE:{rid}")
    if block.get("reintegration_performed") is True:
        raise ReconciliationValidationError(f"REEVALUATE_V2_REINTEGRATION:{rid}")
    if block.get("runtime_mutation_performed") is True:
        raise ReconciliationValidationError(f"REEVALUATE_V2_RUNTIME_MUTATION:{rid}")
    for field in REEVALUATE_REQUIRED_TEXT_FIELDS:
        if not str(block.get(field) or "").strip():
            raise ReconciliationValidationError(f"REEVALUATE_V2_FIELD_MISSING:{rid}:{field}")
    if not list(block.get("current_evidence_set") or []):
        raise ReconciliationValidationError(f"REEVALUATE_V2_EVIDENCE_SET_MISSING:{rid}")
    if not list(block.get("alternatives_rejected") or []):
        raise ReconciliationValidationError(f"REEVALUATE_V2_ALTERNATIVES_MISSING:{rid}")
    if not list(block.get("unresolved_gaps") or []):
        raise ReconciliationValidationError(f"REEVALUATE_V2_GAPS_MISSING:{rid}")
    adj = record.get("adjudication") or {}
    if burden_met is True:
        if rid not in TARGET_FINAL_IDS:
            raise ReconciliationValidationError(f"REEVALUATE_V2_UNEXPECTED_FINAL:{rid}")
        if block.get("final_disposition_change_performed") is not True:
            raise ReconciliationValidationError(f"REEVALUATE_V2_FINAL_FLAG_MISSING:{rid}")
        disposition = str(block.get("disposition") or "")
        if disposition not in {INCOMPATIBLE, REJECT}:
            raise ReconciliationValidationError(
                f"REEVALUATE_V2_DISPOSITION_NOT_ALLOWED:{rid}:{disposition}"
            )
        if str(adj.get("disposition") or "") != disposition:
            raise ReconciliationValidationError(f"REEVALUATE_V2_LIVE_DISPOSITION_DRIFT:{rid}")
        if str(adj.get("lifecycle_state") or "") != str(block.get("lifecycle_state") or ""):
            raise ReconciliationValidationError(f"REEVALUATE_V2_LIVE_STATE_DRIFT:{rid}")
        if not str(adj.get("positive_reason") or "").strip():
            raise ReconciliationValidationError(f"REEVALUATE_V2_POSITIVE_REASON_MISSING:{rid}")
    else:
        if rid not in EXPLICIT_REMAIN_OPEN_IDS:
            raise ReconciliationValidationError(f"REEVALUATE_V2_UNEXPECTED_OPEN_BLOCK:{rid}")
        if block.get("final_disposition_change_performed") is True:
            raise ReconciliationValidationError(f"REEVALUATE_V2_OPEN_CHANGED_DISPOSITION:{rid}")
        if str(block.get("disposition") or "") != "INSUFFICIENT_EVIDENCE":
            raise ReconciliationValidationError(f"REEVALUATE_V2_OPEN_NOT_INSUFFICIENT:{rid}")
        if str(block.get("lifecycle_state") or "") != "OPEN":
            raise ReconciliationValidationError(f"REEVALUATE_V2_OPEN_STATE_DRIFT:{rid}")
        if str(adj.get("disposition") or "") != "INSUFFICIENT_EVIDENCE":
            raise ReconciliationValidationError(f"REEVALUATE_V2_LIVE_OPEN_DRIFT:{rid}")
        if str(adj.get("lifecycle_state") or "") != "OPEN":
            raise ReconciliationValidationError(f"REEVALUATE_V2_LIVE_OPEN_STATE_DRIFT:{rid}")
    if rid == "RCN-000052":
        presence = str((record.get("discovery") or {}).get("current_presence") or "")
        if presence != "CURRENTLY_ABSENT":
            raise ReconciliationValidationError("REEVALUATE_V2_RCN000052_PRESENCE_REWRITE")
        if str(block.get("disposition") or "") == "RETAIN_AS_IS":
            raise ReconciliationValidationError("REEVALUATE_V2_RCN000052_RETAIN_WHILE_CONTRADICTED")
        if str(adj.get("disposition") or "") == "RETAIN_AS_IS":
            raise ReconciliationValidationError("REEVALUATE_V2_RCN000052_LIVE_RETAIN")
        if str(block.get("contradiction_id") or "") != CONTRADICTION_ID_052:
            raise ReconciliationValidationError("REEVALUATE_V2_RCN000052_CONTRADICTION_ID")


def _validate_ledger(ledger: dict[str, Any], gov: dict[str, Any]) -> list[dict[str, Any]]:
    _require_schema_version(ledger, source="ledger.yaml")
    records = list(ledger.get("records") or [])
    declared = ledger.get("ledger_record_count")
    try:
        count = int(declared)
    except (TypeError, ValueError) as exc:
        raise ReconciliationValidationError("LEDGER_RECORD_COUNT_INVALID") from exc
    if count != len(records):
        raise ReconciliationValidationError(f"LEDGER_RECORD_COUNT_MISMATCH:{count}!={len(records)}")
    seen_ids: set[str] = set()
    for record in records:
        if not isinstance(record, dict):
            raise ReconciliationValidationError("LEDGER_RECORD_NOT_MAPPING")
        _validate_record(record, gov=gov, seen_ids=seen_ids)
    return records


def _validate_census_artifacts(payload: dict[str, Any], census: dict[str, Any]) -> None:
    status = str(census.get("census_status") or "")
    if status not in CENSUS_STARTED_STATUSES:
        return
    for rel in CENSUS_ARTIFACT_FILES:
        row = payload["records"].get(rel)
        if not isinstance(row, dict):
            raise ReconciliationValidationError(f"RECONCILIATION_CENSUS_ARTIFACT_MISSING:{rel}")
        _require_schema_version(row, source=rel)
    coverage = payload["records"].get("coverage.yaml") or {}
    rows = list(coverage.get("rows") or [])
    proven = 0
    unproven = 0
    for row in rows:
        if not isinstance(row, dict):
            raise ReconciliationValidationError("COVERAGE_ROW_NOT_MAPPING")
        sid = str(row.get("surface_id") or "")
        if "searched" not in row:
            raise ReconciliationValidationError(f"COVERAGE_SEARCHED_MISSING:{sid}")
        if not str(row.get("method") or row.get("search_method") or "").strip():
            raise ReconciliationValidationError(f"COVERAGE_METHOD_MISSING:{sid}")
        if "exhaustion_proven" not in row:
            raise ReconciliationValidationError(f"COVERAGE_EXHAUSTION_FLAG_MISSING:{sid}")
        exhausted = _as_bool(row.get("exhaustion_proven"), field=f"exhaustion_proven:{sid}")
        if exhausted:
            proven += 1
            if not str(row.get("evidence_reference") or row.get("evidence_ref") or "").strip():
                raise ReconciliationValidationError(f"COVERAGE_EXHAUSTION_WITHOUT_EVIDENCE:{sid}")
        else:
            unproven += 1
            if not str(row.get("remaining_gap") or "").strip():
                raise ReconciliationValidationError(f"COVERAGE_UNPROVEN_WITHOUT_GAP:{sid}")
            reason = str(
                row.get("exhaustion_unproven_reason") or row.get("limitations") or ""
            ).strip()
            if not reason:
                raise ReconciliationValidationError(f"COVERAGE_UNPROVEN_WITHOUT_REASON:{sid}")
    declared_proven = coverage.get("surfaces_exhaustion_proven")
    declared_unproven = coverage.get("surfaces_exhaustion_unproven")
    if declared_proven is not None and int(declared_proven) != proven:
        raise ReconciliationValidationError(
            f"COVERAGE_PROVEN_COUNT_MISMATCH:{declared_proven}!={proven}"
        )
    if declared_unproven is not None and int(declared_unproven) != unproven:
        raise ReconciliationValidationError(
            f"COVERAGE_UNPROVEN_COUNT_MISMATCH:{declared_unproven}!={unproven}"
        )
    closed = _as_bool(census.get("census_closed"), field="census_closed")
    if closed and unproven:
        raise ReconciliationValidationError("CENSUS_CLOSED_WITH_UNPROVEN_SURFACES")
    if closed and proven != len(rows):
        raise ReconciliationValidationError("CENSUS_CLOSED_WITHOUT_ALL_SURFACES_PROVEN")


def validate_reconciliation_v1(payload: dict[str, Any]) -> list[str]:
    """Return empty list on PASS. Raise on integrity failure."""
    gov = payload["records"]["GOVERNANCE_V1.yaml"] or {}
    census = payload["records"]["census_status.yaml"] or {}
    anchors = payload["records"]["search_anchors.yaml"] or {}
    ledger = payload["records"]["ledger.yaml"] or {}
    schema = payload["records"]["schema.yaml"] or {}
    _require_schema_version(schema, source="schema.yaml")
    _validate_governance(gov)
    records = _validate_ledger(ledger, gov)
    _validate_census(census, gov)
    _validate_anchors(anchors, records)
    _validate_census_artifacts(payload, census)
    _validate_reevaluate_pass_v2_tree(payload, records)
    return []


def _validate_reevaluate_pass_v2_tree(
    payload: dict[str, Any], records: list[dict[str, Any]]
) -> None:
    ledger = payload["records"]["ledger.yaml"] or {}
    schema = payload["records"]["schema.yaml"] or {}
    root = Path(str(payload.get("root") or ""))
    status_path = root / "reevaluate" / "pass_v2_status.yaml"
    live_pass = str(ledger.get("reevaluate_pass_id") or "")
    if live_pass != "REEVALUATE_OPEN_RECORDS_PASS_V2":
        return
    if len(records) != 53:
        return
    if not status_path.is_file():
        raise ReconciliationValidationError("REEVALUATE_V2_STATUS_MISSING")
    from scripts.ops.system_atlas_v1.reevaluate_open_records_pass_v1_records import (
        REEVALUATE_BOUND_SHA as REEVALUATE_V1_BOUND_SHA,
        REEVALUATE_PASS_ID as REEVALUATE_V1_PASS_ID,
    )
    from scripts.ops.system_atlas_v1.reevaluate_open_records_pass_v2_records import (
        CONTRADICTION_ID_052,
        INCOMPATIBLE,
        INPUT_PASS_ID,
        OUT_OF_SCOPE_OPEN_IDS,
        PREDECESSOR_BOUND_SHA,
        PREDECESSOR_PASS_ID,
        REJECT,
        REEVALUATE_V2_BOUND_SHA,
        REEVALUATE_V2_PASS_ID,
        REMAINING_OPEN_IDS,
        RESULTING_DISPOSITIONS,
        TARGET_FINAL_IDS,
        V2_WRITTEN_RECORD_IDS,
    )
    from scripts.ops.system_atlas_v1.evidence_resolution_pass_v1_records import OPEN_IDS
    from scripts.ops.system_atlas_v1.adjudicate_pass_v1_records import RETAIN, RETAIN_IDS

    status = _read_yaml(status_path)
    if str(status.get("reevaluate_pass_id") or "") != REEVALUATE_V2_PASS_ID:
        raise ReconciliationValidationError("REEVALUATE_V2_STATUS_PASS_ID")
    if str(status.get("predecessor_pass_id") or "") != PREDECESSOR_PASS_ID:
        raise ReconciliationValidationError("REEVALUATE_V2_STATUS_PREDECESSOR")
    if str(status.get("predecessor_bound_sha") or "") != PREDECESSOR_BOUND_SHA:
        raise ReconciliationValidationError("REEVALUATE_V2_STATUS_PREDECESSOR_SHA")
    if str(status.get("input_pass_id") or "") != INPUT_PASS_ID:
        raise ReconciliationValidationError("REEVALUATE_V2_STATUS_INPUT_PASS")
    if str(status.get("bound_against_sha") or "") != REEVALUATE_V2_BOUND_SHA:
        raise ReconciliationValidationError("REEVALUATE_V2_STATUS_BOUND_SHA")
    if int(status.get("input_open_record_count", -1)) != 35:
        raise ReconciliationValidationError("REEVALUATE_V2_INPUT_OPEN_COUNT")
    if int(status.get("new_final_disposition_count", -1)) != 5:
        raise ReconciliationValidationError("REEVALUATE_V2_FINALIZED_COUNT")
    if int(status.get("remaining_insufficient_evidence_open_count", -1)) != 30:
        raise ReconciliationValidationError("REEVALUATE_V2_REMAINING_OPEN_COUNT")
    if int(status.get("identity_merges_performed", -1)) != 0:
        raise ReconciliationValidationError("REEVALUATE_V2_IDENTITY_MERGES")
    if status.get("reintegration_performed") is True:
        raise ReconciliationValidationError("REEVALUATE_V2_REINTEGRATION")
    if status.get("runtime_mutation_performed") is True:
        raise ReconciliationValidationError("REEVALUATE_V2_RUNTIME")
    if status.get("rcn_000052_remains_open") is not True:
        raise ReconciliationValidationError("REEVALUATE_V2_052_NOT_MARKED_OPEN")
    if str(ledger.get("reevaluate_v1_pass_id_frozen") or "") != REEVALUATE_V1_PASS_ID:
        raise ReconciliationValidationError("REEVALUATE_V2_V1_PASS_FROZEN_MISSING")
    if str(ledger.get("reevaluate_v1_bound_against_sha_frozen") or "") != REEVALUATE_V1_BOUND_SHA:
        raise ReconciliationValidationError("REEVALUATE_V2_V1_SHA_FROZEN_MISSING")
    if schema.get("reevaluate_v1_snapshots_are_frozen") is not True:
        raise ReconciliationValidationError("REEVALUATE_V2_SCHEMA_V1_FROZEN_FLAG")

    hashes = status.get("v1_frozen_file_sha256") or {}
    if not isinstance(hashes, dict) or len(hashes) != 37:
        raise ReconciliationValidationError("REEVALUATE_V2_V1_HASH_CATALOG")
    for rel, expected in hashes.items():
        path = root / str(rel)
        if not path.is_file():
            raise ReconciliationValidationError(f"REEVALUATE_V2_V1_FILE_MISSING:{rel}")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != str(expected):
            raise ReconciliationValidationError(f"REEVALUATE_V2_V1_HASH_MISMATCH:{rel}")

    retain = 0
    insufficient = 0
    incompatible = 0
    rejected = 0
    ids: list[str] = []
    for rec in records:
        rid = str((rec.get("identity") or {}).get("reconciliation_id") or "")
        ids.append(rid)
        disp = str((rec.get("adjudication") or {}).get("disposition") or "")
        if disp == RETAIN:
            retain += 1
            if rec.get("reevaluate_v2") is not None:
                raise ReconciliationValidationError(f"REEVALUATE_V2_ON_RETAIN:{rid}")
            if rid not in RETAIN_IDS:
                raise ReconciliationValidationError(f"REEVALUATE_V2_RETAIN_ID_DRIFT:{rid}")
        elif disp == "INSUFFICIENT_EVIDENCE":
            insufficient += 1
        elif disp == INCOMPATIBLE:
            incompatible += 1
        elif disp == REJECT:
            rejected += 1
        if rid in TARGET_FINAL_IDS:
            expected = RESULTING_DISPOSITIONS[rid]
            if disp != expected:
                raise ReconciliationValidationError(
                    f"REEVALUATE_V2_TARGET_DISPOSITION:{rid}:{disp}!={expected}"
                )
            if rec.get("reevaluate_v2") is None:
                raise ReconciliationValidationError(f"REEVALUATE_V2_TARGET_BLOCK_MISSING:{rid}")
        elif rid in OUT_OF_SCOPE_OPEN_IDS:
            if disp != "INSUFFICIENT_EVIDENCE":
                raise ReconciliationValidationError(f"REEVALUATE_V2_OUT_OF_SCOPE_MUTATED:{rid}")
            if rec.get("reevaluate_v2") is not None:
                raise ReconciliationValidationError(f"REEVALUATE_V2_OUT_OF_SCOPE_BLOCK:{rid}")
        if rid == "RCN-000052":
            if disp != "INSUFFICIENT_EVIDENCE":
                raise ReconciliationValidationError("REEVALUATE_V2_052_FINALIZED")
            v2 = rec.get("reevaluate_v2") or {}
            if str(v2.get("contradiction_id") or "") != CONTRADICTION_ID_052:
                raise ReconciliationValidationError("REEVALUATE_V2_052_CONTRADICTION")
        for rel in (rec.get("relations") or {}).get("items") or []:
            rtype = str(rel.get("relation_type") or "")
            if rtype in {"MERGED_INTO", "RENAMED_TO", "SPLIT_INTO", "SAME_AS"}:
                raise ReconciliationValidationError(f"REEVALUATE_V2_IDENTITY_FUSION:{rid}:{rtype}")
    if len(ids) != 53 or len(set(ids)) != 53:
        raise ReconciliationValidationError("REEVALUATE_V2_RECORD_ID_COUNT")
    if retain != 18 or incompatible != 1 or rejected != 4 or insufficient != 30:
        raise ReconciliationValidationError(
            f"REEVALUATE_V2_COUNT_MISMATCH:{retain}:{incompatible}:{rejected}:{insufficient}"
        )
    live_open = tuple(
        rec["identity"]["reconciliation_id"]
        for rec in records
        if str((rec.get("adjudication") or {}).get("disposition") or "") == "INSUFFICIENT_EVIDENCE"
    )
    if live_open != REMAINING_OPEN_IDS:
        raise ReconciliationValidationError("REEVALUATE_V2_REMAINING_OPEN_SET")
    if tuple(OPEN_IDS) != OPEN_IDS:
        raise ReconciliationValidationError("REEVALUATE_V2_INPUT_OPEN_SET")
    for rid in V2_WRITTEN_RECORD_IDS:
        path = root / "reevaluate" / "records_v2" / f"{rid}.yaml"
        if not path.is_file():
            raise ReconciliationValidationError(f"REEVALUATE_V2_RECORD_MISSING:{rid}")
    extra = list((root / "reevaluate" / "records_v2").glob("RCN-*.yaml"))
    if len(extra) != 6:
        raise ReconciliationValidationError("REEVALUATE_V2_EXTRA_RECORDS")


def validate_reconciliation_tree_v1(*, repo_root: Path) -> list[str]:
    payload = load_reconciliation_v1(repo_root=repo_root)
    return validate_reconciliation_v1(payload)
