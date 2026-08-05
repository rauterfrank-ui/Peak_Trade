"""Fail-closed validator for regime-coverage + dashboard input-gap closeout v1."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping, Sequence

from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_and_dashboard_input_gap_closeout_v1 import (
    constants_v1 as C,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_and_dashboard_input_gap_closeout_v1.executor_v1 import (
    RegimeCoverageDashboardInputGapCloseoutErrorV1,
    execute_regime_coverage_against_canonical_pack_v1,
)


def _require_mapping(raw: Any, *, label: str) -> Mapping[str, Any]:
    if not isinstance(raw, Mapping):
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1(f"MAPPING_REQUIRED:{label}")
    return raw


def _assert_exact(value: Any, expected: Any, *, label: str) -> None:
    if value != expected:
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1(f"VALUE_MISMATCH:{label}")


def _assert_false(value: Any, *, label: str) -> None:
    if value is True:
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1(f"MUST_REMAIN_FALSE:{label}")
    if value not in (False, None) and bool(value):
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1(f"MUST_REMAIN_FALSE:{label}")


def _assert_true(value: Any, *, label: str) -> None:
    if value is not True:
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1(f"MUST_BE_TRUE:{label}")


def _assert_null(value: Any, *, label: str) -> None:
    if value is not None:
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1(f"MUST_REMAIN_NULL:{label}")


def _load_json_mapping(path: Path, *, label: str) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(_require_mapping(payload, label=label))


def load_canonical_regime_coverage_dashboard_input_gap_closeout_manifest_v1(
    repo_root: Path,
) -> dict[str, Any]:
    path = Path(repo_root).resolve() / C.DECISIONS_MANIFEST_REL
    return _load_json_mapping(path, label="execution_manifest")


def _validate_sealed_artifacts(root: Path, live: Mapping[str, Any]) -> None:
    counts_art = _load_json_mapping(root / C.COUNTS_ARTIFACT_REL, label="counts_artifact")
    _assert_exact(
        counts_art.get("regime_coverage_counts"),
        dict(C.REGIME_COVERAGE_COUNTS),
        label="counts_artifact.regime_coverage_counts",
    )
    _assert_exact(
        counts_art.get("producer_digest"),
        C.PRODUCER_DIGEST,
        label="counts_artifact.producer_digest",
    )
    _assert_exact(
        counts_art.get("observation_pack_digest"),
        C.OBSERVATION_PACK_DIGEST,
        label="counts_artifact.observation_pack_digest",
    )

    instance_art = _load_json_mapping(root / C.INSTANCE_ARTIFACT_REL, label="instance_artifact")
    _assert_exact(
        instance_art,
        live["regime_coverage_instance"],
        label="instance_artifact",
    )

    proof = _load_json_mapping(root / C.EXECUTION_PROOF_REL, label="execution_proof")
    _assert_exact(proof.get("next_step_id"), C.NEXT_STEP_ID, label="proof.next_step_id")
    _assert_exact(
        proof.get("observation_pack_digest"),
        C.OBSERVATION_PACK_DIGEST,
        label="proof.observation_pack_digest",
    )
    _assert_exact(proof.get("producer_digest"), C.PRODUCER_DIGEST, label="proof.producer_digest")
    _assert_exact(
        proof.get("regime_coverage_counts"),
        dict(C.REGIME_COVERAGE_COUNTS),
        label="proof.regime_coverage_counts",
    )
    _assert_exact(
        proof.get("regime_coverage_instance"),
        live["regime_coverage_instance"],
        label="proof.regime_coverage_instance",
    )
    _assert_true(proof.get("canonical_binding_ok"), label="proof.canonical_binding_ok")
    for key in (
        "campaign_start",
        "input_authority_flip",
        "runtime_implemented_flip",
        "dashboard_logic_change",
        "trading_logic_change",
        "orders_testnet_live",
        "regime_coverage_producer_available",
        "productive_emission",
    ):
        _assert_false(proof.get(key), label=f"proof.{key}")
    _assert_exact(
        proof.get("dashboard_authority_effect"),
        "NONE",
        label="proof.dashboard_authority_effect",
    )
    _assert_null(proof.get("campaign_id"), label="proof.campaign_id")

    delta = _load_json_mapping(root / C.DELTA_REPORT_REL, label="delta_report")
    _assert_exact(
        delta.get("document_type"),
        "MISSING_SOURCE_DELTA_REPORT",
        label="delta.document_type",
    )
    _assert_false(delta.get("dashboard_logic_change"), label="delta.dashboard_logic_change")
    _assert_exact(
        delta.get("dashboard_authority_effect"),
        "NONE",
        label="delta.dashboard_authority_effect",
    )
    _assert_exact(delta.get("before"), C.INVENTORY_BEFORE_AFTER, label="delta.before")
    _assert_exact(delta.get("after"), C.INVENTORY_BEFORE_AFTER, label="delta.after")
    delta_obj = _require_mapping(delta.get("delta"), label="delta.delta")
    _assert_exact(delta_obj.get("TOTAL_MISSING_SOURCE_COUNT_DELTA"), 0, label="delta.ms")
    _assert_exact(delta_obj.get("TOTAL_NOT_BOUND_COUNT_DELTA"), 0, label="delta.nb")
    _assert_exact(
        delta_obj.get("regime_bull_bear_switch_affected_presentation_element_count_delta"),
        0,
        label="delta.regime_family",
    )

    topic = _load_json_mapping(root / C.TOPIC_CLOSEOUT_REL, label="topic_closeout")
    _assert_exact(topic.get("document_type"), "TOPIC_CLOSEOUT_VERDICT", label="topic.document_type")
    _assert_exact(
        topic.get("overall_topic_closeout_verdict"),
        C.OVERALL_TOPIC_CLOSEOUT_VERDICT,
        label="topic.overall",
    )
    topics = topic.get("topics")
    if not isinstance(topics, Sequence) or isinstance(topics, (str, bytes)):
        raise RegimeCoverageDashboardInputGapCloseoutErrorV1("TOPICS_MUST_BE_SEQUENCE")
    by_id = {
        str(_require_mapping(row, label="topic_row").get("topic_id")): _require_mapping(
            row, label="topic_row"
        )
        for row in topics
    }
    _assert_exact(
        by_id["SURFACE_B_REGIME_COVERAGE_PACK_INPUT_GAP"].get("verdict"),
        "CLOSED",
        label="topic.pack_gap",
    )
    _assert_exact(
        by_id["DASHBOARD_REGIME_BULL_BEAR_SWITCH_MISSING_SOURCE"].get("verdict"),
        "REMAINS_BLOCKED_OUT_OF_SCOPE",
        label="topic.dashboard_gap",
    )
    for key in ("campaign_start", "input_authority_flip", "runtime_implemented_flip"):
        _assert_false(topic.get(key), label=f"topic.{key}")

    producer_txt = (root / C.PRODUCER_DIGEST_TXT_REL).read_text(encoding="utf-8").strip()
    pack_txt = (root / C.OBSERVATION_PACK_DIGEST_TXT_REL).read_text(encoding="utf-8").strip()
    _assert_exact(producer_txt, C.PRODUCER_DIGEST, label="producer_digest.txt")
    _assert_exact(pack_txt, C.OBSERVATION_PACK_DIGEST, label="observation_pack_digest.txt")


def validate_regime_coverage_dashboard_input_gap_closeout_manifest_v1(
    manifest: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    _assert_exact(manifest.get("schema_version"), C.SCHEMA_VERSION, label="schema_version")
    _assert_exact(manifest.get("document_type"), C.DOCUMENT_TYPE, label="document_type")
    _assert_exact(manifest.get("capability_scope"), C.CAPABILITY_SCOPE, label="capability_scope")
    _assert_exact(manifest.get("status"), C.STATUS, label="status")
    _assert_exact(manifest.get("next_step_id"), C.NEXT_STEP_ID, label="next_step_id")
    _assert_exact(manifest.get("owner_go_base_sha"), C.OWNER_GO_BASE_SHA, label="owner_go_base_sha")
    _assert_exact(
        manifest.get("observation_pack_digest"),
        C.OBSERVATION_PACK_DIGEST,
        label="observation_pack_digest",
    )
    _assert_true(manifest.get("use_canonical_merged_pack"), label="use_canonical_merged_pack")
    _assert_true(
        manifest.get("execute_regime_coverage_producer"),
        label="execute_regime_coverage_producer",
    )
    for key in (
        "require_regime_coverage_counts",
        "require_regime_coverage_instance",
        "require_canonical_binding",
        "require_missing_source_delta_report",
        "require_topic_closeout_verdict",
        "fail_closed",
    ):
        _assert_true(manifest.get(key), label=key)
    _assert_false(manifest.get("campaign_id_required"), label="campaign_id_required")
    for key in (
        "campaign_start",
        "input_authority_flip",
        "runtime_implemented_flip",
        "dashboard_logic_change",
        "trading_logic_change",
        "orders_testnet_live",
        "input_authority",
        "runtime_implemented",
        "regime_coverage_producer_available",
        "productive_emission",
    ):
        _assert_false(manifest.get(key), label=key)
    _assert_exact(
        manifest.get("dashboard_authority_effect"),
        "NONE",
        label="dashboard_authority_effect",
    )
    _assert_exact(
        manifest.get("regime_coverage_status"),
        C.REGIME_COVERAGE_STATUS,
        label="regime_coverage_status",
    )
    _assert_exact(
        manifest.get("overall_topic_closeout_verdict"),
        C.OVERALL_TOPIC_CLOSEOUT_VERDICT,
        label="overall_topic_closeout_verdict",
    )
    _assert_null(manifest.get("campaign_id"), label="campaign_id")

    proofs = _require_mapping(manifest.get("execution_proofs"), label="execution_proofs")
    _assert_exact(proofs.get("producer_digest"), C.PRODUCER_DIGEST, label="proofs.producer_digest")
    _assert_exact(
        proofs.get("regime_coverage_counts"),
        dict(C.REGIME_COVERAGE_COUNTS),
        label="proofs.regime_coverage_counts",
    )
    _assert_exact(
        proofs.get("observation_pack_digest"),
        C.OBSERVATION_PACK_DIGEST,
        label="proofs.observation_pack_digest",
    )
    _assert_true(proofs.get("canonical_binding_ok"), label="proofs.canonical_binding_ok")

    live = execute_regime_coverage_against_canonical_pack_v1(repo_root=root)
    _assert_exact(
        live["regime_coverage_counts"],
        dict(C.REGIME_COVERAGE_COUNTS),
        label="live.regime_coverage_counts",
    )
    _assert_exact(live["producer_digest"], C.PRODUCER_DIGEST, label="live.producer_digest")
    _validate_sealed_artifacts(root, live)
    _assert_exact(
        proofs.get("regime_coverage_instance"),
        live["regime_coverage_instance"],
        label="proofs.regime_coverage_instance",
    )

    return {
        "ok": True,
        "next_step_id": C.NEXT_STEP_ID,
        "observation_pack_digest": C.OBSERVATION_PACK_DIGEST,
        "producer_digest": C.PRODUCER_DIGEST,
        "regime_coverage_counts": dict(C.REGIME_COVERAGE_COUNTS),
        "overall_topic_closeout_verdict": C.OVERALL_TOPIC_CLOSEOUT_VERDICT,
        "dashboard_authority_effect": "NONE",
        "campaign_start": False,
        "input_authority": False,
        "runtime_implemented": False,
        "regime_coverage_producer_available": False,
    }


__all__ = [
    "load_canonical_regime_coverage_dashboard_input_gap_closeout_manifest_v1",
    "validate_regime_coverage_dashboard_input_gap_closeout_manifest_v1",
]
