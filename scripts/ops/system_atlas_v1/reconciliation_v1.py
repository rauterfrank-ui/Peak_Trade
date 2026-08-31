"""Historical reconsolidation ledger validation.

ATLAS_AUTHORITY=NONE. RECONCILIATION_AUTHORITY=NONE.
Governance/evidence only. Not runtime authorization.
"""

from __future__ import annotations

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
    return rid


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
    return []


def validate_reconciliation_tree_v1(*, repo_root: Path) -> list[str]:
    payload = load_reconciliation_v1(repo_root=repo_root)
    return validate_reconciliation_v1(payload)
