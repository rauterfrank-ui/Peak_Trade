"""Deterministic fail-closed adjudication evaluator.

Classifies and disqualifies the bound candidate population. Does not
produce PROVEN_OCCURRENCE_IDENTITY, parentage, currentness, supersession,
winner selection, residual closure, or authority.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from scripts.ops.forensic_structure_schema_v1.adjudication_constants import (
    ADJUDICATION_AUTHORITY,
    ADJUDICATION_CONTRACT_VERSION,
    ADJUDICATION_DIMENSIONS,
    ADJUDICATION_GENERATOR_ID,
    ADJUDICATION_LAYER_ID,
    ADJUDICATION_MUST_REMAIN_OPEN,
    ADJUDICATION_OPEN_CLUSTER,
    ADJUDICATION_OUTPUT_ROLE,
    ALIGNMENT_INPUT_RELPATH,
    BOUND_SIDECAR_SHA256,
    BOUND_SOURCE_SHA256,
    CANDIDATE_FAMILIES,
    COMPETING_SET_KIND,
    DISPOSITION_DISQUALIFIERS,
    DOC_DEPENDENCY_COUNTERPARTY_STRINGS,
    EXECUTED_CLASSIFY_DISQUALIFY_DIMENSIONS,
    EXECUTION_BOUNDARIES,
    EXPECTED_CANDIDATE_COUNT,
    EXPECTED_CANDIDATE_FAMILY_COUNT,
    EXPECTED_CANDIDATE_SHARD_SHA256,
    EXPECTED_COMPETING_MEMBER_COUNT,
    EXPECTED_COMPETING_SET_COUNT,
    EXPECTED_ORIGINAL_AMBIGUOUS_BINDING_COUNT,
    EXPECTED_REFERENCED_OVERLAY_CLASS_FAMILY_COUNT,
    EXPECTED_T4_SHARD_SHA256,
    KNOWN_COMPETING_ENDPOINT_STRINGS,
    LOCUS_ABSENT,
    LOCUS_PRESENT,
    NON_IDENTITY_BY_ID,
    NON_IDENTITY_IDS,
    OPERATOR_AUTHORIZATION_SCOPE,
    POLARITY_NEGATIVE,
    REASON_CODES,
    SECTION_22_SIDECAR_ENDPOINT,
    SIDECAR_DEPENDENCY_SUBJECT,
    UNEXECUTED_DIMENSIONS,
)
from scripts.ops.forensic_structure_schema_v1.adjudication_guards import AdjudicationGuardProgram
from scripts.ops.forensic_structure_schema_v1.adjudication_models import (
    AdjudicationContract,
    AdjudicationDecisionRecord,
    CandidateAdjudicationResult,
    CompetingSetRecord,
    EvidenceRecord,
    PresenceTagged,
)
from scripts.ops.forensic_structure_schema_v1.constants import OVERLAY_CLASS_ORDER
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.minting import mint_transformation_local_id


def _fail(rule: str, message: str) -> None:
    raise TransformationContractViolation(rule, message)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _sanitize_suffix(value: str) -> str:
    if value == SECTION_22_SIDECAR_ENDPOINT:
        return "SECTION_22_SIDECAR"
    return value.replace("/", "_").replace(" ", "_")


def classify_candidate_family(endpoint_string: str, competing_strings: set[str]) -> str:
    if endpoint_string.startswith("SRC-"):
        return "T3_SRC_ALIAS"
    if endpoint_string.startswith("REL-"):
        return "T4_REL_ALIAS"
    if endpoint_string.startswith("wrapper_pair-"):
        return "OVERLAY_WRAPPER_PAIR"
    if endpoint_string.startswith("append_epoch-"):
        if endpoint_string in competing_strings:
            return "OVERLAY_APPEND_EPOCH_REUSED"
        return "OVERLAY_APPEND_EPOCH_UNIQUE"
    if endpoint_string.startswith("occ-"):
        return "LAYER1_OCCURRENCE"
    if endpoint_string == "Z2AR":
        return "DOC_Z2AR"
    if endpoint_string == "Z2AP":
        return "DOC_Z2AP"
    if endpoint_string == SECTION_22_SIDECAR_ENDPOINT:
        return "DOC_SECTION_22"
    if endpoint_string == SIDECAR_DEPENDENCY_SUBJECT:
        return "DOC_Z2AR_SUI_POSITION_VALUE_ALGEBRA_RECORD"
    if endpoint_string in DOC_DEPENDENCY_COUNTERPARTY_STRINGS:
        return "DOC_EXPLICIT_DEPENDENCY_COUNTERPARTY"
    _fail("CANDIDATE_FAMILY", f"unclassified endpoint family for {endpoint_string!r}")
    raise AssertionError("unreachable")


def competing_set_kind(endpoint_string: str) -> str:
    kind = COMPETING_SET_KIND.get(endpoint_string)
    if kind is None:
        _fail("COMPETING_SET", f"unknown competing endpoint {endpoint_string!r}")
    return kind


def _ni_applicable(ni_id: str, candidate: dict[str, Any], relation_type: str) -> bool:
    endpoint = str(candidate["endpoint_string"])
    dispositions = set(candidate["existing_disposition"])
    locus = str(candidate["source_locus_availability"])
    if ni_id == "NI-001":
        return False
    if ni_id == "NI-002":
        return False
    if ni_id == "NI-003":
        return relation_type == "WRAPPER_CONTAINS"
    if ni_id == "NI-004":
        return True
    if ni_id == "NI-005":
        return "LAYER1_MARKER_REFERENCE_ONLY" in dispositions
    if ni_id == "NI-006":
        return endpoint.startswith("REL-")
    if ni_id == "NI-007":
        return endpoint.startswith("SRC-")
    if ni_id == "NI-008":
        return False
    if ni_id == "NI-009":
        return endpoint.startswith("append_epoch-")
    if ni_id == "NI-010":
        return endpoint.startswith("append_epoch-")
    if ni_id == "NI-011":
        return relation_type == "STRUCTURAL_ORDERED_BEFORE"
    if ni_id == "NI-012":
        return relation_type in {"EXPLICIT_CONFLICT", "PREFIX_EPOCH_SUCCEEDS"}
    if ni_id == "NI-013":
        return locus == LOCUS_ABSENT
    if ni_id == "NI-014":
        return False
    if ni_id == "NI-015":
        return True
    if ni_id == "NI-016":
        return True
    if ni_id == "NI-017":
        return True
    _fail("NI_UNKNOWN", f"unknown NI id {ni_id}")
    raise AssertionError("unreachable")


def _disqualifier_applicable(code: str, candidate: dict[str, Any], relation_type: str) -> bool:
    dispositions = set(candidate["existing_disposition"])
    locus = str(candidate["source_locus_availability"])
    if code == "DR-002":
        return "LAYER1_MARKER_REFERENCE_ONLY" in dispositions
    if code == "DR-003":
        return locus == LOCUS_PRESENT
    if code == "INVENTED_OR_SIDECAR_CONSTRUCTED_STRING":
        return "INVENTED_OR_SIDECAR_CONSTRUCTED_STRING" in dispositions
    if code == "LAYER1_MARKER_REFERENCE_ONLY":
        return "LAYER1_MARKER_REFERENCE_ONLY" in dispositions
    if code == "AMBIGUOUS_BINDING":
        return "AMBIGUOUS_BINDING" in dispositions
    if code == "NAVIGATION_ONLY":
        return "NAVIGATION_ALIAS_ONLY" in dispositions
    if code == "DO_NOT_BIND":
        return "DO_NOT_BIND" in dispositions
    _fail("DISQUALIFIER_UNKNOWN", f"unknown disqualifier {code}")
    raise AssertionError("unreachable")


def _first_present_locus(candidate: dict[str, Any]) -> dict[str, Any] | None:
    loci = candidate.get("source_loci") or []
    if not loci:
        return None
    return dict(loci[0])


def _validate_loci(candidate: dict[str, Any], guards: AdjudicationGuardProgram) -> None:
    availability = str(candidate["source_locus_availability"])
    loci = candidate.get("source_loci") or []
    candidate_id = str(candidate["derived_record_id"])
    if availability == LOCUS_ABSENT:
        return
    if availability != LOCUS_PRESENT:
        _fail("LOCUS_ENCODING", f"unknown locus_availability {availability}: {candidate_id}")
    if not loci:
        _fail("LOCUS_INCOMPLETE", f"PRESENT without locus rows: {candidate_id}")
    for locus in loci:
        guards.assert_present_locus_complete(locus, candidate_id)


def load_candidate_projection(repo_root: Path | None = None) -> dict[str, Any]:
    root = repo_root or _repo_root()
    align_dir = root / ALIGNMENT_INPUT_RELPATH
    candidate_path = align_dir / "endpoint_binding_candidate_records.json"
    layer3_path = align_dir / "layer3_relation_records.json"
    residual_path = align_dir / "residual_status.json"
    catalog_path = align_dir / "dataset_catalog.json"
    counts_path = align_dir / "counts.json"
    for path in (candidate_path, layer3_path, residual_path, catalog_path, counts_path):
        if not path.is_file():
            _fail("CANDIDATE_PROJECTION_UNBOUND", f"missing alignment input {path}")
    candidate_bytes = candidate_path.read_bytes()
    candidate_sha = _sha256_hex(candidate_bytes)
    if candidate_sha != EXPECTED_CANDIDATE_SHARD_SHA256:
        _fail(
            "CANDIDATE_INDEX_SHA_DRIFT",
            f"candidate shard sha {candidate_sha} != {EXPECTED_CANDIDATE_SHARD_SHA256}",
        )
    candidates = json.loads(candidate_bytes.decode("utf-8"))
    layer3 = json.loads(layer3_path.read_text(encoding="utf-8"))
    residual_status = json.loads(residual_path.read_text(encoding="utf-8"))
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    counts = json.loads(counts_path.read_text(encoding="utf-8"))
    t4_sha = catalog.get("shard_sha256s", {}).get("t4_overlay_records.json")
    if t4_sha != EXPECTED_T4_SHARD_SHA256:
        _fail("T4_SHARD_SHA_DRIFT", f"catalog T4 sha {t4_sha} != {EXPECTED_T4_SHARD_SHA256}")
    if len(candidates) != EXPECTED_CANDIDATE_COUNT:
        _fail("CANDIDATE_POPULATION", f"candidate count {len(candidates)} != 244")
    if counts.get("ENDPOINT_RECORD_COUNT") != EXPECTED_CANDIDATE_COUNT:
        _fail("CANDIDATE_POPULATION", "alignment counts drifted")
    return {
        "candidates": candidates,
        "layer3": layer3,
        "residual_status": residual_status,
        "catalog": catalog,
        "counts": counts,
        "candidate_index_sha256": candidate_sha,
        "t4_shard_sha256": t4_sha,
    }


def _dimension_model() -> dict[str, Any]:
    rows = []
    for index, dimension in enumerate(ADJUDICATION_DIMENSIONS):
        executed = dimension in EXECUTED_CLASSIFY_DISQUALIFY_DIMENSIONS
        rows.append(
            {
                "authority": ADJUDICATION_AUTHORITY,
                "dimension": dimension,
                "dimension_order": index,
                "execution_mode": (
                    "CLASSIFY_DISQUALIFY_ONLY" if executed else "NOT_EXECUTED_UNADJUDICATED"
                ),
                "output_canonical": False,
                "positive_identity_authorized": False,
            }
        )
    return {
        "authority": ADJUDICATION_AUTHORITY,
        "dimensions": rows,
        "executed_classify_disqualify_dimensions": list(EXECUTED_CLASSIFY_DISQUALIFY_DIMENSIONS),
        "output_canonical": False,
        "unexecuted_dimensions": list(UNEXECUTED_DIMENSIONS),
    }


def _execution_boundaries() -> dict[str, Any]:
    common_forbidden = [
        "positive occurrence identity",
        "authority promotion",
        "canonicalization",
        "source or sidecar mutation",
        "residual status mutation",
    ]
    specs: dict[str, dict[str, Any]] = {
        "A_CANDIDATE_ADJUDICATION": {
            "inputs": [
                "endpoint_binding_candidate_records",
                "layer3_relation_records",
                "bound source/sidecar hashes",
            ],
            "outputs": ["derived classification/disqualification records"],
            "preconditions": [
                "OWNER_GO for derived-only contract infrastructure",
                "candidate population bound at 244",
            ],
            "forbidden_implicit_effects": common_forbidden
            + ["PROVEN_OCCURRENCE_IDENTITY", "winner selection"],
            "owner_go_requirement": OPERATOR_AUTHORIZATION_SCOPE,
            "authority_effect": "NONE",
            "replay_behavior": "byte-stable given identical input hashes",
            "authorized_by_this_go": "INFRASTRUCTURE_AND_CLASSIFY_DISQUALIFY_ONLY",
        },
        "B_PROVEN_OCCURRENCE_PERSISTENCE": {
            "inputs": ["adjudicated occurrence identity"],
            "outputs": ["proven occurrence records"],
            "preconditions": ["separate OWNER_GO; PROVEN_OCCURRENCE_IDENTITY authorized"],
            "forbidden_implicit_effects": common_forbidden,
            "owner_go_requirement": "SEPARATE_OWNER_GO_REQUIRED",
            "authority_effect": "NONE",
            "replay_behavior": "not executed",
            "authorized_by_this_go": False,
        },
        "C_PARENTAGE": {
            "inputs": ["view parent hints", "H1 overlays"],
            "outputs": ["parentage decisions"],
            "preconditions": ["separate OWNER_GO"],
            "forbidden_implicit_effects": common_forbidden + ["VIEW_PARENT_HINT as parentage"],
            "owner_go_requirement": "SEPARATE_OWNER_GO_REQUIRED",
            "authority_effect": "NONE",
            "replay_behavior": "not executed",
            "authorized_by_this_go": False,
        },
        "D_CURRENTNESS": {
            "inputs": ["PREFIX_EPOCH_SUCCEEDS", "epoch overlays"],
            "outputs": ["currentness decisions"],
            "preconditions": ["separate OWNER_GO"],
            "forbidden_implicit_effects": common_forbidden + ["epoch order as currentness"],
            "owner_go_requirement": "SEPARATE_OWNER_GO_REQUIRED",
            "authority_effect": "NONE",
            "replay_behavior": "not executed",
            "authorized_by_this_go": False,
        },
        "E_SUPERSESSION": {
            "inputs": ["PREFIX_EPOCH_SUCCEEDS", "later records"],
            "outputs": ["supersession decisions"],
            "preconditions": ["separate OWNER_GO"],
            "forbidden_implicit_effects": common_forbidden + ["epoch order as supersession"],
            "owner_go_requirement": "SEPARATE_OWNER_GO_REQUIRED",
            "authority_effect": "NONE",
            "replay_behavior": "not executed",
            "authorized_by_this_go": False,
        },
        "F_WINNER_SELECTION": {
            "inputs": ["EXPLICIT_CONFLICT competing sets"],
            "outputs": ["winner records"],
            "preconditions": ["separate OWNER_GO"],
            "forbidden_implicit_effects": common_forbidden + ["later record as winner"],
            "owner_go_requirement": "SEPARATE_OWNER_GO_REQUIRED",
            "authority_effect": "NONE",
            "replay_behavior": "not executed",
            "authorized_by_this_go": False,
        },
        "G_RESIDUAL_CLOSURE": {
            "inputs": ["SW-R-002", "SW-R-004", "SW-R-009", "cross-residual edges"],
            "outputs": ["residual status transitions"],
            "preconditions": ["separate OWNER_GO"],
            "forbidden_implicit_effects": common_forbidden
            + ["cross-residual prerequisites as close-order"],
            "owner_go_requirement": "SEPARATE_OWNER_GO_REQUIRED",
            "authority_effect": "NONE",
            "replay_behavior": "not executed",
            "authorized_by_this_go": False,
        },
        "H_CANONICALIZATION": {
            "inputs": ["derived forensic structure"],
            "outputs": ["canonical authority artifacts"],
            "preconditions": ["separate OWNER_GO"],
            "forbidden_implicit_effects": common_forbidden + ["structure as authority"],
            "owner_go_requirement": "SEPARATE_OWNER_GO_REQUIRED",
            "authority_effect": "NONE",
            "replay_behavior": "not executed",
            "authorized_by_this_go": False,
        },
    }
    rows = []
    for boundary_id in EXECUTION_BOUNDARIES:
        spec = specs[boundary_id]
        rows.append(
            {
                "authority_effect": spec["authority_effect"],
                "authorized_by_this_go": spec["authorized_by_this_go"],
                "boundary_id": boundary_id,
                "forbidden_implicit_effects": spec["forbidden_implicit_effects"],
                "inputs": spec["inputs"],
                "outputs": spec["outputs"],
                "owner_go_requirement": spec["owner_go_requirement"],
                "preconditions": spec["preconditions"],
                "replay_behavior": spec["replay_behavior"],
            }
        )
    return {
        "authority": ADJUDICATION_AUTHORITY,
        "boundaries": rows,
        "output_canonical": False,
        "this_go_authorizes_boundary_a_semantic_execution": False,
        "this_go_authorizes_boundaries_b_through_h": False,
    }


def _non_inference_audit() -> dict[str, Any]:
    return {
        "AUTHORITY_CHANGE": False,
        "CURRENTNESS_ADJUDICATION_PERFORMED": False,
        "NO_AUTHORITY_FROM_STRUCTURE": True,
        "NO_BIND_FROM_ADJACENCY": True,
        "NO_BIND_FROM_ALIAS_ONLY": True,
        "NO_BIND_FROM_SHA_ONLY": True,
        "NO_BIND_FROM_STRING_EQUALITY_ONLY": True,
        "NO_CANONICALIZATION": True,
        "NO_CURRENTNESS_FROM_EPOCH": True,
        "NO_DEPENDENCY_FROM_MECHANICAL_ORDER": True,
        "NO_PARENTAGE_FROM_VIEW_HINT": True,
        "NO_RESIDUAL_CLOSE_FROM_ADJUDICATION": True,
        "NO_SUPERSESSION_FROM_EPOCH": True,
        "NO_WINNER_FROM_LATER_RECORD": True,
        "OUTPUT_CANONICAL": False,
        "PARENTAGE_ADJUDICATION_PERFORMED": False,
        "PROVEN_OCCURRENCE_IDENTITY_COUNT": 0,
        "PROVEN_PARENTAGE_COUNT": 0,
        "RESIDUAL_CLOSE_PERFORMED": False,
        "SUPERSESSION_ADJUDICATION_PERFORMED": False,
        "TARGET_AUTHORITY": "NONE",
        "WINNER_SELECTED_COUNT": 0,
        "authority": ADJUDICATION_AUTHORITY,
    }


def _occurrence_outcome(
    candidate: dict[str, Any],
    *,
    in_competing_set: bool,
) -> tuple[str, list[str]]:
    dispositions = set(candidate["existing_disposition"])
    endpoint = str(candidate["endpoint_string"])
    locus = str(candidate["source_locus_availability"])
    reasons: list[str] = ["DISPOSITION_DO_NOT_BIND", "INSUFFICIENT_POSITIVE_EVIDENCE"]
    if "INVENTED_OR_SIDECAR_CONSTRUCTED_STRING" in dispositions:
        reasons.extend(["SIDECAR_CONSTRUCTED", "LOCUS_ABSENT"])
        if in_competing_set:
            reasons.append("COMPETING_SET")
            reasons.append("STRING_REUSE_NOT_OCCURRENCE_IDENTITY")
        if "AMBIGUOUS_BINDING" in dispositions:
            reasons.append("AMBIGUOUS_BINDING")
            return "AMBIGUOUS_COMPETING", _dedupe_reasons(reasons)
        return "NOT_BINDABLE_AS_OCCURRENCE", _dedupe_reasons(reasons)
    if "AMBIGUOUS_BINDING" in dispositions:
        reasons.extend(["AMBIGUOUS_BINDING", "COMPETING_SET", "LOCUS_ABSENT"])
        return "AMBIGUOUS_COMPETING", _dedupe_reasons(reasons)
    if "LAYER1_MARKER_REFERENCE_ONLY" in dispositions:
        reasons.extend(["MARKER_REFERENCE_ONLY", "NI_APPLIES"])
        if endpoint.startswith("occ-"):
            reasons.append("CORPUS_SHA_NOT_OCCURRENCE_PROOF")
        return "NOT_BINDABLE_AS_OCCURRENCE", _dedupe_reasons(reasons)
    if "NAVIGATION_ALIAS_ONLY" in dispositions:
        reasons.extend(["NAVIGATION_ONLY", "ALIAS_NOT_OCCURRENCE", "NI_APPLIES", "CLASS_CROSSING"])
        if locus == LOCUS_ABSENT:
            reasons.append("LOCUS_ABSENT")
        return "NAVIGATION_LINK_ONLY", _dedupe_reasons(reasons)
    if "OVERLAY_REFERENCE_ONLY" in dispositions:
        reasons.extend(["OVERLAY_NOT_OCCURRENCE", "LOCUS_ABSENT", "NI_APPLIES"])
        if in_competing_set:
            reasons.extend(
                [
                    "COMPETING_SET",
                    "STRING_REUSE_NOT_DUPLICATE_RECORD",
                    "STRING_REUSE_NOT_OCCURRENCE_IDENTITY",
                    "EPOCH_NOT_CURRENTNESS",
                    "EPOCH_NOT_SUPERSESSION",
                ]
            )
        return "NOT_BINDABLE_AS_OCCURRENCE", _dedupe_reasons(reasons)
    if "DOCUMENTARY_STRING_ONLY" in dispositions:
        reasons.extend(["LOCUS_ABSENT", "INSUFFICIENT_POSITIVE_EVIDENCE"])
        if in_competing_set:
            reasons.extend(["COMPETING_SET", "STRING_REUSE_NOT_OCCURRENCE_IDENTITY"])
        return "NOT_BINDABLE_AS_OCCURRENCE", _dedupe_reasons(reasons)
    _fail("OCCURRENCE_OUTCOME", f"unclassified candidate {candidate['derived_record_id']}")
    raise AssertionError("unreachable")


def _dedupe_reasons(reasons: list[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for code in reasons:
        if code not in REASON_CODES:
            _fail("REASON_CODE", f"unstable reason code {code}")
        if code not in seen:
            seen.add(code)
            ordered.append(code)
    return ordered


def _unadjudicated_reasons(dimension: str) -> list[str]:
    reasons = ["DIMENSION_NOT_AUTHORIZED", "INSUFFICIENT_POSITIVE_EVIDENCE"]
    if dimension == "PARENTAGE":
        reasons.append("PARENT_HINT_NOT_PARENTAGE")
    elif dimension == "DEPENDENCY":
        reasons.append("MECHANICAL_ORDER_NOT_DEPENDENCY")
    elif dimension == "CURRENTNESS":
        reasons.append("EPOCH_NOT_CURRENTNESS")
    elif dimension == "SUPERSESSION":
        reasons.append("EPOCH_NOT_SUPERSESSION")
    elif dimension == "WINNER_SELECTION":
        reasons.append("LATER_NOT_WINNER")
    elif dimension == "AUTHORITY":
        reasons.append("RESIDUAL_STATUS_NOT_ADJUDICATION_OUTCOME")
    elif dimension == "DUPLICATION":
        reasons.append("STRING_REUSE_NOT_DUPLICATE_RECORD")
    elif dimension == "NAVIGATION_LINKAGE":
        reasons.append("NAVIGATION_ONLY")
    elif dimension == "CHRONOLOGY":
        reasons.append("MECHANICAL_ORDER_NOT_DEPENDENCY")
    return _dedupe_reasons(reasons)


def build_adjudication_contract(
    projection: dict[str, Any] | None = None,
    *,
    repo_root: Path | None = None,
) -> AdjudicationContract:
    guards = AdjudicationGuardProgram()
    loaded = projection or load_candidate_projection(repo_root)
    candidates: list[dict[str, Any]] = list(loaded["candidates"])
    layer3: list[dict[str, Any]] = list(loaded["layer3"])
    residual_status = {
        residual_id: "OPEN"
        for residual_id in (*ADJUDICATION_OPEN_CLUSTER, *ADJUDICATION_MUST_REMAIN_OPEN)
    }
    observed_residuals = dict(loaded["residual_status"])
    for residual_id, status in residual_status.items():
        if observed_residuals.get(residual_id) != "OPEN":
            guards.assert_no_residual_close(
                performed=True,
                residual_status=observed_residuals,
            )
        residual_status[residual_id] = status
    candidate_sha = str(loaded["candidate_index_sha256"])
    relation_type_by_id = {row["relation_id"]: str(row["relation_type"]) for row in layer3}

    if len(candidates) != EXPECTED_CANDIDATE_COUNT:
        _fail("CANDIDATE_POPULATION", f"{len(candidates)} != 244")
    for candidate in candidates:
        if candidate.get("authority") != ADJUDICATION_AUTHORITY:
            guards.assert_authority_none(str(candidate.get("authority")))
        if candidate.get("output_canonical") is True:
            guards.assert_output_not_canonical(True)
        if candidate.get("occurrence_binding_proven") is True:
            guards.assert_no_proven_occurrence(count=1, detail=candidate["derived_record_id"])
        if candidate.get("candidate_state") != "UNRESOLVED":
            _fail(
                "CANDIDATE_STATE",
                f"input candidate_state mutated: {candidate['derived_record_id']}",
            )
        _validate_loci(candidate, guards)

    by_string: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        by_string[str(candidate["endpoint_string"])].append(candidate)
    competing_strings = {key for key, rows in by_string.items() if len(rows) > 1}
    if competing_strings != set(KNOWN_COMPETING_ENDPOINT_STRINGS):
        _fail(
            "COMPETING_SET",
            f"competing strings {sorted(competing_strings)} != expected",
        )

    competing_sets: list[CompetingSetRecord] = []
    candidate_to_set: dict[str, str] = {}
    for set_order, endpoint_string in enumerate(sorted(competing_strings)):
        members = sorted(
            by_string[endpoint_string],
            key=lambda row: str(row["derived_record_id"]),
        )
        member_ids = [str(row["derived_record_id"]) for row in members]
        ambiguous_ids = [
            str(row["derived_record_id"])
            for row in members
            if "AMBIGUOUS_BINDING" in row["existing_disposition"]
        ]
        set_id = mint_transformation_local_id(
            kind="adj-cset",
            source_order=set_order,
            sidecar_stable_suffix=_sanitize_suffix(endpoint_string),
        )
        for member_id in member_ids:
            candidate_to_set[member_id] = set_id
        competing_sets.append(
            CompetingSetRecord(
                ambiguity_set_id=set_id,
                member_candidate_ids=member_ids,
                shared_endpoint_string=endpoint_string,
                candidate_count=len(member_ids),
                duplicate_record=False,
                identity_resolved=False,
                resolution_status="UNRESOLVED",
                competing_set_kind=competing_set_kind(endpoint_string),
                original_ambiguous_binding_member_count=len(ambiguous_ids),
                original_ambiguous_binding_member_ids=ambiguous_ids,
                source_sha256=BOUND_SOURCE_SHA256,
                sidecar_sha256=BOUND_SIDECAR_SHA256,
            )
        )
    member_count = sum(row.candidate_count for row in competing_sets)
    if len(competing_sets) != EXPECTED_COMPETING_SET_COUNT:
        _fail("COMPETING_SET", f"set count {len(competing_sets)} != 8")
    if member_count != EXPECTED_COMPETING_MEMBER_COUNT:
        _fail("COMPETING_SET", f"member count {member_count} != 18")

    family_counts: Counter[str] = Counter()
    evidence_records: list[EvidenceRecord] = []
    decision_records: list[AdjudicationDecisionRecord] = []
    candidate_results: list[CandidateAdjudicationResult] = []
    evidence_order = 0
    decision_order = 0
    original_ambiguous_ids: list[str] = []

    for candidate in candidates:
        candidate_id = str(candidate["derived_record_id"])
        endpoint = str(candidate["endpoint_string"])
        family = classify_candidate_family(endpoint, competing_strings)
        family_counts[family] += 1
        relation_type = relation_type_by_id[str(candidate["relation_id"])]
        in_competing = candidate_id in candidate_to_set
        original_ambiguous = "AMBIGUOUS_BINDING" in candidate["existing_disposition"]
        if original_ambiguous:
            original_ambiguous_ids.append(candidate_id)
        outcome, occ_reasons = _occurrence_outcome(candidate, in_competing_set=in_competing)
        guards.assert_outcome_not_proven(outcome, candidate_id)

        negative_ids_by_dimension: dict[str, list[str]] = defaultdict(list)
        locus = _first_present_locus(candidate)
        locus_availability = str(candidate["source_locus_availability"])

        def _emit_evidence(
            *,
            record_class: str,
            reason_code: str,
            applicable: bool,
            reference: str,
            epistemic_class: str,
            source_provenance: str,
            dimension: str = "OCCURRENCE_IDENTITY",
            human_detail: str = "",
        ) -> str:
            nonlocal evidence_order
            evidence_id = mint_transformation_local_id(
                kind="adj-ev",
                source_order=evidence_order,
                sidecar_stable_suffix=f"{candidate_id}-{reason_code}-{record_class}",
            )
            evidence_order += 1
            use_locus = locus if locus_availability == LOCUS_PRESENT and applicable else None
            availability = LOCUS_PRESENT if use_locus is not None else LOCUS_ABSENT
            evidence_records.append(
                EvidenceRecord(
                    evidence_id=evidence_id,
                    candidate_id=candidate_id,
                    dimension=dimension,
                    epistemic_class=epistemic_class,
                    record_class=record_class,
                    polarity=POLARITY_NEGATIVE,
                    source_sha256=BOUND_SOURCE_SHA256,
                    sidecar_sha256=BOUND_SIDECAR_SHA256,
                    locus_availability=availability,
                    locus=use_locus,
                    evidence_reference=reference,
                    reason_code=reason_code,
                    applicable=applicable,
                    source_provenance=source_provenance,
                    human_detail=human_detail,
                )
            )
            if applicable:
                negative_ids_by_dimension[dimension].append(evidence_id)
            return evidence_id

        for ni_id, left, right in (NON_IDENTITY_BY_ID[ni] for ni in NON_IDENTITY_IDS):
            applicable = _ni_applicable(ni_id, candidate, relation_type)
            _emit_evidence(
                record_class="NON_IDENTITY_CONSTRAINT",
                reason_code="NI_APPLIES" if applicable else "INSUFFICIENT_POSITIVE_EVIDENCE",
                applicable=applicable,
                reference=f"{ni_id}:{left}!={right}",
                epistemic_class="PRIOR_ADJUDICATION_REFERENCE",
                source_provenance="NON_IDENTITY_STATEMENTS",
                human_detail=f"{ni_id} applicable={str(applicable).lower()}",
            )
        for code in DISPOSITION_DISQUALIFIERS:
            applicable = _disqualifier_applicable(code, candidate, relation_type)
            reason = "DISPOSITION_DO_NOT_BIND"
            if code == "INVENTED_OR_SIDECAR_CONSTRUCTED_STRING":
                reason = "SIDECAR_CONSTRUCTED"
            elif code == "LAYER1_MARKER_REFERENCE_ONLY":
                reason = "MARKER_REFERENCE_ONLY"
            elif code == "AMBIGUOUS_BINDING":
                reason = "AMBIGUOUS_BINDING"
            elif code == "NAVIGATION_ONLY":
                reason = "NAVIGATION_ONLY"
            elif code == "DR-002":
                reason = "MARKER_REFERENCE_ONLY"
            elif code == "DR-003":
                reason = "NI_APPLIES"
            _emit_evidence(
                record_class="DISPOSITION_DISQUALIFIER",
                reason_code=reason,
                applicable=applicable,
                reference=code,
                epistemic_class="STRUCTURAL_DERIVATION",
                source_provenance="EXISTING_DISPOSITION_OBSERVATION",
                human_detail=f"{code} applicable={str(applicable).lower()}",
            )
        if in_competing:
            _emit_evidence(
                record_class="COMPETING_SET_MEMBERSHIP",
                reason_code="COMPETING_SET",
                applicable=True,
                reference=candidate_to_set[candidate_id],
                epistemic_class="STRUCTURAL_DERIVATION",
                source_provenance="SHARED_ENDPOINT_STRING",
                human_detail="string reuse is not occurrence identity",
            )

        set_presence = (
            PresenceTagged.present(candidate_to_set[candidate_id])
            if in_competing
            else PresenceTagged.absent()
        )
        for dimension in ADJUDICATION_DIMENSIONS:
            executed = dimension in EXECUTED_CLASSIFY_DISQUALIFY_DIMENSIONS
            if executed:
                dim_outcome = outcome
                dim_reasons = list(occ_reasons)
                dim_negative = list(negative_ids_by_dimension.get("OCCURRENCE_IDENTITY", []))
            else:
                dim_outcome = "UNADJUDICATED"
                dim_reasons = _unadjudicated_reasons(dimension)
                dim_negative = []
            guards.assert_outcome_not_proven(dim_outcome, f"{candidate_id}:{dimension}")
            decision_id = mint_transformation_local_id(
                kind="adj-dec",
                source_order=decision_order,
                sidecar_stable_suffix=f"{candidate_id}-{dimension}",
            )
            decision_order += 1
            decision_records.append(
                AdjudicationDecisionRecord(
                    decision_id=decision_id,
                    candidate_id=candidate_id,
                    dimension=dimension,
                    outcome=dim_outcome,
                    reason_codes=dim_reasons,
                    positive_evidence_ids=[],
                    negative_evidence_ids=dim_negative,
                    ambiguity_set_id=set_presence,
                    input_source_sha256=BOUND_SOURCE_SHA256,
                    input_sidecar_sha256=BOUND_SIDECAR_SHA256,
                    input_candidate_index_sha256=candidate_sha,
                    generator_id=ADJUDICATION_GENERATOR_ID,
                    contract_version=ADJUDICATION_CONTRACT_VERSION,
                    operator_authorization_scope=OPERATOR_AUTHORIZATION_SCOPE,
                    dimension_executed=executed,
                )
            )

        candidate_results.append(
            CandidateAdjudicationResult(
                candidate_id=candidate_id,
                endpoint_string=endpoint,
                candidate_family=family,
                candidate_state=str(candidate["candidate_state"]),
                occurrence_binding_proven=False,
                original_ambiguous_binding=original_ambiguous,
                original_dispositions=list(candidate["existing_disposition"]),
                competing_set_id=set_presence,
                occurrence_identity_outcome=outcome,
                source_locus_availability=locus_availability,
                residual_ids=list(candidate["residual_ids"]),
            )
        )

    if len(family_counts) != EXPECTED_CANDIDATE_FAMILY_COUNT:
        _fail("CANDIDATE_FAMILY", f"family count {len(family_counts)} != 11")
    missing_families = [name for name in CANDIDATE_FAMILIES if family_counts[name] == 0]
    if missing_families:
        _fail("CANDIDATE_FAMILY", f"empty families {missing_families}")
    extra_families = [name for name in family_counts if name not in CANDIDATE_FAMILIES]
    if extra_families:
        _fail("CANDIDATE_FAMILY", f"unexpected families {extra_families}")
    if len(original_ambiguous_ids) != EXPECTED_ORIGINAL_AMBIGUOUS_BINDING_COUNT:
        _fail(
            "AMBIGUOUS_UNDERCOUNT",
            f"AMBIGUOUS_BINDING {len(original_ambiguous_ids)} != 6",
        )

    proven_count = sum(1 for row in decision_records if row.outcome == "PROVEN_OCCURRENCE_IDENTITY")
    ambiguous_outcomes = sum(
        1 for row in candidate_results if row.occurrence_identity_outcome == "AMBIGUOUS_COMPETING"
    )
    guards.assert_no_proven_occurrence(count=proven_count, detail="evaluator")
    guards.assert_silent_ambiguous_normalization(
        original_ambiguous_count=len(original_ambiguous_ids),
        competing_member_count=member_count,
        ambiguous_outcomes=ambiguous_outcomes,
    )
    guards.assert_no_parentage(performed=False, count=0, detail="evaluator")
    guards.assert_no_currentness(performed=False, detail="evaluator")
    guards.assert_no_supersession(performed=False, detail="evaluator")
    guards.assert_no_winner(count=0, detail="evaluator")
    guards.assert_no_residual_close(performed=False, residual_status=residual_status)
    guards.assert_authority_none(ADJUDICATION_AUTHORITY)
    guards.assert_output_not_canonical(False)

    if any(row.positive_evidence_ids for row in decision_records):
        _fail("POSITIVE_EVIDENCE", "positive evidence emitted under derived-only GO")
    if any(row.candidate_state != "UNRESOLVED" for row in candidate_results):
        _fail("CANDIDATE_STATE", "evaluator mutated candidate_state")

    family_inventory = {
        "CANDIDATE_FAMILY_COUNT": len(family_counts),
        "REFERENCED_OVERLAY_CLASS_FAMILY_COUNT": EXPECTED_REFERENCED_OVERLAY_CLASS_FAMILY_COUNT,
        "authority": ADJUDICATION_AUTHORITY,
        "counts": {name: int(family_counts[name]) for name in CANDIDATE_FAMILIES},
        "families": list(CANDIDATE_FAMILIES),
        "output_canonical": False,
        "overlay_class_order_referenced": list(OVERLAY_CLASS_ORDER),
        "taxonomy": "CANDIDATE_PROJECTION_FAMILIES_V1",
    }
    counts = {
        "CANDIDATE_FAMILY_COUNT": len(family_counts),
        "COMPETING_CANDIDATE_MEMBER_COUNT": member_count,
        "COMPETING_CANDIDATE_SET_COUNT": len(competing_sets),
        "CURRENTNESS_ADJUDICATION_PERFORMED": False,
        "DECISION_RECORD_COUNT": len(decision_records),
        "NEGATIVE_EVIDENCE_RECORD_COUNT": len(evidence_records),
        "OCCURRENCE_BINDING_CANDIDATE_COUNT": len(candidate_results),
        "ORIGINAL_AMBIGUOUS_BINDING_CANDIDATE_COUNT": len(original_ambiguous_ids),
        "OUTPUT_CANONICAL": False,
        "PROVEN_OCCURRENCE_IDENTITY_COUNT": proven_count,
        "PROVEN_PARENTAGE_COUNT": 0,
        "RESIDUAL_CLOSE_PERFORMED": False,
        "SEMANTIC_BINDING_PERFORMED": False,
        "SUPERSESSION_ADJUDICATION_PERFORMED": False,
        "WINNER_SELECTED_COUNT": 0,
    }
    return AdjudicationContract(
        dimension_model=_dimension_model(),
        evidence_records=evidence_records,
        competing_sets=competing_sets,
        candidate_results=candidate_results,
        decision_records=decision_records,
        non_inference_audit=_non_inference_audit(),
        execution_boundaries=_execution_boundaries(),
        counts=counts,
        residual_status=residual_status,
        generated_from_source_sha256=BOUND_SOURCE_SHA256,
        generated_from_sidecar_sha256=BOUND_SIDECAR_SHA256,
        generated_from_candidate_index_sha256=candidate_sha,
        family_inventory=family_inventory,
        layer_id=ADJUDICATION_LAYER_ID,
        generator_id=ADJUDICATION_GENERATOR_ID,
        output_role=ADJUDICATION_OUTPUT_ROLE,
        authority=ADJUDICATION_AUTHORITY,
        output_canonical=False,
        semantic_binding_performed=False,
        residual_close_performed=False,
        currentness_adjudication_performed=False,
        supersession_adjudication_performed=False,
        occurrence_binding_proven_count=0,
        proven_occurrence_identity_count=proven_count,
        proven_parentage_count=0,
        winner_selected_count=0,
    )
