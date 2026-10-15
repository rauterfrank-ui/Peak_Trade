"""CURRENT-only relevance filtering with explicit classification."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any

from scripts.ops.ghv_forensic_whole_system_crosswalk_v1.constants_v1 import (
    ATLAS_EPISTEMIC_EXCLUDE,
    ATLAS_RELATION_EPISTEMIC_ALLOW,
    CURRENT_CENSUS_STATUS_ALLOW,
    CURRENT_EPISTEMIC_ALLOW,
    CURRENT_LANDSCAPE_STATUS_ALLOW,
)


class CurrentRelevanceState(str, Enum):
    CURRENT_VERIFIED = "CURRENT_VERIFIED"
    CURRENT_CONDITIONAL = "CURRENT_CONDITIONAL"
    NON_CURRENT = "NON_CURRENT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CurrentRelevanceVerdict:
    state: CurrentRelevanceState
    current_relevance_evidence: str
    evidence_source: str
    evidence_revision: str
    validation_status: str
    activation_condition: str | None

    def to_record(self) -> dict[str, Any]:
        return {
            "CURRENT_RELEVANCE_STATE": self.state.value,
            "CURRENT_RELEVANCE_EVIDENCE": self.current_relevance_evidence,
            "EVIDENCE_SOURCE": self.evidence_source,
            "EVIDENCE_REVISION": self.evidence_revision,
            "VALIDATION_STATUS": self.validation_status,
            "ACTIVATION_CONDITION": self.activation_condition,
        }


def _unknown(kind: str, detail: str) -> CurrentRelevanceVerdict:
    return CurrentRelevanceVerdict(
        state=CurrentRelevanceState.UNKNOWN,
        current_relevance_evidence=f"insufficient_current_proof:{kind}:{detail}",
        evidence_source="none",
        evidence_revision="",
        validation_status="UNKNOWN",
        activation_condition=None,
    )


def classify_census_object(
    obj: dict[str, Any],
    *,
    evidence_revision: str,
) -> CurrentRelevanceVerdict:
    artifact = "config/governance/current_system_census_graph_v1/source_v1.json"
    ep = obj.get("epistemic_status")
    cs = obj.get("current_status")
    if ep is None or cs is None:
        return _unknown("census_object", "missing_status_fields")
    if ep not in CURRENT_EPISTEMIC_ALLOW:
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.NON_CURRENT,
            current_relevance_evidence=f"epistemic_status={ep}",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="EXCLUDED",
            activation_condition=None,
        )
    if cs not in CURRENT_CENSUS_STATUS_ALLOW:
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.NON_CURRENT,
            current_relevance_evidence=f"current_status={cs}",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="EXCLUDED",
            activation_condition=None,
        )
    if obj.get("primary_class") == "OFFLINE_RESEARCH":
        if obj.get("productive_reachability"):
            return CurrentRelevanceVerdict(
                state=CurrentRelevanceState.CURRENT_CONDITIONAL,
                current_relevance_evidence="OFFLINE_RESEARCH_with_productive_reachability",
                evidence_source=artifact,
                evidence_revision=evidence_revision,
                validation_status="PASS",
                activation_condition="productive_reachability=true",
            )
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.NON_CURRENT,
            current_relevance_evidence="OFFLINE_RESEARCH_without_productive_reachability",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="EXCLUDED",
            activation_condition=None,
        )
    return CurrentRelevanceVerdict(
        state=CurrentRelevanceState.CURRENT_VERIFIED,
        current_relevance_evidence="census_PROVEN_CURRENT_object",
        evidence_source=artifact,
        evidence_revision=evidence_revision,
        validation_status="PASS",
        activation_condition=None,
    )


def classify_census_edge(
    edge: dict[str, Any],
    *,
    evidence_revision: str,
    endpoint_verdicts: dict[str, CurrentRelevanceVerdict],
) -> CurrentRelevanceVerdict:
    artifact = "config/governance/current_system_census_graph_v1/source_v1.json"
    ep = edge.get("epistemic_status")
    if ep not in CURRENT_EPISTEMIC_ALLOW:
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.NON_CURRENT,
            current_relevance_evidence=f"edge_epistemic_status={ep}",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="EXCLUDED",
            activation_condition=None,
        )
    for side in ("source_object", "target_object"):
        ref = edge.get(side)
        if not ref or not str(ref).startswith("SO-"):
            continue
        ev = endpoint_verdicts.get(str(ref))
        if ev is None:
            return _unknown("census_edge_endpoint", f"missing_endpoint:{ref}")
        if ev.state in (CurrentRelevanceState.NON_CURRENT, CurrentRelevanceState.UNKNOWN):
            return CurrentRelevanceVerdict(
                state=CurrentRelevanceState.NON_CURRENT,
                current_relevance_evidence=f"endpoint_not_current:{ref}={ev.state.value}",
                evidence_source=artifact,
                evidence_revision=evidence_revision,
                validation_status="EXCLUDED",
                activation_condition=None,
            )
        if ev.state == CurrentRelevanceState.CURRENT_CONDITIONAL:
            return CurrentRelevanceVerdict(
                state=CurrentRelevanceState.CURRENT_CONDITIONAL,
                current_relevance_evidence="edge_connects_conditional_endpoint",
                evidence_source=artifact,
                evidence_revision=evidence_revision,
                validation_status="PASS",
                activation_condition=ev.activation_condition,
            )
    contract = edge.get("contract_or_payload")
    flow = edge.get("flow_type")
    if flow == "DECISION_FLOW" and not (contract and str(contract).strip()):
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.CURRENT_VERIFIED,
            current_relevance_evidence="DECISION_FLOW_present_but_handoff_unresolved",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="UNRESOLVED_TYPED_EDGE",
            activation_condition=None,
        )
    return CurrentRelevanceVerdict(
        state=CurrentRelevanceState.CURRENT_VERIFIED,
        current_relevance_evidence="census_semantic_edge_with_current_endpoints",
        evidence_source=artifact,
        evidence_revision=evidence_revision,
        validation_status="PASS",
        activation_condition=None,
    )


def classify_landscape_surface(
    surface: dict[str, Any],
    *,
    evidence_revision: str,
) -> CurrentRelevanceVerdict:
    artifact = "config/governance/current_universe_landscape_snapshot_v1/source_v1.json"
    status = surface.get("status")
    if status not in CURRENT_LANDSCAPE_STATUS_ALLOW:
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.NON_CURRENT,
            current_relevance_evidence=f"status={status}",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="EXCLUDED",
            activation_condition=None,
        )
    return CurrentRelevanceVerdict(
        state=CurrentRelevanceState.CURRENT_VERIFIED,
        current_relevance_evidence="landscape_PROVEN_CURRENT_surface",
        evidence_source=artifact,
        evidence_revision=evidence_revision,
        validation_status="PASS",
        activation_condition=None,
    )


def _normalize_repo_path(path: str) -> str:
    return str(path).strip().replace("\\", "/")


def build_census_anchor_index(
    census_objects: list[dict[str, Any]],
    *,
    evidence_revision: str,
) -> tuple[set[str], set[str]]:
    """Census object ids and repo-relative paths eligible as CURRENT anchors."""
    obj_ids: set[str] = set()
    paths: set[str] = set()
    for obj in census_objects:
        verdict = classify_census_object(obj, evidence_revision=evidence_revision)
        if verdict.state not in (
            CurrentRelevanceState.CURRENT_VERIFIED,
            CurrentRelevanceState.CURRENT_CONDITIONAL,
        ):
            continue
        obj_ids.add(str(obj["object_id"]))
        for p in obj.get("paths") or []:
            paths.add(_normalize_repo_path(str(p)))
    return obj_ids, paths


def atlas_entity_has_current_anchor(
    entity: dict[str, Any],
    *,
    census_object_ids: set[str],
    census_paths: set[str],
) -> tuple[bool, str]:
    census_link = entity.get("census_object_id") or entity.get("census_object")
    if census_link and str(census_link) in census_object_ids:
        return True, f"census_object_id={census_link}"
    for field in ("evidence_sources", "source_paths", "authority_sources"):
        for raw in entity.get(field) or []:
            norm = _normalize_repo_path(str(raw))
            if norm in census_paths:
                return True, f"path_anchor:{norm}"
    return False, "no_verified_census_anchor"


def classify_atlas_entity(
    entity: dict[str, Any],
    *,
    evidence_revision: str,
    census_object_ids: set[str],
    census_paths: set[str],
) -> CurrentRelevanceVerdict:
    artifact = "docs/system_atlas/entities/catalog.yaml"
    epistemic = str(entity.get("epistemic_class") or entity.get("epistemic_status") or "").upper()
    if epistemic in ATLAS_EPISTEMIC_EXCLUDE or epistemic == "HISTORICAL":
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.NON_CURRENT,
            current_relevance_evidence=f"atlas_epistemic_excluded:{epistemic}",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="EXCLUDED",
            activation_condition=None,
        )
    if entity.get("current_canonical") is False:
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.NON_CURRENT,
            current_relevance_evidence="current_canonical=false",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="EXCLUDED",
            activation_condition=None,
        )
    current_status = str(entity.get("current_status") or "")
    if current_status.upper().startswith("RETIRED"):
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.NON_CURRENT,
            current_relevance_evidence=f"current_status={current_status}",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="EXCLUDED",
            activation_condition=None,
        )
    if entity.get("current_canonical") is not True:
        return _unknown("atlas_entity", "missing_current_canonical_true")
    anchored, anchor_detail = atlas_entity_has_current_anchor(
        entity,
        census_object_ids=census_object_ids,
        census_paths=census_paths,
    )
    if not anchored:
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.UNKNOWN,
            current_relevance_evidence="atlas_without_census_path_anchor",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="UNKNOWN",
            activation_condition=None,
        )
    return CurrentRelevanceVerdict(
        state=CurrentRelevanceState.CURRENT_VERIFIED,
        current_relevance_evidence=f"atlas_with_anchor:{anchor_detail}",
        evidence_source=artifact,
        evidence_revision=evidence_revision,
        validation_status="PASS",
        activation_condition=None,
    )


def classify_atlas_relation(
    rel: dict[str, Any],
    *,
    evidence_revision: str,
    included_entity_ids: set[str],
) -> CurrentRelevanceVerdict:
    artifact = "docs/system_atlas/relations/structural.yaml"
    status = str(rel.get("epistemic_status") or "").upper()
    if status in ATLAS_EPISTEMIC_EXCLUDE:
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.NON_CURRENT,
            current_relevance_evidence=f"relation_epistemic_status={status}",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="EXCLUDED",
            activation_condition=None,
        )
    if status and status not in ATLAS_RELATION_EPISTEMIC_ALLOW:
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.UNKNOWN,
            current_relevance_evidence=f"relation_epistemic_unverified:{status}",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="UNKNOWN",
            activation_condition=None,
        )
    src, tgt = str(rel.get("source") or ""), str(rel.get("target") or "")
    if src not in included_entity_ids or tgt not in included_entity_ids:
        return CurrentRelevanceVerdict(
            state=CurrentRelevanceState.NON_CURRENT,
            current_relevance_evidence="endpoint_not_in_current_atlas_anchor_set",
            evidence_source=artifact,
            evidence_revision=evidence_revision,
            validation_status="EXCLUDED",
            activation_condition=None,
        )
    if not rel.get("evidence_sources") and not rel.get("authority_sources"):
        return _unknown("atlas_relation", "missing_edge_evidence_sources")
    return CurrentRelevanceVerdict(
        state=CurrentRelevanceState.CURRENT_VERIFIED,
        current_relevance_evidence="atlas_structural_relation_with_current_endpoints",
        evidence_source=artifact,
        evidence_revision=evidence_revision,
        validation_status="PASS",
        activation_condition=None,
    )


def verdict_includable_in_graph(verdict: CurrentRelevanceVerdict) -> bool:
    return verdict.state in (
        CurrentRelevanceState.CURRENT_VERIFIED,
        CurrentRelevanceState.CURRENT_CONDITIONAL,
    )


def exclusion_reason_from_verdict(verdict: CurrentRelevanceVerdict) -> str:
    return verdict.current_relevance_evidence
