"""Stage C — Overlay Registry. Kind-partitioned; t5_multilabel overlay_kind stays ABSENT."""

from __future__ import annotations

from typing import Any

from scripts.ops.forensic_structure_schema_v1.constants import (
    EXPECTED_LOSSLESSNESS,
    OVERLAY_CLASS_ORDER,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.id_spaces import (
    assert_token_layer1_disjoint,
    classify_overlay_id,
)
from scripts.ops.forensic_structure_schema_v1.models import OptionalValue, OverlayRecord
from scripts.ops.forensic_structure_schema_v1.state import PipelineState

_LAYER1_REF_FIELDS = (
    "occurrence_id",
    "heading_occurrence_id",
    "open_occurrence_id",
    "close_occurrence_id",
    "begin_occurrence_id",
    "end_occurrence_id",
)

_OVERLAY_REF_FIELDS = (
    "json_fence_overlay_id",
    "wrapper_pair_overlay_id",
)


def _copy_payload(record: dict[str, Any]) -> dict[str, Any]:
    return dict(record)


def run_stage_c(state: PipelineState) -> None:
    overlays_raw = state.sidecar["layer1c_overlays"]
    observed_classes = tuple(overlays_raw.keys())
    if observed_classes != OVERLAY_CLASS_ORDER:
        raise TransformationContractViolation(
            "STAGE_C",
            f"overlay class order drift: {observed_classes}",
        )

    overlays_by_class: dict[str, list[OverlayRecord]] = {}
    overlay_by_id: dict[str, OverlayRecord] = {}
    alias_to_overlay_id: dict[str, str] = {}
    token_occurrence_ids: set[str] = set()
    body_sha_to_ids: dict[str, list[str]] = {}

    for class_name in OVERLAY_CLASS_ORDER:
        records = overlays_raw[class_name]
        if not isinstance(records, list):
            raise TransformationContractViolation(
                "STAGE_C",
                f"{class_name} must be an array",
            )
        class_list: list[OverlayRecord] = []
        for index, raw in enumerate(records):
            if not isinstance(raw, dict):
                raise TransformationContractViolation(
                    "STAGE_C",
                    f"{class_name}[{index}] is not an object",
                )
            overlay_id = str(raw["overlay_id"])
            if overlay_id in overlay_by_id:
                raise TransformationContractViolation(
                    "C2",
                    f"duplicate overlay_id {overlay_id}",
                )
            kind = OptionalValue.from_mapping(raw, "overlay_kind")
            if class_name == "t5_multilabel" and kind.presence != "absent":
                raise TransformationContractViolation(
                    "SW-R-007",
                    "t5_multilabel overlay_kind must remain ABSENT",
                )
            rec = OverlayRecord(
                overlay_id=overlay_id,
                overlay_kind=kind,
                overlay_class=class_name,
                payload=_copy_payload(raw),
                sidecar_index=index,
                byte_start=OptionalValue.from_mapping(raw, "byte_start"),
                byte_end=OptionalValue.from_mapping(raw, "byte_end"),
            )
            classify_overlay_id(overlay_id)
            overlay_by_id[overlay_id] = rec
            class_list.append(rec)
            alias = raw.get("source_identifier_alias")
            if isinstance(alias, str) and alias:
                if alias in alias_to_overlay_id:
                    raise TransformationContractViolation(
                        "STAGE_C",
                        f"duplicate alias {alias} for overlays "
                        f"{alias_to_overlay_id[alias]} and {overlay_id}",
                    )
                alias_to_overlay_id[alias] = overlay_id
            if class_name == "token_occurrence":
                token_occ = str(raw["occurrence_id"])
                if token_occ in token_occurrence_ids:
                    raise TransformationContractViolation(
                        "C2",
                        f"duplicate token occurrence_id {token_occ}",
                    )
                token_occurrence_ids.add(token_occ)
                if raw.get("normalized") is True:
                    raise TransformationContractViolation(
                        "C8",
                        f"token {overlay_id} has normalized=true",
                    )
            if class_name == "fence_block":
                body_sha = str(raw["body_sha256"])
                body_sha_to_ids.setdefault(body_sha, []).append(overlay_id)
            if class_name == "t5_multilabel" and raw.get("collapsed") is True:
                raise TransformationContractViolation(
                    "C4",
                    f"{overlay_id} collapsed=true",
                )
        overlays_by_class[class_name] = class_list

    epochs_raw = state.sidecar["layer1b_append_epochs"]
    epoch_list: list[OverlayRecord] = []
    for index, raw in enumerate(epochs_raw):
        overlay_id = str(raw["overlay_id"])
        if overlay_id in overlay_by_id:
            raise TransformationContractViolation("C2", f"duplicate epoch overlay {overlay_id}")
        rec = OverlayRecord(
            overlay_id=overlay_id,
            overlay_kind=OptionalValue.from_mapping(raw, "overlay_kind"),
            overlay_class="append_epoch",
            payload=_copy_payload(raw),
            sidecar_index=index,
            byte_start=OptionalValue.from_mapping(raw, "byte_start"),
            byte_end=OptionalValue.from_mapping(raw, "byte_end"),
        )
        overlay_by_id[overlay_id] = rec
        epoch_list.append(rec)
        if raw.get("authority_derived") is True:
            raise TransformationContractViolation("C9", f"{overlay_id} authority_derived=true")
        if raw.get("world_time_derived") is True:
            raise TransformationContractViolation("D2", f"{overlay_id} world_time_derived=true")
    overlays_by_class["append_epoch"] = epoch_list

    layer1_ids = set(state.layer1_by_id)
    assert_token_layer1_disjoint(token_occurrence_ids, layer1_ids)

    for rec in overlay_by_id.values():
        payload = rec.payload
        for field_name in _LAYER1_REF_FIELDS:
            if field_name not in payload:
                continue
            value = payload[field_name]
            if value is None:
                continue
            occ = str(value)
            if rec.overlay_class == "token_occurrence" and field_name == "occurrence_id":
                if occ in layer1_ids:
                    raise TransformationContractViolation(
                        "SW-R-008",
                        f"token {rec.overlay_id} occurrence_id equality-joins layer1",
                    )
                continue
            if occ not in layer1_ids:
                raise TransformationContractViolation(
                    "LAYER1_OCCURRENCE_REFERENCE",
                    f"{rec.overlay_id}.{field_name}={occ} not in LAYER1",
                )
        for field_name in _OVERLAY_REF_FIELDS:
            if field_name not in payload:
                continue
            value = payload[field_name]
            if value is None:
                continue
            oid = str(value)
            if oid not in overlay_by_id:
                raise TransformationContractViolation(
                    "OVERLAY_REFERENCE",
                    f"{rec.overlay_id}.{field_name}={oid} unknown overlay",
                )
        if rec.overlay_class == "t5_cls_row":
            aliases = rec.payload.get("cls_aliases")
            if aliases is not None:
                raise TransformationContractViolation(
                    "STAGE_C",
                    "t5_cls_row must not carry cls_aliases",
                )
        if rec.overlay_class == "t5_multilabel":
            aliases = rec.payload.get("cls_aliases") or []
            if len(aliases) != int(rec.payload["row_count"]):
                raise TransformationContractViolation(
                    "C4",
                    f"{rec.overlay_id} row_count != len(cls_aliases)",
                )
            for alias in aliases:
                mapped = alias_to_overlay_id.get(str(alias))
                if mapped is None:
                    raise TransformationContractViolation(
                        "EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY",
                        f"{rec.overlay_id} unknown cls alias {alias}",
                    )

    expected = EXPECTED_LOSSLESSNESS
    _require_count(overlays_by_class, "fence_block", expected["FENCE_BLOCK_COUNT"])
    _require_count(overlays_by_class, "h1_span", expected["H1_SPAN_COUNT"])
    _require_count(overlays_by_class, "t3_src_span", expected["T3_SRC_SPAN_COUNT"])
    _require_count(overlays_by_class, "wrapper_mention", expected["WRAPPER_MENTION_COUNT"])
    _require_count(overlays_by_class, "wrapper_pair", expected["WRAPPER_PAIR_COUNT"])
    _require_count(overlays_by_class, "t5_multilabel", expected["T5_MULTILABEL_COUNT"])
    _require_count(overlays_by_class, "token_occurrence", expected["TOKEN_OCCURRENCE_COUNT"])
    _require_count(overlays_by_class, "t4_rel_row", expected["T4_REL_ROW_COUNT"])
    _require_count(overlays_by_class, "t5_cls_row", expected["T5_CLS_ROW_COUNT"])
    _require_count(overlays_by_class, "kv_packet", expected["KV_PACKET_COUNT"])
    _require_count(overlays_by_class, "forensic_record", expected["FORENSIC_RECORD_COUNT"])
    _require_count(overlays_by_class, "append_epoch", expected["APPEND_EPOCH_COUNT"])

    unique_body = len(body_sha_to_ids)
    if unique_body != expected["FENCE_UNIQUE_BODY_HASHES"]:
        raise TransformationContractViolation(
            "C3",
            f"unique fence body hashes {unique_body} != {expected['FENCE_UNIQUE_BODY_HASHES']}",
        )
    dup_groups = sum(1 for ids in body_sha_to_ids.values() if len(ids) > 1)
    if dup_groups != expected["FENCE_DUPLICATE_GROUPS"]:
        raise TransformationContractViolation(
            "C3",
            f"duplicate fence groups {dup_groups} != {expected['FENCE_DUPLICATE_GROUPS']}",
        )

    state.overlays_by_class = overlays_by_class
    state.overlay_by_id = overlay_by_id
    state.alias_to_overlay_id = alias_to_overlay_id
    state.token_occurrence_ids = token_occurrence_ids
    state.body_sha_to_overlay_ids = body_sha_to_ids
    state.stages_completed.append("C_OVERLAY_REGISTRY")


def _require_count(
    overlays_by_class: dict[str, list[OverlayRecord]], name: str, expected: int
) -> None:
    observed = len(overlays_by_class[name])
    if observed != expected:
        raise TransformationContractViolation(
            "STAGE_C",
            f"{name} count {observed} != {expected}",
        )
