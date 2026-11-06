"""Surface-B regime-coverage + dashboard input-gap closeout contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_and_dashboard_input_gap_closeout_v1.constants_v1 import (
    CYBERSECURITY_MIRROR_REL,
    DECISIONS_MANIFEST_REL,
    NEXT_STEP_ID,
    OBSERVATION_PACK_DIGEST,
    OVERALL_TOPIC_CLOSEOUT_VERDICT,
    OWNER_DECISION_REL,
    OWNER_GO_BASE_SHA,
    PRODUCER_DIGEST,
    REGIME_COVERAGE_COUNTS,
    SCHEMA_REL,
    STATUS,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_and_dashboard_input_gap_closeout_v1.executor_v1 import (
    RegimeCoverageDashboardInputGapCloseoutErrorV1,
    execute_regime_coverage_against_canonical_pack_v1,
)
from src.ops.productive_pure_stack_stage2_surface_b_regime_coverage_and_dashboard_input_gap_closeout_v1.validator_v1 import (
    load_canonical_regime_coverage_dashboard_input_gap_closeout_manifest_v1,
    validate_regime_coverage_dashboard_input_gap_closeout_manifest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=SURFACE_B_REGIME_COVERAGE_AND_DASHBOARD_INPUT_GAP_CLOSEOUT_EXECUTION",
    "CAPABILITY_SCOPE=SURFACE_B_REGIME_COVERAGE_AND_DASHBOARD_INPUT_GAP_CLOSEOUT",
    f"STATUS={STATUS}",
    f"NEXT_STEP_ID={NEXT_STEP_ID}",
    f"OWNER_GO_BASE_SHA={OWNER_GO_BASE_SHA}",
    f"OBSERVATION_PACK_DIGEST={OBSERVATION_PACK_DIGEST}",
    "USE_CANONICAL_MERGED_PACK=true",
    "EXECUTE_REGIME_COVERAGE_PRODUCER=true",
    "REQUIRE_REGIME_COVERAGE_COUNTS=true",
    "REQUIRE_REGIME_COVERAGE_INSTANCE=true",
    "REQUIRE_CANONICAL_BINDING=true",
    "REQUIRE_MISSING_SOURCE_DELTA_REPORT=true",
    "REQUIRE_TOPIC_CLOSEOUT_VERDICT=true",
    "CAMPAIGN_START=false",
    "INPUT_AUTHORITY_FLIP=false",
    "RUNTIME_IMPLEMENTED_FLIP=false",
    "DASHBOARD_LOGIC_CHANGE=false",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "TRADING_LOGIC_CHANGE=false",
    "ORDERS_TESTNET_LIVE=false",
    "FAIL_CLOSED=true",
    "REGIME_COVERAGE_PRODUCER_AVAILABLE=false",
    PRODUCER_DIGEST,
)

FORBIDDEN_DOC_CLAIMS: tuple[str, ...] = (
    "CAMPAIGN_START=true",
    "INPUT_AUTHORITY_FLIP=true",
    "RUNTIME_IMPLEMENTED_FLIP=true",
    "DASHBOARD_LOGIC_CHANGE=true",
    "TRADING_LOGIC_CHANGE=true",
    "ORDERS_TESTNET_LIVE=true",
    "REGIME_COVERAGE_PRODUCER_AVAILABLE=true",
)


def test_closeout_documents_and_schema_exist_v1() -> None:
    assert (REPO_ROOT / OWNER_DECISION_REL).is_file()
    assert (REPO_ROOT / DECISIONS_MANIFEST_REL).is_file()
    assert (REPO_ROOT / SCHEMA_REL).is_file()
    assert (REPO_ROOT / CYBERSECURITY_MIRROR_REL).is_file()


def test_closeout_document_markers_v1() -> None:
    text = (REPO_ROOT / OWNER_DECISION_REL).read_text(encoding="utf-8")
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_DOC_CLAIMS:
        assert claim not in text, claim


def test_execute_against_canonical_pack_v1() -> None:
    live = execute_regime_coverage_against_canonical_pack_v1(repo_root=REPO_ROOT)
    assert live["observation_pack_digest"] == OBSERVATION_PACK_DIGEST
    assert live["producer_digest"] == PRODUCER_DIGEST
    assert live["regime_coverage_counts"] == dict(REGIME_COVERAGE_COUNTS)
    assert live["canonical_binding_ok"] is True
    assert live["campaign_start"] is False
    assert live["dashboard_authority_effect"] == "NONE"
    assert live["regime_coverage_producer_available"] is False


def test_canonical_manifest_validates_v1() -> None:
    manifest = load_canonical_regime_coverage_dashboard_input_gap_closeout_manifest_v1(REPO_ROOT)
    result = validate_regime_coverage_dashboard_input_gap_closeout_manifest_v1(
        manifest, repo_root=REPO_ROOT
    )
    assert result["ok"] is True
    assert result["producer_digest"] == PRODUCER_DIGEST
    assert result["regime_coverage_counts"] == dict(REGIME_COVERAGE_COUNTS)
    assert result["overall_topic_closeout_verdict"] == OVERALL_TOPIC_CLOSEOUT_VERDICT


def test_manifest_rejects_dashboard_logic_change_v1() -> None:
    manifest = load_canonical_regime_coverage_dashboard_input_gap_closeout_manifest_v1(REPO_ROOT)
    bad = copy.deepcopy(dict(manifest))
    bad["dashboard_logic_change"] = True
    with pytest.raises(RegimeCoverageDashboardInputGapCloseoutErrorV1, match="MUST_REMAIN_FALSE"):
        validate_regime_coverage_dashboard_input_gap_closeout_manifest_v1(bad, repo_root=REPO_ROOT)


def test_manifest_rejects_authority_flip_v1() -> None:
    manifest = load_canonical_regime_coverage_dashboard_input_gap_closeout_manifest_v1(REPO_ROOT)
    bad = copy.deepcopy(dict(manifest))
    bad["input_authority_flip"] = True
    with pytest.raises(RegimeCoverageDashboardInputGapCloseoutErrorV1, match="MUST_REMAIN_FALSE"):
        validate_regime_coverage_dashboard_input_gap_closeout_manifest_v1(bad, repo_root=REPO_ROOT)


def test_schema_const_next_step_id_v1() -> None:
    schema = json.loads((REPO_ROOT / SCHEMA_REL).read_text(encoding="utf-8"))
    assert schema["properties"]["next_step_id"]["const"] == NEXT_STEP_ID
    assert schema["properties"]["observation_pack_digest"]["const"] == OBSERVATION_PACK_DIGEST


def test_cybersecurity_mirror_markers_v1() -> None:
    text = (REPO_ROOT / CYBERSECURITY_MIRROR_REL).read_text(encoding="utf-8")
    assert f"OWNER_GO={NEXT_STEP_ID}" in text or f"NEXT_STEP_ID={NEXT_STEP_ID}" in text
    assert f"OWNER_GO_BASE_SHA={OWNER_GO_BASE_SHA}" in text
    assert "DASHBOARD_AUTHORITY_EFFECT=NONE" in text
    assert "CAMPAIGN_START=false" in text
    assert "ORDERS_TESTNET_LIVE=false" in text
