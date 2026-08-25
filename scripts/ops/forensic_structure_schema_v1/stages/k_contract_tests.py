"""Stage K — Contract-Test Evaluation against exact sidecar fixture IDs."""

from __future__ import annotations

from scripts.ops.forensic_structure_schema_v1.constants import (
    DUAL_CLASS_OCCURRENCE_ID,
    DUPLICATE_FENCE_BODY_SHA256,
    EXPECTED_SOURCE_SHA256,
    FIXTURE_IDS,
    HISTORICAL_FORENSIC_RECORD_SHA,
)
from scripts.ops.forensic_structure_schema_v1.exceptions import (
    TransformationContractViolation,
)
from scripts.ops.forensic_structure_schema_v1.models import ContractTestResult
from scripts.ops.forensic_structure_schema_v1.state import PipelineState


def _pass(test_id: str, detail: str) -> ContractTestResult:
    return ContractTestResult(test_id=test_id, status="PASS", detail=detail)


def _fail(test_id: str, detail: str) -> None:
    raise TransformationContractViolation(test_id, detail)


def _overlay(state: PipelineState, overlay_id: str):
    if overlay_id not in state.overlay_by_id:
        raise TransformationContractViolation(
            "STAGE_K",
            f"fixture overlay missing: {overlay_id}",
        )
    return state.overlay_by_id[overlay_id]


def _rel(state: PipelineState, relation_id: str):
    if relation_id not in state.relation_by_id:
        raise TransformationContractViolation(
            "STAGE_K",
            f"fixture relation missing: {relation_id}",
        )
    return state.relation_by_id[relation_id]


def _eval_tv001(state: PipelineState) -> ContractTestResult:
    overlay = _overlay(state, FIXTURE_IDS["TV_001_T4_OVERLAY"])
    payload = overlay.payload
    if payload.get("source_identifier_alias") != FIXTURE_IDS["TV_001_T4_ALIAS"]:
        _fail("TV-001", "REL-000001 alias mismatch")
    if payload.get("declared_relation_type") != "ORDERED_BEFORE":
        _fail("TV-001", "declared_relation_type mutated")
    if payload.get("is_dependency") is not False:
        _fail("TV-001", "t4 is_dependency is not false")
    if payload.get("layer3_mapped_type") != "STRUCTURAL_ORDERED_BEFORE":
        _fail("TV-001", "layer3_mapped_type mismatch")
    rel = _rel(state, FIXTURE_IDS["TV_001_LAYER3"])
    if rel.is_dependency is not False:
        _fail("TV-001", "layer3 is_dependency promoted")
    if rel.relation_type != "STRUCTURAL_ORDERED_BEFORE":
        _fail("TV-001", "relation_type mutated")
    if rel.from_binding.kind != "EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY":
        _fail("TV-001", f"from_binding kind {rel.from_binding.kind}")
    if rel.to_binding.kind != "EXPLICIT_ALIAS_MAP_NAVIGATION_ONLY":
        _fail("TV-001", f"to_binding kind {rel.to_binding.kind}")
    if rel.gate_membership != "UNKNOWN":
        _fail("TV-001", "gate membership inferred")
    rel_note = rel.explicit_source_note
    if rel_note.presence == "present":
        if "NOT a dependency" not in str(rel_note.value):
            _fail("TV-001", "explicit_source_note dropped")
    env = state.envelope_by_overlay_id[overlay.overlay_id][0]
    if env.is_dependency.presence == "present" and env.is_dependency.value is True:
        _fail("TV-001", "envelope is_dependency true")
    return _pass("TV-001", "ORDERED_BEFORE remains non-dependency")


def _eval_tv002(state: PipelineState) -> ContractTestResult:
    ids = (
        FIXTURE_IDS["TV_002_Z2AR_VS_Z2AP"],
        FIXTURE_IDS["TV_002_Z2AR_VS_22"],
        FIXTURE_IDS["TV_002_Z2AP_VS_22"],
    )
    for relation_id in ids:
        rel = _rel(state, relation_id)
        if rel.unresolved.presence != "present" or rel.unresolved.value is not True:
            _fail("TV-002", f"{relation_id} unresolved is not true")
        if rel.winner_selected is not False:
            _fail("TV-002", f"{relation_id} winner_selected")
        if rel.pointer_adjudication_performed.presence == "present":
            if rel.pointer_adjudication_performed.value is not False:
                _fail("TV-002", f"{relation_id} pointer adjudicated")
        if rel.repo_z2cf_imported_as_resolution.presence == "present":
            if rel.repo_z2cf_imported_as_resolution.value is not False:
                _fail("TV-002", f"{relation_id} z2cf imported")
        if rel.from_binding.kind != "DOCUMENTARY_STRING_ENDPOINT":
            _fail("TV-002", f"{relation_id} from_id occurrence-bound")
        if rel.to_binding.kind != "DOCUMENTARY_STRING_ENDPOINT":
            _fail("TV-002", f"{relation_id} to_id occurrence-bound")
    z2cf = 0
    for rec in state.overlays_by_class["token_occurrence"]:
        if rec.payload.get("token_class") == "POINTER_TOKEN":
            if rec.payload.get("imported_as_target_resolution") is True:
                z2cf += 1
        verbatim = rec.payload.get("token_verbatim")
        if (
            isinstance(verbatim, str)
            and "Z2CF" in verbatim
            and rec.payload.get("token_class") == "POINTER_TOKEN"
        ):
            z2cf += 1
    pointer_tokens = [
        r
        for r in state.overlays_by_class["token_occurrence"]
        if r.payload.get("token_class") == "POINTER_TOKEN"
    ]
    if any(r.payload.get("imported_as_target_resolution") is True for r in pointer_tokens):
        _fail("TV-002", "POINTER_TOKEN imported as resolution")
    return _pass("TV-002", "three pointer conflicts remain unresolved")


def _eval_tv003(state: PipelineState) -> ContractTestResult:
    distinct = _overlay(state, FIXTURE_IDS["TV_003_DISTINCT"])
    if distinct.payload.get("collapsed") is not False:
        _fail("TV-003", "distinct group collapsed")
    labels = distinct.payload["labels_in_source_order"]
    aliases = distinct.payload["cls_aliases"]
    if labels != [
        "CANONICAL_AUTHORITY_REFERENCE",
        "HISTORICAL_INTERMEDIATE_STATE",
        "OPEN_OR_CONFLICTED",
    ]:
        _fail("TV-003", "distinct labels mutated")
    if list(aliases) != ["CLS-000038", "CLS-000039", "CLS-000040"]:
        _fail("TV-003", "distinct cls_aliases mutated")
    dup = _overlay(state, FIXTURE_IDS["TV_003_DUP_LABELS"])
    if int(dup.payload["row_count"]) != 3:
        _fail("TV-003", "duplicate-label group row_count mutated")
    if len(dup.payload["cls_aliases"]) != 3:
        _fail("TV-003", "duplicate-label cls_aliases dropped")
    if len(dup.payload["labels_in_source_order"]) != 2:
        _fail("TV-003", "labels_in_source_order is not the unique derived list")
    env = state.envelope_by_overlay_id[distinct.overlay_id][0]
    if env.primary_label != "NONE":
        _fail("TV-003", "primary_label invented")
    if env.authority_status != "NONE":
        _fail("TV-003", "CANONICAL_AUTHORITY_REFERENCE promoted authority")
    return _pass("TV-003", "multilabel rows preserved without primary")


def _eval_tv004(state: PipelineState) -> ContractTestResult:
    a = _overlay(state, FIXTURE_IDS["TV_004_FENCE_A"])
    b = _overlay(state, FIXTURE_IDS["TV_004_FENCE_B"])
    if a.payload["body_sha256"] != DUPLICATE_FENCE_BODY_SHA256:
        _fail("TV-004", "fence A body hash mismatch")
    if b.payload["body_sha256"] != DUPLICATE_FENCE_BODY_SHA256:
        _fail("TV-004", "fence B body hash mismatch")
    if a.overlay_id == b.overlay_id:
        _fail("TV-004", "duplicate fences collapsed")
    ids = state.body_sha_to_overlay_ids[DUPLICATE_FENCE_BODY_SHA256]
    if FIXTURE_IDS["TV_004_FENCE_A"] not in ids or FIXTURE_IDS["TV_004_FENCE_B"] not in ids:
        _fail("TV-004", "duplicate group index dropped an overlay")
    view = next(
        v
        for v in state.sidecar["layer4_derived_views"]
        if v["view_id"] == "view_duplicate_fence_bodies"
    )
    if view.get("deduplicated") is not False:
        _fail("TV-004", "view_duplicate_fence_bodies.deduplicated is not false")
    return _pass("TV-004", "duplicate fence bodies preserved as two overlays")


def _eval_tv005(state: PipelineState) -> ContractTestResult:
    overlay_id = state.alias_to_overlay_id[FIXTURE_IDS["TV_005_CLS_ALIAS"]]
    rec = _overlay(state, overlay_id)
    if rec.payload.get("classified_source_line") is not None:
        _fail("TV-005", "classified_source_line expanded from null")
    env = state.envelope_by_overlay_id[overlay_id][0]
    if env.classified_source_line.presence != "null":
        _fail("TV-005", "classified_source_line presence is not null")
    cell = state.source_bytes[int(rec.payload["byte_start"]) : int(rec.payload["byte_end"])]
    if b"320-346" not in cell:
        _fail("TV-005", "raw TSV range token 320-346 missing")
    return _pass("TV-005", "T5 range remains opaque null")


def _eval_tv006(state: PipelineState) -> ContractTestResult:
    sha64 = _overlay(state, FIXTURE_IDS["TV_006_SHA64"])
    if sha64.payload.get("token_class") != "SHA_HEX_64":
        _fail("TV-006", "SHA_HEX_64 class mutated")
    if sha64.payload.get("hash_kind") != "UNKNOWN":
        _fail("TV-006", "hash_kind promoted from length")
    sha40 = _overlay(state, FIXTURE_IDS["TV_006_SHA40"])
    if sha40.payload.get("token_class") != "SHA_HEX_40":
        _fail("TV-006", "SHA_HEX_40 class mutated")
    if sha40.payload.get("hash_kind") != "UNKNOWN":
        _fail("TV-006", "40-hex promoted to Git SHA1")
    env = state.envelope_by_overlay_id[sha64.overlay_id][0]
    if env.hash_kind.value != "UNKNOWN":
        _fail("TV-006", "envelope hash_kind not UNKNOWN")
    if env.token_occurrence_id.presence != "present":
        _fail("TV-006", "token occurrence_id dropped")
    if env.layer1_occurrence_id.value == env.token_occurrence_id.value:
        _fail("TV-006", "token id copied into layer1 id")
    return _pass("TV-006", "hash_kind remains UNKNOWN")


def _eval_tv007(state: PipelineState) -> ContractTestResult:
    rec = _overlay(state, FIXTURE_IDS["TV_007_H1"])
    if rec.payload.get("h1_sequence") != 1:
        _fail("TV-007", "h1_sequence mutated")
    env = state.envelope_by_overlay_id[rec.overlay_id][0]
    if env.semantic_container != "NOT_ADJUDICATED":
        _fail("TV-007", "H1 treated as semantic container")
    if env.currentness_status != "CURRENTNESS_UNKNOWN":
        _fail("TV-007", "H1 currentness promoted")
    if int(rec.payload["byte_start"]) != 0 or int(rec.payload["byte_end"]) != 746:
        _fail("TV-007", "H1-1 byte range mutated")
    return _pass("TV-007", "H1 remains mechanical navigation partition")


def _eval_tv008(state: PipelineState) -> ContractTestResult:
    rec = _overlay(state, FIXTURE_IDS["TV_008_CURRENT"])
    if rec.payload.get("token_class") != "CURRENT_STAR_ASSIGNMENT":
        _fail("TV-008", "token_class mutated")
    if rec.payload.get("currentness_upgrade") is not False:
        _fail("TV-008", "currentness_upgrade is not false")
    if rec.payload.get("temporal_status") != "currentness_unknown":
        _fail("TV-008", "temporal_status promoted")
    env = state.envelope_by_overlay_id[rec.overlay_id][0]
    if env.currentness_status != "CURRENTNESS_UNKNOWN":
        _fail("TV-008", "envelope currentness promoted")
    return _pass("TV-008", "CURRENT_* remains CURRENTNESS_UNKNOWN")


def _eval_tv009(state: PipelineState) -> ContractTestResult:
    rel = _rel(state, FIXTURE_IDS["TV_009_DEP"])
    if rel.relation_type != "EXPLICIT_DEPENDENCY":
        _fail("TV-009", "relation_type mutated")
    if rel.is_dependency is not True:
        _fail("TV-009", "is_dependency not copied")
    if rel.gate_membership != "UNKNOWN":
        _fail("TV-009", "gate membership inferred")
    if rel.from_binding.kind != "DOCUMENTARY_STRING_ENDPOINT":
        _fail("TV-009", "from_id occurrence-bound by name")
    if rel.to_binding.kind != "DOCUMENTARY_STRING_ENDPOINT":
        _fail("TV-009", "to_id occurrence-bound by name")
    if rel.not_invented_gate_edge.presence == "present":
        if rel.not_invented_gate_edge.value is not True:
            _fail("TV-009", "not_invented_gate_edge mutated")
    return _pass("TV-009", "explicit dependency endpoints remain unbound")


def _eval_tv010(state: PipelineState) -> ContractTestResult:
    rec = _overlay(state, FIXTURE_IDS["TV_010_RECORD"])
    if rec.payload.get("binds_blob_sha256") != HISTORICAL_FORENSIC_RECORD_SHA:
        _fail("TV-010", "historical SHA mutated")
    if rec.payload.get("binds_blob_sha256_matches_current") is not False:
        _fail("TV-010", "matches_current promoted")
    if rec.payload.get("binds_blob_sha256") == EXPECTED_SOURCE_SHA256:
        _fail("TV-010", "historical SHA replaced with current source SHA")
    sibling = _overlay(state, FIXTURE_IDS["TV_010_NULL_SHA_RECORD"])
    if sibling.payload.get("binds_blob_sha256") is not None:
        _fail("TV-010", "null sibling SHA filled")
    env = state.envelope_by_overlay_id[sibling.overlay_id][0]
    if env.binds_blob_sha256.presence != "null":
        _fail("TV-010", "null SHA not serialized as null presence")
    return _pass("TV-010", "embedded prior report keeps historical SHA")


def _eval_tv011(state: PipelineState) -> ContractTestResult:
    rec = _overlay(state, FIXTURE_IDS["TV_011_MENTION"])
    if rec.payload.get("instance_vs_mention") != "mention":
        _fail("TV-011", "mention flag mutated")
    mentions = state.overlays_by_class["wrapper_mention"]
    pairs = state.overlays_by_class["wrapper_pair"]
    if len(mentions) != 9 or len(pairs) != 23:
        _fail("TV-011", "mention/instance counts mutated")
    mention_ids = {r.overlay_id for r in mentions}
    pair_ids = {r.overlay_id for r in pairs}
    if mention_ids.intersection(pair_ids):
        _fail("TV-011", "mention collapsed into wrapper_pair id space")
    wrap_contains = [r for r in state.relations if r.relation_type == "WRAPPER_CONTAINS"]
    if len(wrap_contains) != 23:
        _fail("TV-011", "WRAPPER_CONTAINS count mutated")
    if any(r.from_binding.value in mention_ids for r in wrap_contains):
        _fail("TV-011", "WRAPPER_CONTAINS projected from mention")
    return _pass("TV-011", "wrapper mention remains distinct from instance")


def _eval_tv012(state: PipelineState) -> ContractTestResult:
    rec = _overlay(state, FIXTURE_IDS["TV_012_TICK5"])
    if int(rec.payload["tick_len"]) != 5:
        _fail("TV-012", "tick_len mutated")
    if rec.payload.get("inner_shorter_fence_like") is not True:
        _fail("TV-012", "inner_shorter_fence_like mutated")
    if int(rec.payload["nest_depth"]) != 1:
        _fail("TV-012", "nest_depth invented")
    original = {r.overlay_id for r in state.overlays_by_class["fence_block"]}
    projected = {
        e.sidecar_overlay_id.value for e in state.envelopes if e.overlay_class == "fence_block"
    }
    extra = projected - original
    if extra:
        _fail("TV-012", f"synthetic inner fence overlays: {sorted(extra)[:5]}")
    if len(original) != 1368:
        _fail("TV-012", "fence_block count mutated")
    return _pass("TV-012", "no synthetic inner tick5 fence_block")


def _eval_sw_r_013(state: PipelineState) -> ContractTestResult:
    groups = []
    for rec in state.overlays_by_class["t5_multilabel"]:
        row_count = int(rec.payload["row_count"])
        labels = rec.payload["labels_in_source_order"]
        if row_count > len(labels):
            groups.append(rec.overlay_id)
    if len(groups) != 36:
        _fail("SW-R-013", f"duplicate-label groups {len(groups)} != 36")
    example = _overlay(state, FIXTURE_IDS["TV_003_DUP_LABELS"])
    if len(example.payload["cls_aliases"]) != 3:
        _fail("SW-R-013", "example group lost cls_aliases")
    return _pass("SW-R-013", "duplicate multilabel labels remain uncollapsed; residual OPEN")


def _eval_sw_r_014(state: PipelineState) -> ContractTestResult:
    rec = _overlay(state, FIXTURE_IDS["TV_010_NULL_SHA_RECORD"])
    env = state.envelope_by_overlay_id[rec.overlay_id][0]
    if env.binds_blob_sha256.presence != "null":
        _fail("SW-R-014", "null SHA not preserved")
    if env.binds_blob_sha256.value is not None:
        _fail("SW-R-014", "null SHA filled")
    return _pass("SW-R-014", "null forensic_record SHA preserved; residual OPEN")


def _eval_sw_r_015(state: PipelineState) -> ContractTestResult:
    outside = 0
    for rec in state.overlays_by_class["t3_src_span"]:
        heading = int(rec.payload["heading_line"])
        start = int(rec.payload["source_start_line"])
        end = int(rec.payload["source_end_line"])
        if start <= heading <= end:
            _fail("SW-R-015", f"{rec.overlay_id} heading fused into region")
        outside += 1
        env = state.envelope_by_overlay_id[rec.overlay_id][0]
        if env.semantic_container != "NOT_ADJUDICATED":
            _fail("SW-R-015", "t3 treated as container")
    if outside != 88:
        _fail("SW-R-015", f"heading-outside count {outside} != 88")
    return _pass("SW-R-015", "T3 heading and region remain two loci; residual OPEN")


def run_stage_k(state: PipelineState) -> None:
    results = {
        "TV-001": _eval_tv001(state),
        "TV-002": _eval_tv002(state),
        "TV-003": _eval_tv003(state),
        "TV-004": _eval_tv004(state),
        "TV-005": _eval_tv005(state),
        "TV-006": _eval_tv006(state),
        "TV-007": _eval_tv007(state),
        "TV-008": _eval_tv008(state),
        "TV-009": _eval_tv009(state),
        "TV-010": _eval_tv010(state),
        "TV-011": _eval_tv011(state),
        "TV-012": _eval_tv012(state),
        "SW-R-013": _eval_sw_r_013(state),
        "SW-R-014": _eval_sw_r_014(state),
        "SW-R-015": _eval_sw_r_015(state),
    }
    dual = state.layer2_envelopes_by_occurrence.get(DUAL_CLASS_OCCURRENCE_ID, [])
    if len(dual) != 2:
        _fail("SW-R-011", "dual-class H1 envelopes collapsed")
    open_residuals = [r.residual_id for r in state.residuals if r.status == "OPEN"]
    if len(open_residuals) != len(state.residuals):
        _fail("STAGE_K", "a residual was auto-closed")
    state.contract_tests = results
    state.stages_completed.append("K_CONTRACT_TEST_EVALUATION")
