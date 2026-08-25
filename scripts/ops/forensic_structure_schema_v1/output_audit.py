"""Adversarial non-inference audit of the actually serialized retained output."""

from __future__ import annotations

from typing import Any

from scripts.ops.forensic_structure_schema_v1.constants import (
    CLOSED_JOIN_SET,
    DEFAULT_AUTHORITY_STATUS,
    DEFAULT_CURRENTNESS_STATUS,
    DEFAULT_GATE_MEMBERSHIP,
    DEFAULT_PRIMARY_LABEL,
    DEFAULT_SEMANTIC_CONTAINER,
    DEFAULT_SUPERSESSION,
    DUAL_CLASS_OCCURRENCE_ID,
    EXPECTED_LOSSLESSNESS,
    EXPECTED_SOURCE_SHA256,
    HISTORICAL_FORENSIC_RECORD_SHA,
    HISTORICAL_LOCATOR_ROLE,
    HISTORICAL_LOCATOR_TOKEN_CLASS,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.guards import ORDERING_RELATION_TYPES


def _fail(rule: str, message: str) -> None:
    raise TransformationContractViolation(rule, message)


def _presence(field: dict[str, Any]) -> str:
    return str(field.get("presence"))


def audit_retained_output(
    *,
    dataset: dict[str, Any],
    losslessness_counts: dict[str, Any],
) -> dict[str, bool]:
    """Return named promotion flags. Every value must be false (no promotion)."""
    envelopes = dataset["semantic_envelopes"]
    relations = dataset["relation_envelopes"]
    flags = {
        "ORDERED_BEFORE_TO_DEPENDENCY": False,
        "ORDERED_AFTER_TO_DEPENDENCY": False,
        "PREFIX_EPOCH_SUCCEEDS_TO_DEPENDENCY": False,
        "H1_CONTAINMENT_TO_PARENTAGE": False,
        "VIEW_PARENTS_TO_PARENTAGE": False,
        "WRAPPER_CONTAINS_TO_SEMANTIC_CONTAINER": False,
        "CURRENT_TOKEN_TO_CURRENTNESS": False,
        "SHA_HEX_64_TO_SHA256": False,
        "SHA_HEX_40_TO_SHA1": False,
        "DOCUMENTARY_ENDPOINT_TO_OCCURRENCE_AUTO_BIND": False,
        "T5_RANGE_EXPANSION": False,
        "MULTILABEL_COLLAPSE": False,
        "FENCE_DUPLICATE_COLLAPSE": False,
        "TOKEN_DUPLICATE_COLLAPSE": False,
        "WRAPPER_MENTION_TO_INSTANCE": False,
        "NULL_FORENSIC_SHA_FILL": False,
        "T3_HEADING_REGION_FUSION": False,
        "KV_PACKET_SYNTHETIC_OCCURRENCE": False,
        "HISTORICAL_LOCATOR_NORMALIZATION": False,
        "AUTHORITY_PROMOTION": False,
        "GATE_MEMBERSHIP_INFERENCE": False,
        "SUPERSESSION_INFERENCE": False,
        "CONFLICT_WINNER_SELECTION": False,
    }

    for rel in relations:
        rtype = str(rel["relation_type"])
        if rtype in ORDERING_RELATION_TYPES and rel["is_dependency"] is True:
            if rtype in {"ORDERED_BEFORE", "STRUCTURAL_ORDERED_BEFORE"}:
                flags["ORDERED_BEFORE_TO_DEPENDENCY"] = True
            elif rtype == "ORDERED_AFTER":
                flags["ORDERED_AFTER_TO_DEPENDENCY"] = True
            elif rtype == "PREFIX_EPOCH_SUCCEEDS":
                flags["PREFIX_EPOCH_SUCCEEDS_TO_DEPENDENCY"] = True
            _fail("D1", f"{rel['relation_id']} ordering promoted to dependency")
        if rtype == "WRAPPER_CONTAINS" and rel["semantic_container"] != DEFAULT_SEMANTIC_CONTAINER:
            flags["WRAPPER_CONTAINS_TO_SEMANTIC_CONTAINER"] = True
            _fail("D5", f"{rel['relation_id']} WRAPPER_CONTAINS became semantic container")
        if rtype == "EXPLICIT_CONFLICT" and rel["winner_selected"] is True:
            flags["CONFLICT_WINNER_SELECTION"] = True
            _fail("C5", f"{rel['relation_id']} winner selected")
        if rel["authority_status"] != DEFAULT_AUTHORITY_STATUS:
            flags["AUTHORITY_PROMOTION"] = True
            _fail("C9", f"{rel['relation_id']} authority promoted")
        if rel["gate_membership"] != DEFAULT_GATE_MEMBERSHIP:
            flags["GATE_MEMBERSHIP_INFERENCE"] = True
            _fail("D12", f"{rel['relation_id']} gate inferred")
        if rel["supersession"] != DEFAULT_SUPERSESSION:
            flags["SUPERSESSION_INFERENCE"] = True
            _fail("D13", f"{rel['relation_id']} supersession inferred")
        for side in ("from_binding", "to_binding"):
            binding = rel[side]
            kind = str(binding["kind"])
            if kind not in CLOSED_JOIN_SET:
                _fail("UNAUTHORIZED_JOIN", f"{rel['relation_id']} {side} kind {kind}")
            if (
                kind
                in {
                    "DOCUMENTARY_STRING_ENDPOINT",
                    "EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY",
                }
                and binding.get("unresolved_to_occurrence") is not True
            ):
                flags["DOCUMENTARY_ENDPOINT_TO_OCCURRENCE_AUTO_BIND"] = True
                _fail("SW-R-004", f"{rel['relation_id']} {side} auto-bound")

    token_ids: list[str] = []
    historical_locator_count = 0
    kv_null_occ = 0
    for env in envelopes:
        if env["authority_status"] != DEFAULT_AUTHORITY_STATUS:
            flags["AUTHORITY_PROMOTION"] = True
            _fail("C9", f"{env['transformation_local_id']} authority promoted")
        if env["gate_membership"] != DEFAULT_GATE_MEMBERSHIP:
            flags["GATE_MEMBERSHIP_INFERENCE"] = True
            _fail("D12", f"{env['transformation_local_id']} gate inferred")
        if env["supersession"] != DEFAULT_SUPERSESSION:
            flags["SUPERSESSION_INFERENCE"] = True
            _fail("D13", f"{env['transformation_local_id']} supersession inferred")
        if env["semantic_container"] != DEFAULT_SEMANTIC_CONTAINER:
            flags["H1_CONTAINMENT_TO_PARENTAGE"] = True
            _fail("SW-R-005", f"{env['transformation_local_id']} parentage inferred")
        if env["primary_label"] != DEFAULT_PRIMARY_LABEL:
            flags["MULTILABEL_COLLAPSE"] = True
            _fail("C4", f"{env['transformation_local_id']} primary_label invented")
        if env["winner_selected"] is True:
            flags["CONFLICT_WINNER_SELECTION"] = True
            _fail("C5", f"{env['transformation_local_id']} winner selected")
        if env["currentness_status"] not in {DEFAULT_CURRENTNESS_STATUS, "historical"}:
            flags["CURRENT_TOKEN_TO_CURRENTNESS"] = True
            _fail("D8", f"{env['transformation_local_id']} currentness promoted")
        upgrade = env["currentness_upgrade"]
        if _presence(upgrade) == "present" and upgrade.get("value") is not False:
            flags["CURRENT_TOKEN_TO_CURRENTNESS"] = True
            _fail("D8", f"{env['transformation_local_id']} currentness_upgrade not false")
        hash_kind = env["hash_kind"]
        if _presence(hash_kind) == "present" and hash_kind.get("value") != "UNKNOWN":
            value = str(hash_kind.get("value"))
            if "SHA256" in value:
                flags["SHA_HEX_64_TO_SHA256"] = True
            if "SHA1" in value:
                flags["SHA_HEX_40_TO_SHA1"] = True
            _fail("D7", f"{env['transformation_local_id']} hash_kind={value}")
        classified = env["classified_source_line"]
        if env["overlay_class"] == "t5_cls_row" and _presence(classified) == "null":
            if classified.get("value") is not None:
                flags["T5_RANGE_EXPANSION"] = True
                _fail("SW-R-003", f"{env['transformation_local_id']} null line expanded")
        collapsed = env["collapsed"]
        if _presence(collapsed) == "present" and collapsed.get("value") is True:
            flags["MULTILABEL_COLLAPSE"] = True
            _fail("C4", f"{env['transformation_local_id']} collapsed=true")
        if env["overlay_class"] == "token_occurrence":
            token_field = env["token_occurrence_id"]
            if _presence(token_field) == "present":
                token_ids.append(str(token_field["value"]))
            token_class = env["token_class"]
            if (
                _presence(token_class) == "present"
                and token_class.get("value") == HISTORICAL_LOCATOR_TOKEN_CLASS
            ):
                historical_locator_count += 1
                normalized = env["normalized"]
                locator_role = env["locator_role"]
                if not (_presence(normalized) == "present" and normalized.get("value") is False):
                    flags["HISTORICAL_LOCATOR_NORMALIZATION"] = True
                    _fail("C8", f"{env['transformation_local_id']} locator normalized")
                if not (
                    _presence(locator_role) == "present"
                    and locator_role.get("value") == HISTORICAL_LOCATOR_ROLE
                ):
                    flags["HISTORICAL_LOCATOR_NORMALIZATION"] = True
                    _fail("C7", f"{env['transformation_local_id']} locator_role mutated")
        if env["overlay_class"] == "wrapper_mention":
            mention = env["instance_vs_mention"]
            if _presence(mention) == "present" and str(mention.get("value")) == "instance":
                flags["WRAPPER_MENTION_TO_INSTANCE"] = True
                _fail("TV-011", f"{env['transformation_local_id']} mention promoted")
        if env["overlay_class"] == "kv_packet":
            occ = env["layer1_occurrence_id"]
            if _presence(occ) != "null":
                flags["KV_PACKET_SYNTHETIC_OCCURRENCE"] = True
                _fail("DR-008", f"{env['transformation_local_id']} kv synthetic occ")
            kv_null_occ += 1
        binds = env["binds_blob_sha256"]
        if (
            env["overlay_class"] == "forensic_record"
            and _presence(binds) == "null"
            and binds.get("value") == EXPECTED_SOURCE_SHA256
        ):
            flags["NULL_FORENSIC_SHA_FILL"] = True
            _fail("SW-R-014", f"{env['transformation_local_id']} null SHA filled")
        if (
            env["overlay_class"] == "forensic_record"
            and _presence(binds) == "present"
            and binds.get("value") == EXPECTED_SOURCE_SHA256
            and HISTORICAL_FORENSIC_RECORD_SHA != EXPECTED_SOURCE_SHA256
        ):
            flags["NULL_FORENSIC_SHA_FILL"] = True
            _fail("SW-R-014", f"{env['transformation_local_id']} historical SHA replaced")

    if (
        losslessness_counts["FENCE_DUPLICATE_GROUPS"]
        != EXPECTED_LOSSLESSNESS["FENCE_DUPLICATE_GROUPS"]
    ):
        flags["FENCE_DUPLICATE_COLLAPSE"] = True
        _fail("C3", "fence duplicate groups collapsed")
    if len(token_ids) != len(set(token_ids)):
        flags["TOKEN_DUPLICATE_COLLAPSE"] = True
        _fail("C2", "token occurrence ids collapsed")
    if historical_locator_count != 50:
        flags["HISTORICAL_LOCATOR_NORMALIZATION"] = True
        _fail("C7", f"historical locator count {historical_locator_count} != 50")
    if (
        losslessness_counts["T3_HEADING_OUTSIDE_DECLARED_REGION_COUNT"]
        != EXPECTED_LOSSLESSNESS["T3_HEADING_OUTSIDE_DECLARED_REGION_COUNT"]
    ):
        flags["T3_HEADING_REGION_FUSION"] = True
        _fail("SW-R-015", "T3 heading/region fused")
    if kv_null_occ != EXPECTED_LOSSLESSNESS["KV_PACKET_COUNT"]:
        flags["KV_PACKET_SYNTHETIC_OCCURRENCE"] = True
        _fail("DR-008", "kv_packet count drift in retained envelopes")

    layer2 = [env for env in envelopes if env["overlay_class"] == "layer2"]
    dual = [
        env
        for env in layer2
        if _presence(env["layer1_occurrence_id"]) == "present"
        and env["layer1_occurrence_id"]["value"] == DUAL_CLASS_OCCURRENCE_ID
    ]
    if len(dual) != 2:
        _fail("SW-R-011", f"dual-class envelopes collapsed to {len(dual)}")
    if dual[0]["transformation_local_id"] == dual[1]["transformation_local_id"]:
        _fail("SW-R-011", "dual-class transformation_local_id collapsed")

    if dataset.get("output_authority") != DEFAULT_AUTHORITY_STATUS:
        flags["AUTHORITY_PROMOTION"] = True
        _fail("C9", "dataset output_authority promoted")
    if dataset.get("output_is_canonical") is True:
        flags["AUTHORITY_PROMOTION"] = True
        _fail("C9", "dataset claimed canonical")
    if "RESOLVED_BY_TRANSFORMATION" in str(dataset):
        _fail("STAGE_H", "output claims RESOLVED_BY_TRANSFORMATION")

    view_parentage = [
        rel
        for rel in relations
        if "PARENT" in str(rel["relation_type"]).upper()
        and rel["semantic_container"] != DEFAULT_SEMANTIC_CONTAINER
    ]
    if view_parentage:
        flags["VIEW_PARENTS_TO_PARENTAGE"] = True
        _fail("SW-R-009", "view parents adjudicated as parentage")

    views = dataset.get("navigation_views")
    if not isinstance(views, list) or len(views) != EXPECTED_LOSSLESSNESS["VIEW_COUNT"]:
        _fail("NAVIGATION_VIEW_RETENTION", "retained navigation views missing or drifted")
    for view in views:
        if view.get("view_authority") != DEFAULT_AUTHORITY_STATUS:
            flags["AUTHORITY_PROMOTION"] = True
            _fail("C9", f"{view.get('view_id')} view authority promoted")
        if view.get("view_role") != "NAVIGATION_OR_ANALYSIS_ONLY":
            _fail("NAVIGATION_VIEW_RETENTION", f"{view.get('view_id')} not navigation-only")
        if view.get("parentage_adjudicated") is not False:
            flags["VIEW_PARENTS_TO_PARENTAGE"] = True
            _fail("SW-R-009", f"{view.get('view_id')} parents promoted to parentage")
        if view.get("sw_r_009_status") != "OPEN":
            flags["VIEW_PARENTS_TO_PARENTAGE"] = True
            _fail("SW-R-009", f"{view.get('view_id')} SW-R-009 closed")
        original = view.get("original_view")
        if not isinstance(original, dict):
            _fail("NAVIGATION_VIEW_RETENTION", f"{view.get('view_id')} original_view missing")
        if "parents" in original and view.get("parents_field_status") != (
            "DOCUMENTARY_UNADJUDICATED"
        ):
            flags["VIEW_PARENTS_TO_PARENTAGE"] = True
            _fail("SW-R-009", f"{view.get('view_id')} parents field status mutated")

    return flags
