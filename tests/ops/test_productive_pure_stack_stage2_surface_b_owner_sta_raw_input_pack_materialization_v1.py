"""Owner/STA raw input-pack materialization execution contracts."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_v1.constants_v1 import (
    ARTIFACTS_REL,
    BAR_COUNT,
    CYBERSECURITY_MIRROR_REL,
    DECISION_ID,
    DECISIONS_MANIFEST_REL,
    MATERIALIZATION_PROOF_REL,
    OBSERVATION_PACK_DIGEST,
    OBSERVATION_PACK_REL,
    OWNER_DECISION_REL,
    OWNER_GO,
    OWNER_GO_BASE_SHA,
    OWNER_VALUE,
    RAW_SOURCE_DIGEST,
    SCHEMA_REL,
    SCOPE,
    STATUS,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_v1.materializer_v1 import (
    RawInputPackMaterializationErrorV1,
    materialize_raw_input_observation_pack_v1,
)
from src.ops.productive_pure_stack_stage2_surface_b_owner_sta_raw_input_pack_materialization_v1.validator_v1 import (
    RawInputPackMaterializationExecutionErrorV1,
    load_canonical_raw_input_pack_materialization_execution_manifest_v1,
    validate_raw_input_pack_materialization_execution_manifest_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]

REQUIRED_DOC_MARKERS: tuple[str, ...] = (
    "DOCUMENT_TYPE=OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION_EXECUTION",
    f"CAPABILITY_SCOPE=SURFACE_B_OWNER_STA_RAW_INPUT_PACK_MATERIALIZATION",
    f"STATUS={STATUS}",
    f"DECISION_ID={DECISION_ID}",
    "DECISION_STATUS=RATIFIED",
    f"OWNER_VALUE={OWNER_VALUE}",
    f"OWNER_GO={OWNER_GO}",
    f"OWNER_GO_BASE_SHA={OWNER_GO_BASE_SHA}",
    f"SCOPE={SCOPE}",
    "USE_RECORDED_INSTANCE_VALUES=true",
    "PACK_MATERIALIZATION=true",
    "RAW_INPUT_PACK_CREATED=true",
    "RAW_INPUT_PACK_MATERIALIZATION_AUTHORIZED=true",
    "CAMPAIGN_START=false",
    "INPUT_AUTHORITY=false",
    "RUNTIME_IMPLEMENTED=false",
    "REGIME_COVERAGE_PRODUCER_AVAILABLE=false",
    "PRODUCTIVE_THRESHOLDS_LOOKBACKS=false",
    "TRADING_LOGIC_CHANGE=false",
    "DASHBOARD_AUTHORITY_EFFECT=NONE",
    "ORDERS_TESTNET_LIVE=false",
    "INVENTED_VALUES=false",
    "SILENT_DEFAULTS=false",
    "PROPOSED_VALUES=false",
    f"observation_pack_digest={OBSERVATION_PACK_DIGEST}",
)

FORBIDDEN_DOC_CLAIMS: tuple[str, ...] = (
    "CAMPAIGN_START=true",
    "INPUT_AUTHORITY=true",
    "RUNTIME_IMPLEMENTED=true",
    "REGIME_COVERAGE_PRODUCER_AVAILABLE=true",
    "PRODUCTIVE_THRESHOLDS_LOOKBACKS=true",
    "TRADING_LOGIC_CHANGE=true",
    "ORDERS_TESTNET_LIVE=true",
    "INVENTED_VALUES=true",
    "SILENT_DEFAULTS=true",
    "PROPOSED_VALUES=true",
)


def test_materialization_artifacts_exist_v1() -> None:
    assert (REPO_ROOT / OWNER_DECISION_REL).is_file()
    assert (REPO_ROOT / DECISIONS_MANIFEST_REL).is_file()
    assert (REPO_ROOT / SCHEMA_REL).is_file()
    assert (REPO_ROOT / CYBERSECURITY_MIRROR_REL).is_file()
    assert (REPO_ROOT / OBSERVATION_PACK_REL).is_file()
    assert (REPO_ROOT / MATERIALIZATION_PROOF_REL).is_file()
    assert (REPO_ROOT / ARTIFACTS_REL / "observation_pack_digest.txt").is_file()


def test_materialization_document_markers_v1() -> None:
    text = (REPO_ROOT / OWNER_DECISION_REL).read_text(encoding="utf-8")
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text, marker
    for claim in FORBIDDEN_DOC_CLAIMS:
        assert claim not in text, claim


def test_materialize_pack_rebuilds_sealed_digest_v1() -> None:
    pack = materialize_raw_input_observation_pack_v1(repo_root=REPO_ROOT)
    assert pack.observation_pack_digest == OBSERVATION_PACK_DIGEST
    assert pack.provenance.raw_source_digest == RAW_SOURCE_DIGEST
    assert len(pack.bars) == BAR_COUNT
    sealed = json.loads((REPO_ROOT / OBSERVATION_PACK_REL).read_text(encoding="utf-8"))
    assert pack.to_dict() == sealed


def test_canonical_execution_manifest_validates_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_execution_manifest_v1(REPO_ROOT)
    result = validate_raw_input_pack_materialization_execution_manifest_v1(
        manifest, repo_root=REPO_ROOT
    )
    assert result["ok"] is True
    assert result["observation_pack_digest"] == OBSERVATION_PACK_DIGEST
    assert result["pack_materialization"] is True
    assert result["campaign_start"] is False
    assert result["input_authority"] is False


def test_execution_manifest_rejects_campaign_start_true_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_execution_manifest_v1(REPO_ROOT)
    bad = copy.deepcopy(dict(manifest))
    bad["campaign_start"] = True
    with pytest.raises(RawInputPackMaterializationExecutionErrorV1, match="MUST_REMAIN_FALSE"):
        validate_raw_input_pack_materialization_execution_manifest_v1(bad, repo_root=REPO_ROOT)


def test_execution_manifest_rejects_authority_flip_v1() -> None:
    manifest = load_canonical_raw_input_pack_materialization_execution_manifest_v1(REPO_ROOT)
    bad = copy.deepcopy(dict(manifest))
    bad["input_authority"] = True
    with pytest.raises(RawInputPackMaterializationExecutionErrorV1, match="MUST_REMAIN_FALSE"):
        validate_raw_input_pack_materialization_execution_manifest_v1(bad, repo_root=REPO_ROOT)


def test_cybersecurity_mirror_markers_v1() -> None:
    text = (REPO_ROOT / CYBERSECURITY_MIRROR_REL).read_text(encoding="utf-8")
    assert f"OWNER_GO={OWNER_GO}" in text
    assert "PACK_MATERIALIZATION=true" in text
    assert "CAMPAIGN_START=false" in text
    assert "INPUT_AUTHORITY=false" in text
    assert "RUNTIME_IMPLEMENTED=false" in text
